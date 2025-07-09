
from flask import Flask, request, redirect
import requests

app = Flask(__name__)

API_URL = "https://sps.airbapay.kz/acquiring-api/api/v1"
USER = "Ideal-Rtest"
PASSWORD = "1MNG/?uA2,h~k"
TERMINAL_ID = "686e40fa63ef56b0d0a82085"

@app.route("/pay")
def pay():
    order_id = request.args.get("order_id", "test-order-001")
    amount = request.args.get("amount", "1000")

    # Авторизация
    auth_payload = {
        "user": USER,
        "password": PASSWORD,
        "terminal_id": TERMINAL_ID
    }
    auth_resp = requests.post(f"{API_URL}/auth/sign-in", json=auth_payload)
    token = auth_resp.json().get("access_token")
    if not token:
        return "Auth failed", 400

    # Создание платежа
    payment_payload = {
        "amount": int(amount),
        "currency": "KZT",
        "order_id": order_id,
        "callback_url": "https://your-callback-url.com/callback",
        "description": "SmartMoney Test Payment"
    }
    headers = {"Authorization": f"Bearer {token}"}
    pay_resp = requests.post(f"{API_URL}/payment/create", json=payment_payload, headers=headers)
    pay_data = pay_resp.json()
    payment_url = pay_data.get("payment_url")

    if not payment_url:
        return f"Error creating payment: {pay_data}", 400

    return redirect(payment_url)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
