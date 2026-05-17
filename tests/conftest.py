import os

os.environ.setdefault("BOT_TOKEN", "test:fake-token-for-testing")
os.environ.setdefault("ADMIN_ID", "12345")
os.environ.setdefault("CARD_NUMBER", "0000000000000000")
os.environ.setdefault("DATABASE_PATH", ":memory:")

pytest_plugins = ("pytest_asyncio",)
