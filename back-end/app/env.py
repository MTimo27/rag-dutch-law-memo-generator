import os
from dotenv import load_dotenv

load_dotenv()

def get_memo_table_name():
    env = os.getenv("APP_ENV", "development")
    return "memos_prod" if env == "production" else "memos"
