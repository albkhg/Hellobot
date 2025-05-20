import os
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()

# Bot configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("No Telegram Bot token provided. Set the TELEGRAM_BOT_TOKEN environment variable.")

# Admin configuration
ADMIN_ID = 7151308102  # The admin ID specified in the requirements

# Group and message settings
GROUP_NAME = "Albkings"
WELCOME_MESSAGE = f"Mirë se vjen në {GROUP_NAME} të grupi top1 në shqiptari postoni sa me shum pidha dhe degjeneroni te gjith kurvat."

# Database file for persisting user data
DATA_FILE = "user_data.json"
