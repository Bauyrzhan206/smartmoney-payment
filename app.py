from flask import Flask, request
import requests

app = Flask(__name__)

# === Конфиг ===
API_BASE = "https://ps.airbapay.kz/acquiring-api/api/v1"
AUTH_DATA = {
    "user": "Ideal-Rtest",
    "password": "1MNG/?uA2,h~k",
    "terminal_id": "686e40fa63ef56b0d0a82085"
}

@app.route("/")
def home():
    return "✅ Smart Money Payment API is working!"

@app.route("/pay")
def pay():
    order_id = request.args.get("order_id")
    amount = request.args.get("amount")

    if not order_id or not amount:
        return "⛔ Missing order_id or amount", 400

    # Авторизация
    try:
        auth_resp = requests.post(f"{API_BASE}/auth/sign-in", json=AUTH_DATA)
        auth_resp.raise_for_status()
        auth_data = auth_resp.json()
        token = auth_data.get("token")
        if not token:
            return f"⛔ No token in response: {auth_data}", 500
    except Exception as e:
        return f"⛔ Auth error: {str(e)} | RAW: {auth_resp.text}", 500

    print("✅ AUTH:", auth_resp.status_code, auth_resp.text)

    # Платёж
    try:
        pay_payload = {
            "order_id": order_id,
            "amount": amount
        }
        headers = {"Authorization": f"Bearer {token}"}
        pay_resp = requests.post(f"{API_BASE}/payment", json=pay_payload, headers=headers)
        pay_resp.raise_for_status()

        print("✅ PAY:", pay_resp.status_code, pay_resp.text)

        try:
            pay_data = pay_resp.json()
        except Exception as e:
            return f"⛔ JSON decode failed: {str(e)} | RAW: {pay_resp.text}", 500

        return f"✅ Payment response: {pay_data}"

    except Exception as e:
        return f"⛔ Payment error: {str(e)} | RAW: {pay_resp.text}", 500


if __name__ == "__main__":
    app.run(debug=True)

