from flask import Flask, request, Response, render_template
import openai
import os
from dotenv import load_dotenv

# Initialize application
app = Flask(__name__)
messages = []

# ======================================================== INI BAGIAN RAG START ========================================================

# OpenAI Configuration
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# Function jalan kedua 
def get_openai_response(message):
    """Separate function to handle OpenAI communication"""
    if not openai.api_key:
        raise ValueError("API key is not set!")
        
    try:
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}],
            stream=False
        )
        if not response or not response.choices:
            raise ValueError("No response received from API")
        return response.choices[0].message.content
    except openai.AuthenticationError:
        raise ValueError("Invalid API key")
    except Exception as e:
        raise ValueError(f"Error communicating with OpenAI: {str(e)}")

# Function ini jalan dahulu
@app.route('/', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        message = request.form.get('message', '')
        
        # Jika terdeteksi API key kosong
        if not openai.api_key:
            return render_template('index.html', 
                                messages=messages, 
                                error="OpenAI API key is not set!")
        
        # Jika terdeteksi pesan masuk dan API key ada
        if message:
            try:
                answer = get_openai_response(message)
                messages.extend([
                    {"is_user": True, "q": message},
                    {"is_user": False, "a": answer}
                ])
            except Exception as e:
                app.logger.error(f"Error in chat route: {str(e)}")
                return render_template('index.html', 
                                    messages=messages, 
                                    error=f"An error occurred while processing your request: {str(e)}")
    
    return render_template('index.html', messages=messages)

# ======================================================== INI BAGIAN RAG END ========================================================


@app.route('/reset', methods=['POST'])
def reset():
    global messages
    messages = []
    return render_template('index.html', messages=messages)

if __name__ == '__main__':
    app.run()