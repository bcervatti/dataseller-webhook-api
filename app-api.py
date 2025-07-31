from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
import requests
import sqlite3
import datetime
import os
import hmac
import hashlib

# Caminho do banco de dados
DB_PATH = os.path.join(os.path.dirname(__file__), "ml_tokens.db")
SEGREDO = "2925a271d0efcea338f9e7c21698913b4905244ea0d1ae87a0a382028ff96ce2"

# Criação automática das tabelas
def inicializar_banco():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id TEXT,
                nome TEXT,
                email TEXT,
                telefone TEXT,
                produto TEXT,
                data_compra TEXT,
                estado TEXT
            )
        """)
        conn.commit()
        conn.close()
        print("🗃️ Banco e tabelas inicializados com sucesso.")
    except Exception as e:
        print("❌ Erro ao inicializar banco:", e)

inicializar_banco()

app = FastAPI()

@app.get("/webhook")
async def receber_codigo(code: str = None):
    if not code:
        return JSONResponse(content={"erro": "Código de autorização não encontrado na URL."}, status_code=400)
    return JSONResponse(content={"mensagem": "Código recebido com sucesso!", "code": code})

@app.post("/webhook")
async def receber_webhook(request: Request, x_signature: str = Header(None)):
    corpo = await request.body()
    if not x_signature:
        return JSONResponse(content={"erro": "Assinatura não enviada."}, status_code=400)

    assinatura_calculada = hmac.new(
        SEGREDO.encode(),
        corpo,
        hashlib.sha256
    ).hexdigest()

    if assinatura_calculada != x_signature:
        return JSONResponse(content={"erro": "Assinatura inválida."}, status_code=403)

    json_data = await request.json()
    print("📦 Webhook recebido:", json_data)
    return JSONResponse(content={"status": "ok", "evento": json_data.get("action")})

@app.get("/executar-coleta")
def executar_coleta():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT access_token FROM users ORDER BY id DESC LIMIT 1")
        token = cursor.fetchone()
        if not token:
            return {"erro": "Nenhum token encontrado no banco de dados."}
        access_token = token[0]

        offset = 0
        limit = 50
        todos_pedidos = []

        while True:
            url = f"https://api.mercadolibre.com/orders/search?seller=1118447657&offset={offset}&limit={limit}&access_token={access_token}"
            r = requests.get(url)
            if r.status_code != 200:
                break
            data = r.json()
            results = data.get("results", [])
            if not results:
                break
            for pedido in results:
                pedido_id = pedido.get("id")
                r_pedido = requests.get(f"https://api.mercadolibre.com/orders/{pedido_id}?access_token={access_token}")
                if r_pedido.status_code != 200:
                    continue
                dados = r_pedido.json()
                nome = dados.get("buyer", {}).get("nickname")
                email = dados.get("buyer", {}).get("email")  # geralmente null
                telefone = dados.get("buyer", {}).get("phone", {}).get("number")
                data_compra = dados.get("date_created")
                status = dados.get("status")
                produto = dados.get("order_items", [{}])[0].get("item", {}).get("title")
                estado = "N/A"

                # Tenta buscar dados da entrega (shipping)
                shipping_id = dados.get("shipping", {}).get("id")
                if shipping_id:
                    r_envio = requests.get(f"https://api.mercadolibre.com/shipments/{shipping_id}?access_token={access_token}")
                    if r_envio.status_code == 200:
                        envio = r_envio.json()
                        telefone = envio.get("receiver_address", {}).get("receiver_phone") or telefone
                        estado = envio.get("receiver_address", {}).get("state", {}).get("name", "N/A")
                        nome = envio.get("receiver_address", {}).get("receiver_name") or nome

                cursor.execute("INSERT INTO pedidos (pedido_id, nome, email, telefone, produto, data_compra, estado) VALUES (?, ?, ?, ?, ?, ?, ?)",
                               (pedido_id, nome, email, telefone, produto, data_compra, estado))
                conn.commit()
                todos_pedidos.append(pedido_id)

            offset += limit

        conn.close()
        return {"sucesso": True, "total_pedidos_salvos": len(todos_pedidos)}

    except Exception as e:
        return {"erro": str(e)}

@app.get("/visualizar-pedidos")
def visualizar_pedidos():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pedido_id, nome, email, telefone, produto, data_compra, estado FROM pedidos
            ORDER BY data_compra DESC
            LIMIT 100
        """)
        pedidos = cursor.fetchall()
        conn.close()

        lista = []
        for p in pedidos:
            lista.append({
                "pedido_id": p[0],
                "nome": p[1],
                "email": p[2],
                "telefone": p[3],
                "produto": p[4],
                "data_compra": p[5],
                "estado": p[6]
            })

        return {"pedidos": lista}

    except Exception as e:
        return {"erro": str(e)}
