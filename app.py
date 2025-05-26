import os
from flask import Flask, request, jsonify, redirect
from dotenv import load_dotenv
import openai
import stripe

load_dotenv()

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

YOUR_DOMAIN = os.getenv("YOUR_DOMAIN") or "http://localhost:5000"

@app.route("/api/generate-cardapio", methods=["POST"])
def generate_cardapio():
    data = request.json
    prompt = data.get("prompt", "Crie um cardápio saudável e simples para 7 dias.")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7
        )
        cardapio = response.choices[0].message.content
        return jsonify({"cardapio": cardapio})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.json
    price_id = data.get("priceId")  # você pode passar o ID do preço no corpo

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="payment",
            success_url=YOUR_DOMAIN + "/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=YOUR_DOMAIN + "/cancel",
        )
        return jsonify({"url": checkout_session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return "Backend rodando. Use /api/generate-cardapio e /create-checkout-session."

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
