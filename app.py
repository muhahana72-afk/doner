import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, ConversationHandler

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# States for conversation
START, PHONE, FOOD, PRICE, LOCATION = range(5)

# Bot token (replace with your actual token)
TOKEN = '8257697001:AAEKhj2l8JPcilAUXYZ6Xd709KwTsFg3Fn8'

# Group chat ID (replace with actual group ID)
GROUP_CHAT_ID = '-4891848671'  # Placeholder

# Food options with prices
FOODS = {
    'lavash': {'name': 'Lavash', 'prices': {'oddiy': 20000, 'standart': 30000, 'chizz': 35000}},
    'hotdog': {'name': 'Hotdog', 'prices': {'oddiy': 8000, '2x': 10000, '3x_asarti': 15000, 'milliy': 20000, '4x': 22000, 'katta_asarti': 25000, 'boing': 30000, 'boing_787': 35000}},
    'burger': {'name': 'Burger', 'prices': {'oddiy': 15000, 'chizz': 20000, 'extra': 25000, 'dabble': 30000}},
    'non_kavob': {'name': 'Non Kavob', 'prices': {'oddiy': 15000, '2x': 25000}},
    'kofe': {'name': 'Kofe', 'prices': {'maccofe': 5000, 'cappucino': 10000}}
}

# User data storage (in production, use database)
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[KeyboardButton("Telefon raqamini yuborish", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Assalomu aleykum! Telefon raqamingizni yuboring:", reply_markup=reply_markup)
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text
    user_data[update.effective_user.id] = {'phone': phone}
    keyboard = [[InlineKeyboardButton(food['name'], callback_data=food_key)] for food_key, food in FOODS.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Qanday fastfood hohlaysiz?", reply_markup=reply_markup)
    return FOOD

async def food_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    food_key = query.data
    user_data[update.effective_user.id]['food'] = food_key
    food = FOODS[food_key]
    keyboard = [[InlineKeyboardButton(f"{size}: {price} UZS", callback_data=f"{food_key}_{size}")] for size, price in food['prices'].items()]
    keyboard.append([InlineKeyboardButton("Orqaga", callback_data='back')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=f"Qanday narxda {food['name']} hohlaysiz?", reply_markup=reply_markup)
    return PRICE

async def price_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == 'back':
        keyboard = [[InlineKeyboardButton(food['name'], callback_data=food_key)] for food_key, food in FOODS.items()]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Qanday fastfood hohlaysiz?", reply_markup=reply_markup)
        return FOOD
    data = query.data.split('_')
    food_key, size = data[0], data[1]
    price = FOODS[food_key]['prices'][size]
    user_data[update.effective_user.id]['price'] = price
    user_data[update.effective_user.id]['size'] = size
    keyboard = [[KeyboardButton("Location tashlash", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Location tashlash:", reply_markup=reply_markup)
    return LOCATION


async def receive_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if update.message.location:
        user_data[user_id]['location'] = update.message.location
        # Generate order number
        order_number = f"#{user_id}_{len(user_data)}"
        data = user_data[user_id]
        user = update.effective_user
        user_name = f"{user.first_name} {user.last_name or ''}".strip()
        username = f"@{user.username}" if user.username else ""
        message = f"Yangi buyurtma!\nRaqam: {order_number}\nFoydalanuvchi: {user_name} {username}\nTelefon: {data['phone']}\nOvqat: {FOODS[data['food']]['name']} ({data['size']})\nNarx: {data['price']} UZS"
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=message)
        await context.bot.send_location(chat_id=GROUP_CHAT_ID, latitude=data['location'].latitude, longitude=data['location'].longitude)
        await update.message.reply_text("Buyurtmangiz qabul qilindi! Rahmat.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Iltimos, location yuboring.")
        return LOCATION

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Bekor qilindi.")
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [MessageHandler(None, phone)],
            FOOD: [CallbackQueryHandler(food_selection)],
            PRICE: [CallbackQueryHandler(price_selection)],
            LOCATION: [MessageHandler(None, receive_location)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()