from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from config import PACKAGES, ADMIN_ID, CARD_NUMBER, format_price
from database import Database

(SELECT_PACKAGE, ENTER_GAME_ID, ENTER_SERVER,
 CONFIRM_ORDER, WAIT_PAYMENT) = range(5)


def packages_keyboard():
    keyboard = []
    items = list(PACKAGES.items())
    for i in range(0, len(items), 2):
        row = []
        for name, data in items[i:i + 2]:
            row.append(InlineKeyboardButton(
                f"{data['diamonds']}💎 — {format_price(data['price'])}",
                callback_data=f"pkg_{name}"
            ))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(keyboard)


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Купить алмазы", callback_data="buy")],
        [InlineKeyboardButton("📋 Мои заказы", callback_data="my_orders")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")],
    ])


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
    await update.message.reply_text(text, parse_mode="Markdown",
                                    reply_markup=main_menu())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    db: Database = context.bot_data["db"]

    if data == "buy":
        await query.edit_message_text(
            "💎 *Выбери пакет алмазов:*\n\nВсе цены в узбекских сумах.",
            parse_mode="Markdown",
            reply_markup=packages_keyboard()
        )
        return SELECT_PACKAGE

    if data.startswith("pkg_"):
        pkg_name = data[4:]
        pkg = PACKAGES.get(pkg_name)
        if not pkg:
            await query.edit_message_text("❌ Пакет не найден. /start")
            return ConversationHandler.END

        context.user_data["package"] = pkg_name
        context.user_data["diamonds"] = pkg["diamonds"]
        context.user_data["price"] = pkg["price"]

        await query.edit_message_text(
            f"✅ Выбрано: *{pkg['diamonds']} алмазов* — "
            f"{format_price(pkg['price'])}\n\n"
            f"📝 Введи свой *Game ID* в Mobile Legends\n\n"
            f"_(Найти можно в игре: Профиль → твой ID под ником)_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
            ])
        )
        return ENTER_GAME_ID

    if data == "confirm_pay":
        user_id = update.effective_user.id
        order = context.user_data.get("order_id")
        if not order:
            await query.edit_message_text("❌ Заказ не найден. /start")
            return ConversationHandler.END

        db_order = db.get_order(order)
        if not db_order:
            await query.edit_message_text("❌ Заказ не найден. /start")
            return ConversationHandler.END

        db.update_status(order, "awaiting_payment")

        await query.edit_message_text(
            f"💳 *Оплата заказа {db_order['order_id']}*\n\n"
            f"Сумма: *{format_price(db_order['price'])}*\n\n"
            f"Переведи на карту:\n"
            f"`{CARD_NUMBER}`\n\n"
            f"После оплаты нажми «✅ Оплатил» и пришли скриншот чека.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Оплатил — отправить чек",
                                      callback_data="paid")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel")],
            ])
        )
        return WAIT_PAYMENT

    if data == "paid":
        await query.edit_message_text(
            "📸 *Отправь скриншот чека об оплате*\n\n"
            "Пришли фото или скриншот из Payme / Click.",
            parse_mode="Markdown"
        )
        return WAIT_PAYMENT

    if data == "my_orders":
        context.user_data.clear()
        user_id = update.effective_user.id
        order = db.get_latest_order(user_id)
        if not order:
            await query.edit_message_text(
                "У тебя пока нет заказов.\n\n"
                "Нажми /start чтобы сделать заказ.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Главная",
                                          callback_data="home")]
                ])
            )
        else:
            await query.edit_message_text(
                f"📋 *Последний заказ:*\n\n"
                f"ID: `{order['order_id']}`\n"
                f"💎 Алмазы: {order['diamonds']}\n"
                f"🎮 Game ID: `{order['game_id']}`\n"
                f"🌐 Сервер: {order['server']}\n"
                f"💰 Сумма: {format_price(order['price'])}\n"
                f"📌 Статус: *{order['status']}*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Главная",
                                          callback_data="home")]
                ])
            )
        return ConversationHandler.END

    elif data == "help":
        context.user_data.clear()
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
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Главная",
                                      callback_data="home")]
            ])
        )
        return ConversationHandler.END

    elif data == "home":
        context.user_data.clear()
        await query.edit_message_text(
            "⚡️ *SAINT — Топап алмазов MLBB*",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        return ConversationHandler.END

    elif data == "cancel":
        context.user_data.clear()
        await query.edit_message_text(
            "❌ Заказ отменён.\n\nНажми /start чтобы начать заново."
        )
        return ConversationHandler.END

    return None


async def receive_game_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game_id = update.message.text.strip()
    if not game_id or not game_id.isdigit() or len(game_id) < 6:
        await update.message.reply_text(
            "⚠️ Game ID должен содержать минимум 6 цифр.\n"
            "Попробуй ещё раз:"
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
    if not server:
        await update.message.reply_text(
            "⚠️ Введи номер сервера:"
        )
        return ENTER_SERVER

    context.user_data["server"] = server
    user_id = update.effective_user.id
    db: Database = context.bot_data["db"]

    order = db.create_order(
        user_id=user_id,
        username=update.effective_user.username or "",
        game_id=context.user_data["game_id"],
        server=server,
        package_name=context.user_data["package"],
        diamonds=context.user_data["diamonds"],
        price=context.user_data["price"],
    )
    context.user_data["order_id"] = order["id"]

    await update.message.reply_text(
        f"📦 *Подтверди заказ:*\n\n"
        f"💎 Алмазы: *{context.user_data['diamonds']}*\n"
        f"🎮 Game ID: `{context.user_data['game_id']}`\n"
        f"🌐 Сервер: `{server}`\n"
        f"💰 Сумма: *{format_price(context.user_data['price'])}*\n\n"
        f"Всё верно?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Подтвердить и оплатить",
                                  callback_data="confirm_pay")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")],
        ])
    )
    return CONFIRM_ORDER


async def receive_payment_screenshot(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id
    db: Database = context.bot_data["db"]
    order_id = context.user_data.get("order_id")
    if order_id:
        order = db.get_order(order_id)
    else:
        order = db.get_latest_order(user_id)

    if not order:
        await update.message.reply_text("❌ Заказ не найден. /start")
        return ConversationHandler.END

    db.update_status(order["id"], "verifying_payment")

    await update.message.reply_text(
        "✅ *Чек получен!*\n\n"
        "Проверяем оплату и пополняем алмазы.\n"
        "Обычно это занимает 5-15 минут.\n\n"
        "Мы уведомим тебя когда алмазы будут зачислены 🎮",
        parse_mode="Markdown"
    )

    caption = (
        f"🆕 *НОВЫЙ ЗАКАЗ — SAINT*\n\n"
        f"Order: `{order['order_id']}`\n"
        f"👤 @{order['username']} (ID: {user_id})\n"
        f"💎 {order['diamonds']} алмазов\n"
        f"🎮 Game ID: `{order['game_id']}`\n"
        f"🌐 Сервер: `{order['server']}`\n"
        f"💰 {format_price(order['price'])}\n\n"
        f"⬆️ Скриншот оплаты выше"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Выполнен",
                              callback_data=f"done_{order['id']}")],
        [InlineKeyboardButton("❌ Отклонить",
                              callback_data=f"reject_{order['id']}")],
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
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    data = query.data
    db: Database = context.bot_data["db"]

    if data.startswith("done_"):
        order_id = int(data[5:])
        order = db.get_order(order_id)
        if not order:
            return
        db.update_status(order_id, "completed")

        await context.bot.send_message(
            chat_id=order["user_id"],
            text=(
                f"🎉 *Алмазы зачислены!*\n\n"
                f"💎 {order['diamonds']} алмазов успешно добавлены.\n"
                f"Game ID: `{order['game_id']}`\n\n"
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
        order_id = int(data[7:])
        order = db.get_order(order_id)
        if not order:
            return
        db.update_status(order_id, "rejected")

        await context.bot.send_message(
            chat_id=order["user_id"],
            text=(
                "❌ *Оплата не подтверждена*\n\n"
                "Свяжись с поддержкой: @SAINT_support\n"
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
    await update.message.reply_text(
        "❌ Отменено. Нажми /start чтобы начать заново."
    )
    return ConversationHandler.END
