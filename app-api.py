from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import sqlite3
import datetime
import os
import hmac
import hashlib

app = FastAPI()

# Caminho absoluto do banco (garante compatibilidade com Render)
DB_PATH = os.path.join(os.path.dirname(__file__), "ml_tokens.db")

# Assinatura secreta fornecida pelo Mercado Pago
WEBHOOK_SECRET = "2925a271d0efcea338f9e7c21698913b4905244ea0d1ae87a0a382028ff96ce2"

@app.get("/webhook")
async def receber_codigo(code: str = None):
    if not code:
        return JSONResponse(content={"erro": "Código de autorização não encontrado na URL."}, status_code=400)
    return JSONResponse(content={"mensagem": "Código recebido com sucesso!", "code": code})

@app.post("/webhook")
async def receber_webhook(request: Request):
    # Valida a assinatura do Mercado Pago
    raw_body = await request.body()
    signature_header = request.headers.get("x-signature")

    if not signature_header:
        return JSONResponse(content={"erro": "Assinatura não enviada."}, status_code=403)

    # Gera assinatura local para comparação
    expected_signature = hmac.new(WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()

    if signature_header != expected_signature:
        return JSONResponse(content={"erro": "Assinatura inválida."}, status_code=403)

    # Se assinatura for válida, processa normalmente
    corpo = await request.json()
    print("📦 Webhook recebido:", corpo)

    # (Exemplo) Você pode tratar o evento aqui
    return JSONResponse(content={"status": "ok", "evento": corpo.get("action", "desconhecido")})