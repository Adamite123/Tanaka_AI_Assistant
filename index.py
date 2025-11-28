from flask import Flask, request, render_template, jsonify
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Import LangChain components
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

# Load environment variables
load_dotenv()

app = Flask(__name__)
# app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here-change-in-production')

# ================= PERSISTENT STORAGE =================

CHAT_HISTORY_FILE = "chat_history.json"

def load_chat_history():
    """Load chat history dari file JSON"""
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading chat history: {e}")
            return []
    return []

def save_chat_history(messages):
    """Save chat history ke file JSON"""
    try:
        with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving chat history: {e}")

def add_to_vectorstore(user_message, ai_response):
    """
    Menambahkan percakapan baru ke ChromaDB sebagai knowledge tambahan
    Format: "User bertanya: [question]. Jawabannya: [answer]"
    """
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        embeddings = OpenAIEmbeddings(api_key=api_key)
        persist_dir = "./chroma_db"
        
        # Load existing vectorstore
        vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings
        )
        
        # Format percakapan sebagai knowledge
        conversation_text = f"User bertanya: {user_message}. Jawabannya: {ai_response}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Tambahkan metadata untuk tracking
        vectorstore.add_texts(
            texts=[conversation_text],
            metadatas=[{
                "source": "chat_history",
                "timestamp": timestamp,
                "type": "conversation"
            }]
        )
        
        print(f">>> Conversation added to vectorstore at {timestamp}")
        
    except Exception as e:
        print(f"Error adding to vectorstore: {e}")

# ================= RAG SETUP =================

def setup_rag_chain():
    """
    Menginisialisasi Vector Store (ChromaDB) dan Conversational RAG Chain.
    """
    file_path = 'datasheet.json'

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("WARNING: OPENAI_API_KEY not found in environment")
        return None

    # Import Knowladge base dari file datasheet.json
    with open(file_path, 'r') as f:
        knowledge_base = json.load(f)

    try:
        embeddings = OpenAIEmbeddings(api_key=api_key)
        persist_dir = "./chroma_db"

        # 2. Cek apakah DB sudah ada
        if os.path.exists(persist_dir):
            print(">>> Loading existing ChromaDB Vector Store...")
            vectorstore = Chroma(
                persist_directory=persist_dir,
                embedding_function=embeddings
            )
        else:
            print(">>> Creating new ChromaDB Vector Store...")
            vectorstore = Chroma.from_texts(
                texts=knowledge_base,
                embedding=embeddings,
                persist_directory=persist_dir
            )
        
        # Retriever dengan K=4 untuk mendapat lebih banyak konteks
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

        # 3. Model (LLM)
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=api_key)

        # PROMPT + RETRIEVER HISTORY/MEMORY PERCAKAPAN SEBELUMNYA SET UP >>>>>>>>>>>>>>>>>>>>>>> START
        # 4. History-Aware Retriever
        contextualize_q_system_prompt = """
        Anda adalah pengolah pertanyaan cerdas. Tugas Anda adalah menganalisis riwayat percakapan (chat_history) dan pertanyaan user saat ini (input) untuk menghasilkan **satu pertanyaan mandiri yang lengkap**.

        Tujuan:
        1.  Jika pertanyaan user saat ini memiliki dependensi konteks dari riwayat percakapan (misalnya, menggunakan kata ganti seperti "itu", "dia", "tersebut"), maka gabungkan konteks yang relevan untuk membuat pertanyaan baru yang **eksplisit dan lengkap** (tidak ambigu).
        2.  Jika pertanyaan user saat ini sudah jelas, berdiri sendiri, dan tidak membutuhkan konteks dari riwayat percakapan, maka kembalikan pertanyaan user tersebut **apa adanya**.

        Aturan Keras:
        * Output Anda HANYA berupa pertanyaan tunggal yang telah dikontekstualisasikan.
        * Jangan pernah menambahkan komentar, penjelasan, atau informasi tambahan di luar pertanyaan yang dihasilkan.
        """
        
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )

        # PROMPT + RETRIEVER HISTORY SET UP >>>>>>>>>>>>>>>>>>>>>>> END

        # PROMPT + RETRIEVER PRESENT atau sekarang SET UP >>>>>>>>>>>>>>>>>>>>>>> START
        # 5. Answer Chain
        qa_system_prompt = """
        Anda adalah **Mouna**, seorang Asisten AI Layanan Pelanggan (Customer Service) yang profesional dan ramah dari Mountain Camp Booking. Tugas utama Anda adalah menjawab pertanyaan user secara akurat, natural, dan membantu, **hanya berdasarkan** informasi yang tersedia dalam `Konteks dari knowledge base` yang disediakan.

        ### ATURAN UTAMA (WAJIB DIIKUTI):

        1.  **Sumber Jawaban Tunggal:** Jawablah pertanyaan user **HANYA** menggunakan informasi yang ada di dalam `{context}` dan mempertimbangkan `chat_history`.

        2.  **Jawaban Natural dan Informatif:**
            - **JANGAN** pernah gunakan kata "Maaf" di awal jawaban, langsung berikan informasi yang diminta
            - Gunakan intro singkat yang natural (1 kalimat) sebelum memberikan detail/list
            - Akhiri dengan kalimat penutup yang mengajak interaksi lebih lanjut jika relevan
            - Contoh BAIK: "Kami melayani pendakian ke 15+ gunung di Indonesia:" [list gunung]
            - Contoh BURUK: "Maaf, saya tidak memiliki informasi..." atau hanya list tanpa konteks

        3.  **Format Keterbacaan:**
            - Jika jawaban berisi 3+ item atau data kompleks, gunakan format bullet points atau numbered list
            - Berikan intro singkat sebelum list untuk konteks
            - Tambahkan detail relevan dalam list (misal: harga, lokasi, spesifikasi)

        4.  **Struktur Jawaban Ideal:**
            ```
            [Intro singkat 1 kalimat yang menjawab pertanyaan]

            [Detail dalam format list jika > 3 item:]
            - Item 1 (detail tambahan jika ada)
            - Item 2 (detail tambahan jika ada)
            - Item 3 (detail tambahan jika ada)

            [Penutup mengajak interaksi jika relevan - opsional]
            ```

        5.  **Handling Pertanyaan Spesifik:**
            - **Harga**: Berikan range harga per kategori/gunung dengan penjelasan singkat
            - **Cara booking**: Berikan step-by-step dalam numbered list
            - **Daftar items**: Berikan dengan intro dan penutup yang natural
            - **Fasilitas**: Sebutkan kategori dan detail spesifik

        6.  **Penanganan Data Tidak Lengkap:**
            - **JANGAN** gunakan kata "Maaf" atau "Saya tidak memiliki informasi"
            - Berikan informasi terbaik yang ada di konteks dengan natural
            - Jika benar-benar tidak ada info, arahkan ke kontak CS dengan ramah

        7.  **Nada Bahasa:** Ramah, natural, profesional tapi tidak kaku. Seperti CS manusia yang helpful.

        ### PROFIL DAN TUGAS:

        * **Identitas:** Mouna dari Mountain Camp Booking
        * **Konsistensi:** Jaga konsistensi jawaban dengan riwayat percakapan
        * **Tujuan:** Membantu user mendapatkan informasi yang jelas dan lengkap

        Konteks dari knowledge base:
        {context}
        """
        
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

        # PROMPT + RETRIEVER PRESENT atau sekarang SET UP >>>>>>>>>>>>>>>>>>>>>>> END

        # 6. Final Retrieval Chain // #Ini Final Chain atau sebelum data kita dikirim ke LLM/OPEN AI
        # history_aware_retriever = Retriever dan Prompt untuk memberi pemahaman dan kemampuan RAG berdasarkan history
        # question_answer_chain = Retriever dan Prompt untuk menjawab pertanyaan present bukan pertanyaan sebelum sebelumnya
        # rag_chain = Gabungan antara kemampuan menjawab pertanyaan saat ini + pemahaman percakapan sebelumnya
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        
        print(">>> ChromaDB & Conversational RAG Initialized Successfully")
        return rag_chain

    except Exception as e:
        print(f"Error initializing RAG: {e}")
        return None

# Initialize Chain Global
rag_chain = setup_rag_chain()

# ================= ROUTES (AJAX API) =================

@app.route('/')
def index():
    """Render halaman utama"""
    return render_template('index.html')

@app.route('/get_history', methods=['GET'])
def get_history():
    """API endpoint untuk mengambil chat history"""
    try:
        messages = load_chat_history()
        return jsonify({"success": True, "messages": messages})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/send_message', methods=['POST'])
def send_message():
    """API endpoint untuk mengirim pesan dan mendapat response"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        if not os.getenv('OPENAI_API_KEY'):
            return jsonify({"error": "OpenAI API key is not set!"}), 500
        
        # Load chat history
        messages = load_chat_history()
        
        if rag_chain:
            # --- PROSES HISTORY ---
            # Ambil maksimal 20 pesan terakhir (10 percakapan)
            recent_messages = messages[-20:] 
            
            chat_history = []
            for msg in recent_messages:
                if msg.get("is_user"):
                    chat_history.append(HumanMessage(content=msg["q"]))
                else:
                    chat_history.append(AIMessage(content=msg["a"]))

            # --- INVOKE RAG ---
            response = rag_chain.invoke({
                "input": user_message,
                "chat_history": chat_history
            })
            
            answer = response["answer"]
            
            # Simpan percakapan baru ke vectorstore
            add_to_vectorstore(user_message, answer)
        else:
            answer = "Maaf, sistem AI sedang tidak dapat diinisialisasi."

        # Simpan ke file dengan timestamp
        timestamp = datetime.now().isoformat()
        new_messages = [
            {
                "is_user": True, 
                "q": user_message,
                "timestamp": timestamp
            },
            {
                "is_user": False, 
                "a": answer,
                "timestamp": timestamp
            }
        ]
        
        messages.extend(new_messages)
        save_chat_history(messages)
        
        return jsonify({
            "success": True,
            "response": answer,
            "timestamp": timestamp
        })

    except Exception as e:
        app.logger.error(f"Error in send_message: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset():
    """Reset chat history (hanya UI, tidak menghapus dari vectorstore)"""
    try:
        save_chat_history([])
        return jsonify({"success": True, "message": "Chat history reset successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/clear_all', methods=['POST'])
def clear_all():
    """
    Menghapus semua data (chat history + vectorstore)
    HATI-HATI: Ini akan menghapus semua data termasuk knowledge base!
    """
    try:
        import shutil
        
        # Hapus chat history
        if os.path.exists(CHAT_HISTORY_FILE):
            os.remove(CHAT_HISTORY_FILE)
        
        # Hapus vectorstore
        persist_dir = "./chroma_db"
        if os.path.exists(persist_dir):
            shutil.rmtree(persist_dir)
        
        # Reinitialize RAG dengan knowledge base baru
        global rag_chain
        rag_chain = setup_rag_chain()
        
        return jsonify({"success": True, "message": "All data cleared successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)