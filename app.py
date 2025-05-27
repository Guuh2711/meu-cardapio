from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import stripe
import uuid
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# 🔐 Carrega as chaves do Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# Banco de dados simulado
pedidos_confirmados = {}

@app.route("/criar-sessao", methods=["POST"])
def criar_sessao():
    try:
        data = request.get_json()
        preco = data["preco"]
        dados = data["dados"]
        pedido_id = str(uuid.uuid4())

        pedidos_confirmados[pedido_id] = {
            "status": "aguardando",
            "dados": dados
        }

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "brl",
                    "product_data": {
                        "name": f"Cardápio Personalizado ({dados['dias']} dias)",
                    },
                    "unit_amount": preco,
                },
                "quantity": 1,
            }],
            mode="payment",
            client_reference_id=pedido_id,
            success_url=f"http://localhost:5500/sucesso.html?id={pedido_id}",
            cancel_url="http://localhost:5500/erro.html"
        )

        # 🔄 Alterado aqui: retorna "id" em vez de "sessionId"
        return jsonify(id=session.id)

    except Exception as e:
        print(f"Erro ao criar sessão Stripe: {e}")
        return jsonify(error="Erro interno ao criar sessão de pagamento."), 500

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        return str(e), 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        pedido_id = session.get("client_reference_id")

        if pedido_id and pedido_id in pedidos_confirmados:
            pedidos_confirmados[pedido_id]["status"] = "pago"
            print("✅ Pagamento confirmado para o pedido:", pedido_id)
        else:
            print("⚠️ Pedido não encontrado no webhook:", pedido_id)

    return "", 200

@app.route("/api/cardapio")
def gerar_cardapio():
    pedido_id = request.args.get("id")

    if not pedido_id or pedido_id not in pedidos_confirmados:
        return jsonify({"erro": "Pedido não encontrado."}), 404

    pedido = pedidos_confirmados[pedido_id]

    if pedido["status"] != "pago":
        return jsonify({"erro": "Pagamento não confirmado ainda."}), 403

    dados = pedido["dados"]
    nome_arquivo = f"/tmp/{pedido_id}.pdf"

    with open(nome_arquivo, "wb") as f:
        conteudo = f"""
        🥗 Cardápio Personalizado

        Nome: {dados['nome']}
        Objetivo: {dados['objetivo']}
        Dias: {dados['dias']}
        Refeições por dia: {dados['refeicoes']}
        Preferências: {dados['preferencias']}
        """.encode("utf-8")
        f.write(conteudo)

    retorno = send_file(nome_arquivo, as_attachment=True)
    os.remove(nome_arquivo)
    return retorno

@app.route("/api/status")
def status_pedido():
    pedido_id = request.args.get("id")

    if not pedido_id or pedido_id not in pedidos_confirmados:
        return jsonify({"erro": "Pedido não encontrado."}), 404

    pedido = pedidos_confirmados[pedido_id]
    return jsonify({
        "status": pedido["status"],
        "dados": pedido["dados"]
    })

if __name__ == "__main__":
    app.run(debug=True)
