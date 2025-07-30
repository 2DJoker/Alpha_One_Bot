import os
import requests
import time

API_URL = "https://pay.crypt.bot/api/"
API_KEY = os.getenv('CRYPTOBOT_API_KEY')

def create_invoice(amount_rub: int):
    headers = {"Crypto-Pay-API-Token": API_KEY}
    payload = {
        "amount": amount_rub,
        "asset": "USDT",  
        "description": "Доступ к приватному каналу",
        "hidden_message": "Спасибо за оплату!",
        "fiat": "RUB",
        "paid_btn_name": "viewItem",
        "paid_btn_url": "https://t.me/your_bot",
        "allow_anonymous": False
    }
    
    try:
        response = requests.post(f"{API_URL}createInvoice", headers=headers, json=payload)
        data = response.json()
        if data.get('ok'):
            return data['result']
        else:
            print("CryptoBot error:", data.get('error'))
            return None
    except Exception as e:
        print("CryptoBot exception:", e)
        return None

def check_payment(user_id: int):
    
    return False  