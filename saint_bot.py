"""
SAINT - Mobile Legends Diamond Top-up Bot
Telegram Bot для продажи алмазов Mobile Legends

Установка:
    pip install python-telegram-bot==20.7

Запуск:
    python saint_bot.py

Переменные окружения (или заполни прямо здесь):
    BOT_TOKEN   - токен от @BotFather
    ADMIN_ID    - твой Telegram ID (узнать у @userinfobot)
    CARD_NUMBER - номер карты для оплаты (Payme/Click реквизиты)
"""

import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler,
)

# ─── НАСТРОЙКИ ───────────────────────────────────────────────
BOT_TOKEN   = os.getenv("BOT_TOKEN", "ВСТАВЬ_ТОКЕН_СЮДА")
ADMIN_ID    = int(os.getenv("ADMIN_ID", "ВСТАВЬ_СВОЙ_ID"))
CARD_NUMBER = os.getenv("CARD_NUMBER", "1234 5678 9012 3456")  # Payme/Click карта

# Прайс-лист алмазов (количество: цена в сумах)
PACKAGES = {
    "💎 86 алмазов":    {"diamonds": 86,   "price": 15_000},
    "💎 172 алмаза":   {"diamonds": 172,  "price": 29_000},
    "💎 257 алмазов":  {"diamonds": 257,  "price": 43_000},
    "💎 344 алмаза":   {"diamonds": 344,  "price": 57_000},
    "💎 429 алмазов":  {"diamonds": 429,  "price": 70_000},
    "💎 514 алмазов":  {"diamonds": 514,  "price": 84_000},
    "💎 706 алмазов":  {"diamonds": 706,  "price": 114_000},
    "💎 878 алмазов":  {"diamonds": 878,  "price": 141_000},
    "💎 963 алмаза":   {"diamonds": 963,  "price": 154_000},
    "💎 1412 алмазов": {"diamonds": 1412, "price": 225_000},
    "💎 2195 алмазов": {"diamonds": 2195, "price": 348_000},
    "💎 3688 алмазов": {"diamonds": 3688, "price": 582_000},
}

# ─── СОСТОЯНИЯ ДИАЛОГА ───────────────────────────────────────
SELECT_PACKAGE, ENTER_GAME_ID, ENTER_SERVER, CONFIRM_ORDER, WAIT_PAYMENT = range(5)

# Временное хранилище заказов (в продакшн замени на БД)
orders = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─── ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ─────────────────────────────────

def format_price(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " сум"


def get_order_id(user_id: int) -> str:
    return f"SAINT-{user_id}-{datetime.now().strftime('%d%m%H%M')}"


def packages_keyboard():
    keyboard = []
    items = list(PACKAGES.items())
    for i in range(0, len(items), 2):
        row = []
        for name, data in items[i:i+2]:
            row.append(InlineKeyboardButton(
                f"{data['diamonds']}💎 — {format_price(data['price'])}",
                callback_data=f"pkg_{name}"
            ))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(keyboard)


# ─── ХЭНДЛЕРЫ ────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"⚡️ *SAINT — Топап алмазов MLBB*\n\n"
        f"Привет, {user.first_name}! 👋\n\n"
        f"Здесь ты можешь купить алмазы для Mobile Legends "
        f"по самым низким ценам в Узбекистане.\n\n"
        f"🔥 *Почему SAINT?*\n"
        f"• Дешевле чем в игре на 20-30%\n"
        f"• Пополнение за 5-15 минут\n"
        f"• Оплата через Payme / Click\n"
        f"• Работаем 24/7\n\n"
        f"Нажми кнопку ниже чтобы сделать заказ 👇"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Купить алмазы", callback_data="buy")],
        [InlineKeyboardButton("📋 Мои заказы", callback_data="my_orders")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")],
    ])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "buy":
        await query.edit_message_text(
            "💎 *Выбери пакет алмазов:*\n\nВсе цены в узбекских сумах.",
            parse_mode="Markdown",
            reply_markup=packages_keyboard()
        )
        return SELECT_PACKAGE

    elif data.startswith("pkg_"):
        pkg_name = data[4:]
        pkg = PACKAGES.get(pkg_name)
        if not pkg:
            await query.edit_message_text("❌ Пакет не найден. Начни заново /start")
            return ConversationHandler.END

        context.user_data["package"] = pkg_name
        context.user_data["diamonds"] = pkg["diamonds"]
        context.user_data["price"] = pkg["price"]

        await query.edit_message_text(
            f"✅ Выбрано: *{pkg['diamonds']} алмазов* — {format_price(pkg['price'])}\n\n"
            f"📝 Введи свой *Game ID* в Mobile Legends\n\n"
            f"_(Найти можно в игре: Профиль → твой ID под ником)_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]])
        )
        return ENTER_GAME_ID

    elif data == "confirm_pay":
        user_id = update.effective_user.id
        order = orders.get(user_id, {})
        order_id = get_order_id(user_id)
        order["order_id"] = order_id
        order["status"] = "ожидает оплаты"
        orders[user_id] = order

        await query.edit_message_text(
            f"💳 *Оплата заказа {order_id}*\n\n"
            f"Сумма: *{format_price(order['price'])}*\n\n"
            f"Переведи на карту:\n"
            f"`{CARD_NUMBER}`\n\n"
            f"После оплаты нажми кнопку «✅ Оплатил» и пришли скриншот чека.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Оплатил — отправить чек", callback_data="paid")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel")],
            ])
        )
        return WAIT_PAYMENT

    elif data == "paid":
        user_id = update.effective_user.id
        order = orders.get(user_id, {})
        order["status"] = "ожидает проверки"
        orders[user_id] = order

        await query.edit_message_text(
            "📸 *Отправь скриншот чека об оплате*\n\n"
            "Пришли фото или скриншот из Payme / Click.",
            parse_mode="Markdown"
        )
        return WAIT_PAYMENT

    elif data == "my_orders":
        user_id = update.effective_user.id
        order = orders.get(user_id)
        if not order:
            await query.edit_message_text(
                "У тебя пока нет заказов.\n\nНажми /start чтобы сделать заказ.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главная", callback_data="home")]])
            )
        else:
            await query.edit_message_text(
                f"📋 *Последний заказ:*\n\n"
                f"ID заказа: `{order.get('order_id', '—')}`\n"
                f"Алмазы: {order.get('diamonds', '—')} 💎\n"
                f"Game ID: `{order.get('game_id', '—')}`\n"
                f"Сервер: {order.get('server', '—')}\n"
                f"Сумма: {format_price(order.get('price', 0))}\n"
                f"Статус: *{order.get('status', '—')}*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главная", callback_data="home")]])
            )

    elif data == "help":
        await query.edit_message_text(
            "❓ *Помощь*\n\n"
            "1. Нажми «Купить алмазы»\n"
            "2. Выбери пакет\n"
            "3. Введи Game ID и номер сервера\n"
            "4. Оплати на карту\n"
            "5. Пришли скриншот чека\n"
            "6. Получи алмазы в течение 5-15 минут\n\n"
            "По вопросам: @SAINT_support",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главная", callback_data="home")]])
        )

    elif data == "home":
        await query.edit_message_text(
            "⚡️ *SAINT — Топап алмазов MLBB*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💎 Купить алмазы", callback_data="buy")],
                [InlineKeyboardButton("📋 Мои заказы", callback_data="my_orders")],
                [InlineKeyboardButton("❓ Помощь", callback_data="help")],
            ])
        )

    elif data == "cancel":
        context.user_data.clear()
        await query.edit_message_text(
            "❌ Заказ отменён.\n\nНажми /start чтобы начать заново."
        )
        return ConversationHandler.END


async def receive_game_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game_id = update.message.text.strip()
    if not game_id.isdigit():
        await update.message.reply_text(
            "⚠️ Game ID должен состоять только из цифр.\nПопробуй ещё раз:"
        )
        return ENTER_GAME_ID

    context.user_data["game_id"] = game_id
    await update.message.reply_text(
        f"✅ Game ID: `{game_id}`\n\n"
        f"Теперь введи номер *сервера* (Server ID)\n\n"
        f"_(Найти можно рядом с Game ID в профиле игры)_",
        parse_mode="Markdown"
    )
    return ENTER_SERVER


async def receive_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    server = update.message.text.strip()
    context.user_data["server"] = server
    user_id = update.effective_user.id

    # Сохраняем заказ
    orders[user_id] = {
        "game_id":  context.user_data["game_id"],
        "server":   server,
        "diamonds": context.user_data["diamonds"],
        "price":    context.user_data["price"],
        "package":  context.user_data["package"],
        "user_id":  user_id,
        "username": update.effective_user.username or "—",
        "status":   "новый",
    }

    pkg = context.user_data["package"]
    diamonds = context.user_data["diamonds"]
    price = context.user_data["price"]

    await update.message.reply_text(
        f"📦 *Подтверди заказ:*\n\n"
        f"💎 Алмазы: *{diamonds}*\n"
        f"🎮 Game ID: `{context.user_data['game_id']}`\n"
        f"🌐 Сервер: `{server}`\n"
        f"💰 Сумма: *{format_price(price)}*\n\n"
        f"Всё верно?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Подтвердить и оплатить", callback_data="confirm_pay")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")],
        ])
    )
    return CONFIRM_ORDER


async def receive_payment_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Клиент прислал скриншот оплаты — уведомляем админа."""
    user_id = update.effective_user.id
    order = orders.get(user_id, {})
    order["status"] = "проверка оплаты"
    orders[user_id] = order

    # Уведомление клиенту
    await update.message.reply_text(
        "✅ *Чек получен!*\n\n"
        "Проверяем оплату и пополняем алмазы.\n"
        "Обычно это занимает 5-15 минут.\n\n"
        "Мы уведомим тебя когда алмазы будут зачислены 🎮",
        parse_mode="Markdown"
    )

    # Уведомление админу
    caption = (
        f"🆕 *НОВЫЙ ЗАКАЗ — SAINT*\n\n"
        f"Order ID: `{order.get('order_id', '—')}`\n"
        f"👤 Клиент: @{order.get('username', '—')} (ID: {user_id})\n"
        f"💎 Алмазы: {order.get('diamonds', '—')}\n"
        f"🎮 Game ID: `{order.get('game_id', '—')}`\n"
        f"🌐 Сервер: `{order.get('server', '—')}`\n"
        f"💰 Сумма: {format_price(order.get('price', 0))}\n\n"
        f"⬆️ Скриншот оплаты выше"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Выполнен", callback_data=f"done_{user_id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user_id}")],
    ])

    if update.message.photo:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    elif update.message.document:
        await context.bot.send_document(
            chat_id=ADMIN_ID,
            document=update.message.document.file_id,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    else:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=caption + "\n\n⚠️ Клиент не прислал фото!",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    return ConversationHandler.END


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок для админа — выполнен/отклонён."""
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    data = query.data
    if data.startswith("done_"):
        client_id = int(data[5:])
        order = orders.get(client_id, {})
        order["status"] = "выполнен ✅"
        orders[client_id] = order

        await context.bot.send_message(
            chat_id=client_id,
            text=(
                f"🎉 *Алмазы зачислены!*\n\n"
                f"💎 {order.get('diamonds', '')} алмазов успешно добавлены на аккаунт.\n"
                f"Game ID: `{order.get('game_id', '')}`\n\n"
                f"Спасибо за покупку! 🙌\n"
                f"Возвращайся снова → /start"
            ),
            parse_mode="Markdown"
        )
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n✅ *ВЫПОЛНЕН*",
            parse_mode="Markdown"
        )

    elif data.startswith("reject_"):
        client_id = int(data[7:])
        order = orders.get(client_id, {})
        order["status"] = "отклонён ❌"
        orders[client_id] = order

        await context.bot.send_message(
            chat_id=client_id,
            text=(
                "❌ *Оплата не подтверждена*\n\n"
                "К сожалению, мы не смогли подтвердить твою оплату.\n"
                "Пожалуйста, свяжись с поддержкой: @SAINT_support\n\n"
                "Или сделай новый заказ → /start"
            ),
            parse_mode="Markdown"
        )
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n❌ *ОТКЛОНЁН*",
            parse_mode="Markdown"
        )


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Отменено. Нажми /start чтобы начать заново.")
    return ConversationHandler.END


# ─── ЗАПУСК ──────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^buy$")],
        states={
            SELECT_PACKAGE: [CallbackQueryHandler(button_handler, pattern="^pkg_")],
            ENTER_GAME_ID:  [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_game_id)],
            ENTER_SERVER:   [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_server)],
            CONFIRM_ORDER:  [CallbackQueryHandler(button_handler, pattern="^confirm_pay$")],
            WAIT_PAYMENT:   [
                CallbackQueryHandler(button_handler, pattern="^paid$"),
                MessageHandler(filters.PHOTO | filters.Document.ALL, receive_payment_screenshot),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CallbackQueryHandler(button_handler, pattern="^cancel$"),
        ],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(done|reject)_"))

    print("🚀 SAINT Bot запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
                  
