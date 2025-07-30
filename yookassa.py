import os
import uuid
import requests
import base64

SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')
SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY')
AUTH = base64.b64encode(f"{SHOP_ID}:{SECRET_KEY}".encode()).decode()

def create_payment(amount: float, user_id: int):
    headers = {
        "Authorization": f"Basic {AUTH}",
        "Idempotence-Key": str(uuid.uuid4()),
        "Content-Type": "application/json"
    }
    
    payload = {
        "amount": {
            "value": f"{amount:.2f}",
            "currency": "RUB"
        },
        "capture": True,
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/your_bot"
        },
        "description": f"Доступ к каналу для пользователя {user_id}",
        "metadata": {"user_id": user_id}
    }
    
    try:
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            headers=headers,
            json=payload
        )
        data = response.json()
        if response.status_code == 200:
            return data
        else:
            print("ЮKassa error:", data.get('description'))
            return None
    except Exception as e:
        print("ЮKassa exception:", e)
        return None

def check_payment(user_id: int):
    return False