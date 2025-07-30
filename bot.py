import os
import logging
import asyncio
import uuid
import base64
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram import F
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import requests

load_dotenv()


bot = Bot(token=os.getenv('TELEGRAM_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
logging.basicConfig(level=logging.INFO)


CHANNEL_ID = "-1002853947878"  
PRICE = 100  


YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')
YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY')
YOOKASSA_AUTH = base64.b64encode(f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}".encode()).decode()
RETURN_URL = "@Alpha_One_Money_Bot"  

user_payments = {}  


def get_payment_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Криптовалюта ₿", callback_data="pay_crypto"),
            InlineKeyboardButton(text="Карта РФ 💳", callback_data="pay_card"),
        ],
        [
            InlineKeyboardButton(text="Проверить оплату ✅", callback_data="check_payment")
        ]
    ])
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"💰 Доступ к приватному каналу: {PRICE} руб.\n"
        "Выберите способ оплаты:",
        reply_markup=get_payment_keyboard()
    )

def create_yookassa_payment(user_id: int, amount: float, description: str):
    headers = {
        "Authorization": f"Basic {YOOKASSA_AUTH}",
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
            "return_url": RETURN_URL
        },
        "description": description,
        "metadata": {"user_id": user_id}
    }
    
    try:
        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            headers=headers,
            json=payload
        )
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"ЮKassa error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logging.error(f"ЮKassa exception: {e}")
        return None


def check_yookassa_payment(payment_id: str):
    headers = {
        "Authorization": f"Basic {YOOKASSA_AUTH}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"https://api.yookassa.ru/v3/payments/{payment_id}",
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"ЮKassa check error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logging.error(f"ЮKassa check exception: {e}")
        return None


@dp.callback_query(F.data == "pay_card")
async def process_card_payment(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    full_name = f"{callback.from_user.first_name} {callback.from_user.last_name or ''}".strip()
    
   
    payment = create_yookassa_payment(
        user_id=user_id,
        amount=PRICE,
        description=f"Доступ к каналу для {full_name} (ID: {user_id})"
    )
    
    if payment:
        payment_id = payment['id']
        user_payments[user_id] = payment_id
        
        confirmation_url = payment['confirmation']['confirmation_url']
        
        await callback.message.answer(
            "💳 Для оплаты перейдите по ссылке ниже:\n"
            "После оплаты нажмите кнопку 'Проверить оплату'",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Оплатить картой", url=confirmation_url)],
                [InlineKeyboardButton(text="Проверить оплату", callback_data="check_payment")]
            ])
        )
    else:
        await callback.message.answer("❌ Ошибка при создании платежа. Попробуйте позже.")

@dp.callback_query(F.data == "check_payment")
async def check_payment(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id not in user_payments:
        await callback.message.answer("❌ Платеж не найден. Пожалуйста, сначала произведите оплату.")
        return
    
    payment_id = user_payments[user_id]
    payment_info = check_yookassa_payment(payment_id)
    
    if not payment_info:
        await callback.message.answer("❌ Ошибка при проверке платежа. Попробуйте позже.")
        return
    
    status = payment_info.get('status')
    
    if status == 'succeeded':
        await callback.message.answer("✅ Оплата прошла успешно! Предоставляем доступ к каналу...")
        await grant_channel_access(user_id)
        del user_payments[user_id]
    elif status == 'pending':
        await callback.message.answer("⌛ Платеж в обработке. Попробуйте проверить позже.")
    else:
        await callback.message.answer(f"❌ Статус платежа: {status}. Если вы оплатили, попробуйте позже.")

async def grant_channel_access(user_id: int):
    try:
        chat = await bot.get_chat(CHANNEL_ID)
        
        if chat.invite_link:
            invite_link = chat.invite_link
        else:
            invite_link = await bot.export_chat_invite_link(CHANNEL_ID)
        
        await bot.send_message(
            user_id,
            f"✅ Добро пожаловать в приватный канал!\n"
            f"Ссылка для доступа: {invite_link}\n\n"
            "Если возникли проблемы с доступом, свяжитесь с администратором."
        )
        
    except Exception as e:
        logging.error(f"Ошибка доступа к каналу: {e}")
        await bot.send_message(
            user_id,
            "❌ Произошла ошибка при предоставлении доступа. Пожалуйста, свяжитесь с администратором."
        )

@dp.callback_query(F.data == "pay_crypto")
async def process_crypto_payment(callback: types.CallbackQuery):
    await callback.message.answer(
        "Оплата криптовалютой временно недоступна. Пожалуйста, выберите оплату картой."
    )

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())