from flask import Flask, request # type: ignore
import sqlite3

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json

    if data and data.get("type") == "preapproval":
        preapproval_id = data.get("data", {}).get("id")

        # Aqui você consultaria a API do Mercado Pago para validar a assinatura
        # Vamos simular que o email foi recebido e é válido:
        email_simulado = "cliente@email.com"

        # Ativar usuário no banco
        conn = sqlite3.connect("usuarios.db")
        c = conn.cursor()
        c.execute("UPDATE usuarios SET assinatura_ativa = 1 WHERE email = ?", (email_simulado,))
        conn.commit()
        conn.close()

        return "Assinatura ativada", 200
    return "Evento ignorado", 200

if __name__ == '__main__':
    app.run()