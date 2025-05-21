from flask import Flask, request
import sqlite3

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data and data.get("type") == "preapproval":
        email_simulado = "cliente@email.com"
        conn = sqlite3.connect("usuarios.db")
        c = conn.cursor()
        c.execute("UPDATE usuarios SET assinatura_ativa = 1 WHERE email = ?", (email_simulado,))
        conn.commit()
        conn.close()
        return "Assinatura ativada", 200
    return "Evento ignorado", 200

if __name__ == '__main__':
    app.run()
