"""
PromptPing - Game Evaluasi Prompt
Game untuk menilai kemampuan siswa membuat prompt berdasarkan:
1. Clarity (Kejelasan Prompt)
2. Instruction Following (Kepatuhan Instruksi)
3. Hallucination (Halusinasi)
"""

from flask import Flask, request, render_template, jsonify
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import uuid

# Import LangChain components
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'promptping-secret-key-2025')

# ================= CONFIGURATION =================

DATA_DIR = "game_data"
SCORES_FILE = os.path.join(DATA_DIR, "scores.json")
LEADERBOARD_FILE = os.path.join(DATA_DIR, "leaderboard.json")

# Ensure data directories exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ================= GAME CHALLENGES =================

CHALLENGES = [
    {
        "id": 1,
        "title": "Penjelasan Konsep",
        "task": "Minta AI menjelaskan apa itu 'Machine Learning' untuk anak SMP",
        "context": "Kamu adalah guru yang perlu menjelaskan konsep teknologi ke siswa SMP",
        "expected_output": "Penjelasan sederhana tentang Machine Learning dengan analogi yang mudah dipahami anak SMP",
        "difficulty": "easy"
    },
    {
        "id": 2,
        "title": "Menulis Email Formal",
        "task": "Minta AI menulis email permohonan izin tidak masuk kerja karena sakit",
        "context": "Kamu adalah karyawan yang perlu mengirim email ke atasan",
        "expected_output": "Email formal dengan format yang benar, alasan yang jelas, dan nada sopan",
        "difficulty": "easy"
    },
    {
        "id": 3,
        "title": "Analisis Data",
        "task": "Minta AI menganalisis data penjualan berikut dan berikan insight: Jan: 100, Feb: 150, Mar: 120, Apr: 200, May: 180",
        "context": "Kamu adalah manajer yang perlu memahami tren penjualan",
        "expected_output": "Analisis trend, insight tentang kenaikan/penurunan, dan rekomendasi",
        "difficulty": "medium"
    },
    {
        "id": 4,
        "title": "Debugging Code",
        "task": "Minta AI untuk menemukan bug dalam kode berikut: for i in range(10): print(i) if i = 5: break",
        "context": "Kamu adalah programmer yang butuh bantuan debugging",
        "expected_output": "Identifikasi bug (= seharusnya ==) dan penjelasan mengapa itu error",
        "difficulty": "medium"
    },
    {
        "id": 5,
        "title": "Kreasi Konten",
        "task": "Minta AI membuat caption Instagram untuk promosi produk kopi lokal dengan target anak muda",
        "context": "Kamu adalah social media manager untuk brand kopi",
        "expected_output": "Caption yang catchy, menggunakan bahasa anak muda, ada call-to-action",
        "difficulty": "medium"
    },
    {
        "id": 6,
        "title": "Pembuatan Rencana",
        "task": "Minta AI membuat rencana belajar untuk persiapan ujian TOEFL dalam 30 hari",
        "context": "Kamu adalah mahasiswa yang akan ujian TOEFL bulan depan",
        "expected_output": "Rencana terstruktur dengan jadwal harian/mingguan, target skor, dan strategi per section",
        "difficulty": "hard"
    },
    {
        "id": 7,
        "title": "Argumentasi",
        "task": "Minta AI membuat argumen pro dan kontra tentang 'Work From Home permanen'",
        "context": "Kamu sedang mempersiapkan debat di kantor",
        "expected_output": "Minimal 3 argumen pro dan 3 argumen kontra yang berimbang dan didukung fakta",
        "difficulty": "hard"
    }
]

# ================= DATA MANAGEMENT =================

def load_json_file(filepath):
    """Load JSON file safely"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    return None

def save_json_file(filepath, data):
    """Save data to JSON file safely"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {filepath}: {e}")
        return False

def load_leaderboard():
    """Load leaderboard"""
    data = load_json_file(LEADERBOARD_FILE)
    return data if data else {"players": []}

def save_leaderboard(data):
    """Save leaderboard"""
    return save_json_file(LEADERBOARD_FILE, data)

# ================= PROMPT EVALUATION =================

def evaluate_prompt(user_prompt, challenge, ai_response):
    """
    Evaluate user's prompt based on 3 criteria:
    1. Clarity (Kejelasan) - 0-100
    2. Instruction Following (Kepatuhan Instruksi) - 0-100
    3. Hallucination (Halusinasi) - 0-100 (higher = less hallucination = better)
    """
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return {
                "error": "API key not configured",
                "scores": {"clarity": 50, "instruction_following": 50, "hallucination": 50}
            }

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)

        evaluation_prompt = f"""
Kamu adalah evaluator ahli untuk menilai kualitas prompt yang dibuat oleh siswa.

TUGAS YANG DIBERIKAN:
{challenge['task']}

KONTEKS:
{challenge['context']}

OUTPUT YANG DIHARAPKAN:
{challenge['expected_output']}

PROMPT YANG DIBUAT SISWA:
{user_prompt}

RESPONS AI DARI PROMPT TERSEBUT:
{ai_response}

Evaluasi prompt siswa berdasarkan 3 kriteria berikut:

1. CLARITY (Kejelasan Prompt) - 0-100
   - Apakah prompt jelas dan tidak ambigu?
   - Apakah instruksi mudah dipahami?
   - Apakah ada detail yang cukup?

2. INSTRUCTION FOLLOWING (Kepatuhan Instruksi) - 0-100
   - Apakah prompt sesuai dengan tugas yang diberikan?
   - Apakah prompt mencakup semua persyaratan?
   - Apakah output AI sesuai dengan yang diharapkan?

3. HALLUCINATION (Anti-Halusinasi) - 0-100
   - Apakah prompt mendorong jawaban faktual?
   - Apakah ada batasan yang jelas untuk mencegah AI mengarang?
   - Apakah output AI tidak mengandung informasi palsu/mengarang?
   (Skor tinggi = tidak ada halusinasi, Skor rendah = banyak halusinasi)

Berikan output dalam format JSON:
{{
    "clarity": {{
        "score": <0-100>,
        "feedback": "<penjelasan singkat>"
    }},
    "instruction_following": {{
        "score": <0-100>,
        "feedback": "<penjelasan singkat>"
    }},
    "hallucination": {{
        "score": <0-100>,
        "feedback": "<penjelasan singkat>"
    }},
    "overall_feedback": "<feedback keseluruhan dan tips untuk perbaikan>",
    "total_score": <rata-rata dari 3 kriteria>
}}
"""

        response = llm.invoke(evaluation_prompt)
        result_text = response.content if hasattr(response, 'content') else str(response)

        # Parse JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            try:
                evaluation = json.loads(json_match.group())
                return {"success": True, "evaluation": evaluation}
            except json.JSONDecodeError:
                pass

        # Fallback
        return {
            "success": False,
            "error": "Could not parse evaluation",
            "raw_response": result_text
        }

    except Exception as e:
        print(f"Error evaluating prompt: {e}")
        return {"success": False, "error": str(e)}

def get_ai_response(user_prompt):
    """Get AI response for user's prompt"""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return {"error": "API key not configured"}

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, api_key=api_key)

        response = llm.invoke(user_prompt)
        result_text = response.content if hasattr(response, 'content') else str(response)

        return {"success": True, "response": result_text}

    except Exception as e:
        print(f"Error getting AI response: {e}")
        return {"success": False, "error": str(e)}

# ================= ROUTES =================

@app.route('/')
def index():
    """Render main game page"""
    return render_template('index.html')

@app.route('/api/challenges', methods=['GET'])
def get_challenges():
    """Get all available challenges"""
    return jsonify({"success": True, "data": CHALLENGES})

@app.route('/api/challenge/<int:challenge_id>', methods=['GET'])
def get_challenge(challenge_id):
    """Get specific challenge"""
    challenge = next((c for c in CHALLENGES if c['id'] == challenge_id), None)
    if challenge:
        return jsonify({"success": True, "data": challenge})
    return jsonify({"success": False, "error": "Challenge not found"}), 404

@app.route('/api/submit', methods=['POST'])
def submit_prompt():
    """Submit prompt for evaluation"""
    try:
        data = request.get_json()
        user_prompt = data.get('prompt', '')
        challenge_id = data.get('challenge_id')
        player_name = data.get('player_name', 'Anonymous')

        if not user_prompt:
            return jsonify({"success": False, "error": "Prompt tidak boleh kosong"}), 400

        # Get challenge
        challenge = next((c for c in CHALLENGES if c['id'] == challenge_id), None)
        if not challenge:
            return jsonify({"success": False, "error": "Challenge tidak ditemukan"}), 404

        # Get AI response for the prompt
        ai_result = get_ai_response(user_prompt)
        if not ai_result.get('success'):
            return jsonify({"success": False, "error": ai_result.get('error', 'Failed to get AI response')}), 500

        ai_response = ai_result['response']

        # Evaluate the prompt
        eval_result = evaluate_prompt(user_prompt, challenge, ai_response)
        if not eval_result.get('success'):
            return jsonify({"success": False, "error": eval_result.get('error', 'Failed to evaluate')}), 500

        evaluation = eval_result['evaluation']

        # Save to leaderboard
        leaderboard = load_leaderboard()
        entry = {
            "id": str(uuid.uuid4()),
            "player_name": player_name,
            "challenge_id": challenge_id,
            "challenge_title": challenge['title'],
            "prompt": user_prompt,
            "ai_response": ai_response,
            "scores": {
                "clarity": evaluation['clarity']['score'],
                "instruction_following": evaluation['instruction_following']['score'],
                "hallucination": evaluation['hallucination']['score']
            },
            "total_score": evaluation['total_score'],
            "timestamp": datetime.now().isoformat()
        }
        leaderboard['players'].append(entry)
        save_leaderboard(leaderboard)

        return jsonify({
            "success": True,
            "data": {
                "ai_response": ai_response,
                "evaluation": evaluation,
                "entry": entry
            }
        })

    except Exception as e:
        print(f"Error submitting prompt: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get leaderboard sorted by total score"""
    try:
        leaderboard = load_leaderboard()
        players = leaderboard.get('players', [])

        # Sort by total_score descending
        players.sort(key=lambda x: x.get('total_score', 0), reverse=True)

        # Get top 20
        top_players = players[:20]

        return jsonify({"success": True, "data": top_players})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/leaderboard/clear', methods=['POST'])
def clear_leaderboard():
    """Clear leaderboard (admin only)"""
    try:
        save_leaderboard({"players": []})
        return jsonify({"success": True, "message": "Leaderboard cleared"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
