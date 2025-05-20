import logging
import os
import json
import time
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_ID = 7151308102  # Admin user ID
WELCOME_MESSAGE = "Mirë se vjen në Albkings të grupi top1 në shqiptari postoni sa me shum pidha dhe degjeneroni te gjith kurvat"
DATABASE_FILE = "users_database.json"

# Database class
class Database:
    """
    A simple database class for managing user data with JSON persistence.
    """
    def __init__(self, database_file):
        self.database_file = database_file
        self.users = {}
        self.load_data()
        
    def load_data(self) -> None:
        """Load data from JSON file if it exists"""
        try:
            if os.path.exists(self.database_file):
                with open(self.database_file, 'r', encoding='utf-8') as file:
                    self.users = json.load(file)
                logger.info(f"Database loaded with {len(self.users)} users")
            else:
                logger.info("No existing database found, starting with empty database")
        except Exception as e:
            logger.error(f"Error loading database: {e}")
            self.users = {}
    
    def save_data(self) -> None:
        """Save data to JSON file"""
        try:
            with open(self.database_file, 'w', encoding='utf-8') as file:
                json.dump(self.users, file, ensure_ascii=False, indent=4)
            logger.info(f"Database saved with {len(self.users)} users")
        except Exception as e:
            logger.error(f"Error saving database: {e}")
    
    def add_user(self, user_id: int, username: Optional[str], first_name: str, 
                 last_name: Optional[str] = None) -> None:
        """
        Add a new user to the database or update an existing one
        
        Args:
            user_id: Telegram user ID
            username: Telegram username (optional)
            first_name: User's first name
            last_name: User's last name (optional)
        """
        # Convert user_id to string since JSON keys must be strings
        str_user_id = str(user_id)
        
        # Check if user already exists
        is_new_user = str_user_id not in self.users
        
        # Current timestamp for join date
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        
        # Update or create user data
        self.users[str_user_id] = {
            'user_id': user_id,
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'join_date': current_time if is_new_user else self.users[str_user_id].get('join_date', current_time)
        }
        
        # Save the updated database
        self.save_data()
        
        if is_new_user:
            logger.info(f"New user added: {first_name} (ID: {user_id})")
        else:
            logger.info(f"Existing user updated: {first_name} (ID: {user_id})")
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data by user ID"""
        return self.users.get(str(user_id))
    
    def get_all_users(self) -> Dict[int, Dict[str, Any]]:
        """Get all users"""
        # Convert string keys back to integers for user_ids
        return {int(user_id): user_data for user_id, user_data in self.users.items()}
    
    def get_user_count(self) -> int:
        """Get the total number of users"""
        return len(self.users)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get user statistics"""
        return {
            'total_users': len(self.users),
            'users': self.users
        }

# Initialize database
db = Database(DATABASE_FILE)

# Initialize bot
bot = telebot.TeleBot(7874374219:AAFdGhaAMKmjso_qTkM7xvcEtf6o4pH7JXc)

# Helper function
def is_admin(user_id: int) -> bool:
    """Check if a user is an admin"""
    return user_id == ADMIN_ID

# Command handlers
@bot.message_handler(commands=['start'])
def start_command(message):
    """Handler for the /start command"""
    user = message.from_user
    
    # Add the user to the database
    db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    bot.reply_to(message, 
        f"👋 Përshëndetje, {user.first_name}!\n\n"
        f"Unë jam Albkings Bot. Unë ndihmoj në menaxhimin e grupit dhe sigurim të funksionaliteteve të dobishme."
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    """Handler for the /help command"""
    help_text = (
        "🤖 <b>Albkings Bot Komandat</b>\n\n"
        "<b>Komandat e Përdoruesit:</b>\n"
        "/start - Fillo bot-in\n"
        "/help - Shfaq këtë mesazh ndihme\n\n"
        "<b>Komandat e Administratorit:</b>\n"
        "/broadcast - Dërgo një mesazh të gjithë përdoruesve\n"
        "/statistics - Shiko statistikat e përdoruesve\n"
        "/share - Ndaj një lidhje me të gjithë përdoruesit\n"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    """Handler for the /broadcast command - Admin only"""
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "⛔ Ju nuk jeni të autorizuar për të përdorur këtë komandë.")
        return
        
    message_text = message.text.replace('/broadcast', '', 1).strip()
    
    if not message_text:
        bot.reply_to(message, 
            "Ju lutem jepni një mesazh për të transmetuar.\n\n"
            "Shembull: /broadcast Përshëndetje të gjithëve! Ky është një njoftim i rëndësishëm."
        )
        return
    
    # Get all users
    users = db.get_all_users()
    successful_sends = 0
    failed_sends = 0
    
    # Send a confirmation message first
    bot.reply_to(message, f"📢 Duke filluar transmetimin tek {len(users)} përdorues...")
    
    # Broadcast the message to all users
    for user_id in users:
        try:
            bot.send_message(
                chat_id=user_id,
                text=f"📢 <b>Njoftim nga Administratori:</b>\n\n{message_text}",
                parse_mode='HTML'
            )
            successful_sends += 1
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {e}")
            failed_sends += 1
    
    # Send summary
    bot.send_message(
        message.chat.id,
        f"📢 Transmetimi u kompletua!\n"
        f"✅ Dërguar me sukses: {successful_sends}\n"
        f"❌ Dështuar: {failed_sends}"
    )

@bot.message_handler(commands=['statistics'])
def statistics_command(message):
    """Handler for the /statistics command - Admin only"""
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "⛔ Ju nuk jeni të autorizuar për të përdorur këtë komandë.")
        return
        
    stats = db.get_statistics()
    total_users = stats.get('total_users', 0)
    
    # Start with the header and total count
    result = f"📊 <b>Statistikat e Bot-it</b>\n\n"
    result += f"👥 <b>Përdorues Total:</b> {total_users}\n\n"
    
    # Add recent users if there are any
    if total_users > 0:
        result += f"<b>Përdoruesit e Fundit:</b>\n"
        # Get the 10 most recent users
        users = stats.get('users', {})
        # Sort users by join date (newest first) and take the first 10
        recent_users = sorted(
            users.items(), 
            key=lambda x: x[1].get('join_date', ''), 
            reverse=True
        )[:10]
        
        for i, (user_id, user_data) in enumerate(recent_users, 1):
            username = user_data.get('username', 'None')
            first_name = user_data.get('first_name', 'Unknown')
            last_name = user_data.get('last_name', '')
            join_date = user_data.get('join_date', 'Unknown')
            
            name_display = f"{first_name} {last_name}".strip()
            username_display = f"@{username}" if username and username != 'None' else "No username"
            
            result += f"{i}. <b>{name_display}</b> ({username_display})\n"
            result += f"   📅 Bashkuar më: {join_date}\n"
    
    bot.send_message(message.chat.id, result, parse_mode='HTML')

@bot.message_handler(commands=['share'])
def share_command(message):
    """Handler for the /share command - Admin only"""
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "⛔ Ju nuk jeni të autorizuar për të përdorur këtë komandë.")
        return
        
    command_parts = message.text.split(' ', 2)
    
    # Check if we have enough arguments (command, button text, and URL)
    if len(command_parts) < 3:
        bot.reply_to(message,
            "Ju lutem jepni tekstin e butonit dhe URL-në.\n\n"
            "Shembull: /share 'Bashkohu në Kanalin Tonë' https://t.me/albkings"
        )
        return
    
    # The command format is: /share BUTTON_TEXT URL
    button_text = command_parts[1]
    url = command_parts[2]
    
    # Validate URL (basic check)
    if not url.startswith(('http://', 'https://', 't.me/')):
        bot.reply_to(message,
            "Ju lutem jepni një URL të vlefshme që fillon me http://, https://, ose t.me/"
        )
        return
    
    # Create share button
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton(text=button_text, url=url))
    
    # Get all users
    users = db.get_all_users()
    
    # Send confirmation
    bot.send_message(
        message.chat.id,
        f"🔗 Duke dërguar butonin e ndarjes tek {len(users)} përdorues...",
        reply_markup=keyboard  # Show the admin what the button looks like
    )
    
    # Send to all users
    successful_sends = 0
    failed_sends = 0
    
    for user_id in users:
        try:
            bot.send_message(
                chat_id=user_id,
                text="🔗 <b>Ndarë nga Administratori:</b>",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            successful_sends += 1
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {e}")
            failed_sends += 1
    
    # Send summary
    bot.send_message(
        message.chat.id,
        f"🔗 Ndarja u kompletua!\n"
        f"✅ Dërguar me sukses: {successful_sends}\n"
        f"❌ Dështuar: {failed_sends}"
    )

# Welcome new members and auto-accept
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_members(message):
    """Welcome new members and send private message"""
    for new_member in message.new_chat_members:
        if not new_member.is_bot:
            # Add user to database
            db.add_user(
                user_id=new_member.id,
                username=new_member.username,
                first_name=new_member.first_name,
                last_name=new_member.last_name
            )
            
            # Try to send welcome message to the user privately
            try:
                bot.send_message(
                    chat_id=new_member.id,
                    text=f"👋 {WELCOME_MESSAGE}"
                )
                logger.info(f"Welcome message sent to user {new_member.id}")
            except Exception as e:
                logger.error(f"Failed to send welcome message to user {new_member.id}: {e}")

# Main function
def main():
    """Start the bot."""
    logger.info("Starting AlbkingsBot...")
    
    # Start polling
    try:
        logger.info("Bot is polling for updates...")
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"Error in bot polling: {e}")

if __name__ == '__main__':
    main()
