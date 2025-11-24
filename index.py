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
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("WARNING: OPENAI_API_KEY not found in environment")
        return None

    # 1. Knowledge Base (Data statis yang selalu ada)
    knowledge_base = [
        "Gezenio adalah platform UI/UX modern yang dirancang untuk efisiensi coding.",
        "Gezenio menggunakan framework Flask sebagai backend utamanya.",
        "Fitur utama Gezenio meliputi dashboard real-time, manajemen user yang intuitif, dan integrasi AI.",
        "Untuk mereset percakapan di Gezenio, pengguna bisa menekan tombol Reset Chat.",
        "Creator Gezenio berfokus pada kesederhanaan desain (minimalist) namun fungsionalitas tinggi.",
        "LangSmith digunakan di Gezenio untuk memantau performa LLM dan debugging."
    ]

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
        Kamu adalah asisten yang cerdas dalam memahami konteks percakapan.
        Gunakan riwayat percakapan untuk memahami maksud pertanyaan user.
        Jika pertanyaan sudah jelas tanpa konteks, kembalikan pertanyaan apa adanya.
        Jangan menambahkan informasi yang tidak ada dalam pertanyaan.
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
        qa_system_prompt = """Kamu adalah asisten AI bernama Tanaka yang membantu user dengan masalah mereka.

        Tugas utamamu:
        1. Jawab pertanyaan berdasarkan konteks yang diberikan dan riwayat percakapan
        2. Jika informasi tidak ada dalam konteks, gunakan pengetahuan umummu
        3. Jika tidak tahu, katakan dengan jujur bahwa kamu tidak memiliki informasi tersebut
        4. Selalu jawab dalam Bahasa Indonesia dengan ramah dan profesional
        5. Ingat percakapan sebelumnya untuk memberikan jawaban yang konsisten

        Konteks dari knowledge base:
        {context}"""
        
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