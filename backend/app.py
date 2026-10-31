import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types


# Carrega as variáveis do arquivo .env
load_dotenv()

# Configuração do Flask
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

# Configuração CORS para o endereço do BioPulse
CORS(
    app,
    resources={
        r"/chat": {
            "origins": [
                "http://26.185.49.13:8443",
            ]
        }
    },
)

# Configuração da chave Gemini
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "Configure GEMINI_API_KEY no arquivo backend/.env"
    )

# Cliente Gemini
client = genai.Client(api_key=api_key)


# Contexto do assistente BioPulse
SYSTEM_CONTEXT = """
Você é o BioPulse Assistant, assistente virtual do site BioPulse.

Responda em português brasileiro, com clareza, educação e objetividade.

Ajude a explicar as seções:
- Visão geral
- Sensores
- Minigames
- API & dados

O site é uma demonstração: números, gráficos, status de sensores
e unidades mostrados no painel são dados ilustrativos do protótipo.

Nunca diga que são medições reais.
Nunca invente telemetria.
Nunca afirme que controla equipamentos.

Se perguntarem algo que não esteja documentado,
explique que não tem essa informação.

Não peça nem revele chaves de API, senhas ou dados pessoais.
"""


# Verificação do backend
@app.get("/health")
def health():
    return jsonify({"status": "ok"})


# Endpoint do chatbot
@app.post("/chat")
def chat():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "erro": "Requisição inválida."
        }), 400

    message = data.get("mensagem", "")

    if not isinstance(message, str) or not message.strip():
        return jsonify({
            "erro": "Envie uma mensagem válida."
        }), 400

    if len(message) > 2000:
        return jsonify({
            "erro": "A mensagem é muito longa. Limite: 2000 caracteres."
        }), 413

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
                contents=(
                    f"{SYSTEM_CONTEXT}\n\n"
                    f"Mensagem do visitante: {message.strip()}"
            ),
)


        answer = response.text or (
            "Não consegui formular uma resposta agora."
        )

        return jsonify({
            "resposta": answer
        })

    except Exception:
        app.logger.exception("Falha ao consultar Gemini")

        return jsonify({
            "erro": "O assistente não conseguiu responder agora. Tente novamente."
        }), 502


# Inicialização do servidor
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )