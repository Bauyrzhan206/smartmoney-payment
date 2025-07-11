from flask import Flask, request, redirect
import requests
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# === Конфиг Airba Pay (PROD) ===
API_BASE = "https://ps.airbapay.kz/acquiring-api/api/v1"
AUTH_DATA = {
    "user": "IDEAL-R",
    "password": "xZ3r.=r_?9wPb_",
    "terminal_id": "68709560148c066ef0b45277"
}

SUCCESS_CALLBACK = "https://smartmoneykz.kz/payment/success"
FAILURE_CALLBACK = "https://smartmoneykz.kz/payment/failure"

# === Конфиг Email ===
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "rollpizza.uralsk@gmail.com"      # твой Gmail
SMTP_PASSWORD = "YOUR_APP_PASSWORD"           # сюда вставь App Password (не обычный пароль!)
TO_EMAIL = "rollpizza.uralsk@gmail.com"       # куда слать уведомления

def send_email(subject, body):
    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = TO_EMAIL

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, TO_EMAIL, msg.as_string())
        server.quit()
        print("✅ Email sent!")
    except Exception as e:
        print("❌ Email send failed:", str(e))


@app.route("/")
def home():
    return "✅ Smart Money PROD API + Email уведомления работают!"


@app.route("/pay")
def pay():
    order_id = request.args.get("order_id")
    amount = request.args.get("amount")

    if not order_id or not amount:
        return "⛔ Missing order_id or amount", 400

    # === Авторизация ===
    try:
        auth_resp = requests.post(f"{API_BASE}/auth/sign-in", json=AUTH_DATA)
        auth_resp.raise_for_status()
        auth_data = auth_resp.json()
        token = auth_data.get("access_token")
        if not token:
            return f"⛔ No token in response: {auth_data}", 500
    except Exception as e:
        return f"⛔ Auth error: {str(e)} | RAW: {auth_resp.text}", 500

    print("✅ AUTH:", auth_resp.status_code, auth_resp.text)

    # === Создание платежа ===
    try:
        pay_payload = {
            "amount": int(amount),
            "currency": "KZT",
            "order_id": order_id,
            "callback_url": SUCCESS_CALLBACK,
            "fail_callback_url": FAILURE_CALLBACK,
            "description": f"SmartMoney Order {order_id}"
        }

        headers = {"Authorization": f"Bearer {token}"}
        pay_resp = requests.post(f"{API_BASE}/payment/create", json=pay_payload, headers=headers)
        pay_resp.raise_for_status()

        print("✅ PAY:", pay_resp.status_code, pay_resp.text)

        try:
            pay_data = pay_resp.json()
        except Exception as e:
            return f"⛔ JSON decode failed: {str(e)} | RAW: {pay_resp.text}", 500

        payment_url = pay_data.get("payment_url")
        if not payment_url:
            return f"⛔ No payment_url in response: {pay_data}", 500

        return redirect(payment_url)

    except Exception as e:
        return f"⛔ Payment error: {str(e)} | RAW: {pay_resp.text}", 500

# === Success callback ===
@app.route("/payment/success", methods=["POST"])
def payment_success():
    data = request.json
    print("✅ SUCCESS CALLBACK:", data)

    subject = "✅ Оплата успешна (SmartMoney)"
    body = f"""
    <h3>Новая успешная оплата</h3>
    <p><b>Заказ:</b> {data.get('order_id')}</p>
    <p><b>Сумма:</b> {data.get('amount')} KZT</p>
    <p><b>Статус:</b> {data.get('status')}</p>
    """

    send_email(subject, body)
    return "OK", 200

# === Failure callback ===
@app.route("/payment/failure", methods=["POST"])
def payment_failure():
    data = request.json
    print("❌ FAILURE CALLBACK:", data)

    subject = "❌ Оплата неуспешна (SmartMoney)"
    body = f"""
    <h3>Неуспешная оплата</h3>
    <p><b>Заказ:</b> {data.get('order_id')}</p>
    <p><b>Сумма:</b> {data.get('amount')} KZT</p>
    <p><b>Статус:</b> {data.get('status')}</p>
    """

    send_email(subject, body)
    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True)
