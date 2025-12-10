import telebot
from telebot import types
import datetime
import json
import os
import re

# === Sozlamalar ===
TOKEN = "8326480931:AAF6i3xAEAFQCDaat8lKKzEA1-p8Z6bI7xc"
ARIZA_CHANNEL = "@vazirlikd"  # Kanal username
DATA_FILE = "arizalar.json"      # Faylga yozish uchun
ADMIN_ID = 8497454087            # Admin Telegram ID

bot = telebot.TeleBot(TOKEN)
users = {}

# Fayl mavjud bo‘lmasa — yaratamiz
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=4)


# === /start komandasi ===
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    users[chat_id] = {}
    bot.send_message(chat_id, "👋 Assalomu alaykum!\nQo‘mondonga murojaat botiga xush kelibsiz.")
    bot.send_message(chat_id, "🧍‍♂️ Ism, familiya, otangiz ismini kiriting:")
    bot.register_next_step_handler(message, get_name)


# === Foydalanuvchidan ma’lumotlarni olish ===
def get_name(message):
    chat_id = message.chat.id
    users[chat_id]['name'] = message.text.strip()
    bot.send_message(chat_id, "📍 Tug‘ilgan joyingizni kiriting:")
    bot.register_next_step_handler(message, get_birthplace)


def get_birthplace(message):
    chat_id = message.chat.id
    users[chat_id]['birthplace'] = message.text.strip()
    bot.send_message(chat_id, "📞 Telefon raqamingizni kiriting (+998 bilan boshlansin):")
    bot.register_next_step_handler(message, get_phone)


def get_phone(message):
    chat_id = message.chat.id
    phone = message.text.strip()
    if not re.match(r'^\+998\d{9}$', phone):
        bot.send_message(chat_id, "❌ Noto‘g‘ri raqam! Iltimos, +998 bilan boshlanuvchi to‘liq raqam kiriting.")
        bot.register_next_step_handler(message, get_phone)
        return
    users[chat_id]['phone'] = phone
    bot.send_message(chat_id, "✍️ Endi arizangizni yozing yoki rasm/video/fayl yuboring.")
    bot.register_next_step_handler(message, save_ariza)


# === Arizani saqlash ===
def save_ariza(message):
    chat_id = message.chat.id
    if chat_id not in users or "phone" not in users[chat_id]:
        return

    user = users[chat_id]
    ariza_text = message.text if message.text else ""
    sana_vaqt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    info = (
        f"📥 *Yangi ariza!* \n\n"
        f"👤 F.I.Sh: {user.get('name')}\n"
        f"📍 Tug‘ilgan joy: {user.get('birthplace')}\n"
        f"📞 Telefon: {user.get('phone')}\n"
        f"📅 Sana: {sana_vaqt}\n\n"
        f"📝 Ariza:\n{ariza_text}"
    )

    # Kanalga yuborish
    if message.content_type == 'text':
        bot.send_message(ARIZA_CHANNEL, info, parse_mode="Markdown")
    elif message.content_type == 'photo':
        bot.send_photo(ARIZA_CHANNEL, message.photo[-1].file_id, caption=info, parse_mode="Markdown")
    elif message.content_type == 'video':
        bot.send_video(ARIZA_CHANNEL, message.video.file_id, caption=info, parse_mode="Markdown")
    elif message.content_type == 'document':
        bot.send_document(ARIZA_CHANNEL, message.document.file_id, caption=info, parse_mode="Markdown")

    # JSON faylga yozish
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    data.append({
        "ism": user.get('name'),
        "tugilgan_joy": user.get('birthplace'),
        "telefon": user.get('phone'),
        "ariza": ariza_text,
        "sana": sana_vaqt
    })

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    bot.send_message(chat_id, "✅ Arizangiz qabul qilindi.\nRahmat! Ma'lumotlaringiz yetkazildi.")


# === ADMIN PANEL ===
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Sizda bunga ruxsat yo‘q!")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Statistika", "🗂 So‘nggi arizalar", "📁 Faylni yuklab olish", "⬅️ Chiqish")
    bot.send_message(message.chat.id, "🧭 Admin panelga xush kelibsiz:", reply_markup=markup)


@bot.message_handler(func=lambda m: m.text == "📊 Statistika")
def stats(message):
    if message.chat.id != ADMIN_ID:
        return
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    jami = len(data)
    bot.send_message(message.chat.id, f"📈 Jami arizalar soni: {jami}")


@bot.message_handler(func=lambda m: m.text == "🗂 So‘nggi arizalar")
def last_arizalar(message):
    if message.chat.id != ADMIN_ID:
        return
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not data:
        bot.send_message(message.chat.id, "⚠️ Hozircha arizalar yo‘q.")
        return
    text = ""
    for item in data[-3:]:
        text += (f"👤 {item['ism']}\n"
                 f"📍 {item['tugilgan_joy']}\n"
                 f"📞 {item['telefon']}\n"
                 f"📅 {item['sana']}\n"
                 f"📝 {item['ariza']}\n\n")
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda m: m.text == "📁 Faylni yuklab olish")
def send_file(message):
    if message.chat.id != ADMIN_ID:
        return
    with open(DATA_FILE, "rb") as f:
        bot.send_document(message.chat.id, f)


@bot.message_handler(func=lambda m: m.text == "⬅️ Chiqish")
def exit_admin(message):
    if message.chat.id != ADMIN_ID:
        return
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "🔒 Admin panel yopildi.", reply_markup=markup)


# === BOTNI ISHGA TUSHIRISH ===
if __name__ == "__main__":
    print("🤖 Bot ishga tushdi...")
    bot.polling(none_stop=True)
