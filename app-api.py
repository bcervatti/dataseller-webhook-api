from fastapi import FastAPI, Request
import requests
import sqlite3
import datetime
import os

app = FastAPI()

# Caminho absoluto do banco (garante que funcione no Render)
DB_PATH = os.path.join(os.path.dirname(__file__), "ml_tokens.db")

@app.get("/webhook")
async def receber_code(request: Request):
    code = request.query_params.get("code")
    if not code:
        return {"erro": "Código de autorização não encontrado na URL."}

    # Dados da aplicação no Mercado Livre
    client_id = "8940516793064447"
    client_secret = "gd7IkR1Q8MuCm94yna6DsTS5OmO6EGnr"
    redirect_uri = "https://dataseller-webhook.onrender.com/webhook"

    # Troca do code por token
    response = requests.post(
        "https://api.mercadolibre.com/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if response.status_code != 200:
        return {"erro": "Erro ao obter token", "detalhe": response.text}

    token_data = response.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Salvar no banco SQLite
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                access_token TEXT,
                refresh_token TEXT,
                created_at TEXT
            )
        """)
        cursor.execute("INSERT INTO users (access_token, refresh_token, created_at) VALUES (?, ?, ?)",
                       (access_token, refresh_token, created_at))
        conn.commit()
        conn.close()
    except Exception as e:
        return {"erro": "Erro ao salvar no banco de dados", "detalhe": str(e)}

    return {
        "sucesso": True,
        "mensagem": "Token salvo com sucesso!",
        "access_token": access_token
    }