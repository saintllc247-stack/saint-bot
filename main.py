import logging

from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler,
)

from config import BOT_TOKEN
from database import Database, DATABASE_PATH
from handlers import (
    start, button_handler, receive_game_id, receive_server,
    receive_payment_screenshot, admin_callback, cancel_command,
    SELECT_PACKAGE, ENTER_GAME_ID, ENTER_SERVER,
    CONFIRM_ORDER, WAIT_PAYMENT,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def build_app() -> Application:
    db = Database(DATABASE_PATH)

    app = Application.builder().token(BOT_TOKEN).build()
    app.bot_data["db"] = db

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^buy$")],
        states={
            SELECT_PACKAGE: [
                CallbackQueryHandler(button_handler, pattern="^pkg_")
            ],
            ENTER_GAME_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND,
                               receive_game_id)
            ],
            ENTER_SERVER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND,
                               receive_server)
            ],
            CONFIRM_ORDER: [
                CallbackQueryHandler(button_handler, pattern="^confirm_pay$")
            ],
            WAIT_PAYMENT: [
                CallbackQueryHandler(button_handler, pattern="^paid$"),
                MessageHandler(filters.PHOTO | filters.Document.ALL,
                               receive_payment_screenshot),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CallbackQueryHandler(button_handler, pattern="^cancel$"),
        ],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(admin_callback,
                                         pattern="^(done|reject)_"))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(button_handler))

    return app


def main():
    logger.info("SAINT Bot запущен!")
    app = build_app()

    app.post_shutdown = lambda _: app.bot_data["db"].close()

    app.run_polling()


if __name__ == "__main__":
    main()
