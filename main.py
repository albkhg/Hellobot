"""
Albkings Telegram Bot
--------------------
A Telegram bot that automatically accepts new members, sends welcome messages,
and provides admin broadcast and statistics functionality.
"""
import logging
import os
import json
from typing import Dict, Any, Optional, List, Set
import time
from datetime import datetime
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Chat
from dotenv import load_dotenv

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
if not TELEGRAM_BOT_TOKEN:
    logger.error("Telegram bot token not found in environment variables!")
    raise ValueError("No Telegram Bot token provided. Set the TELEGRAM_BOT_TOKEN environment variable.")

ADMIN_ID = 7151308102  # Admin user ID
WELCOME_MESSAGE = "Mirë se vjen në Albkings të grupi top1 në shqiptari per gjdo ndihm shkruni ketu"
DATABASE_FILE = "users_database.json"
BANNED_USERS_FILE = "banned_users.json"
GROUPS_FILE = "group_statistics.json"

# Initialize the bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Function to check if user is admin
def check_admin(user_id: int) -> bool:
    """Check if a user is an admin"""
    return user_id == ADMIN_ID

# Database management
class GroupDatabase:
    """Database for managing group statistics"""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.groups = {}
        self.load_data()
    
    def load_data(self) -> None:
        """Load group data from file if it exists"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.groups = json.load(f)
                logger.info(f"Loaded {len(self.groups)} groups from database")
            else:
                logger.info("No group database file found, starting with empty database")
        except Exception as e:
            logger.error(f"Error loading group database: {e}")
            self.groups = {}
    
    def save_data(self) -> None:
        """Save group data to file"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.groups, f, ensure_ascii=False, indent=4)
            logger.info(f"Saved {len(self.groups)} groups to database")
        except Exception as e:
            logger.error(f"Error saving group database: {e}")
    
    def update_group(self, group_id: int, name: str, member_count: int, is_admin: bool = True) -> None:
        """Add or update a group in the database"""
        group_id_str = str(group_id)
        
        # Check if this is a new group
        is_new = group_id_str not in self.groups
        
        # Current time for last update
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        if is_new:
            # Create new group entry
            self.groups[group_id_str] = {
                'name': name,
                'member_count': member_count,
                'is_admin': is_admin,
                'join_date': current_time,
                'last_update': current_time,
                'messages_count': 0
            }
            logger.info(f"Added new group: {name} (ID: {group_id})")
        else:
            # Update existing group
            self.groups[group_id_str].update({
                'name': name,
                'member_count': member_count,
                'is_admin': is_admin,
                'last_update': current_time
            })
            logger.info(f"Updated group: {name} (ID: {group_id})")
        
        self.save_data()
    
    def increment_message_count(self, group_id: int) -> None:
        """Increment the message count for a group"""
        group_id_str = str(group_id)
        if group_id_str in self.groups:
            self.groups[group_id_str]['messages_count'] = self.groups[group_id_str].get('messages_count', 0) + 1
            self.save_data()
    
    def get_admin_groups(self) -> List[Dict[str, Any]]:
        """Get all groups where bot is admin"""
        admin_groups = []
        for group_id, group_data in self.groups.items():
            if group_data.get('is_admin', False):
                group_info = group_data.copy()
                group_info['id'] = int(group_id)
                admin_groups.append(group_info)
        
        # Sort by member count (largest first)
        return sorted(admin_groups, key=lambda x: x.get('member_count', 0), reverse=True)
    
    def get_all_groups(self) -> Dict[int, Dict[str, Any]]:
        """Get all groups"""
        return {int(k): v for k, v in self.groups.items()}

class UserDatabase:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.banned_file = BANNED_USERS_FILE
        self.users = {}
        self.banned_users = set()
        self.load_database()
        self.load_banned_users()
    
    def load_database(self):
        """Load user data from file if it exists"""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
                logger.info(f"Loaded database with {len(self.users)} users")
            else:
                logger.info("No database file found, starting with empty database")
        except Exception as e:
            logger.error(f"Error loading database: {e}")
    
    def load_banned_users(self):
        """Load banned users list from file if it exists"""
        try:
            if os.path.exists(self.banned_file):
                with open(self.banned_file, 'r', encoding='utf-8') as f:
                    banned_data = json.load(f)
                    self.banned_users = set(banned_data.get("banned_users", []))
                logger.info(f"Loaded {len(self.banned_users)} banned users")
            else:
                logger.info("No banned users file found, starting with empty banned list")
        except Exception as e:
            logger.error(f"Error loading banned users: {e}")
            self.banned_users = set()
    
    def save_database(self):
        """Save user data to file"""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=4)
            logger.info(f"Saved database with {len(self.users)} users")
        except Exception as e:
            logger.error(f"Error saving database: {e}")
    
    def save_banned_users(self):
        """Save banned users list to file"""
        try:
            with open(self.banned_file, 'w', encoding='utf-8') as f:
                banned_data = {"banned_users": list(self.banned_users)}
                json.dump(banned_data, f, ensure_ascii=False, indent=4)
            logger.info(f"Saved {len(self.banned_users)} banned users")
        except Exception as e:
            logger.error(f"Error saving banned users: {e}")
    
    def add_user(self, user_id: int, username: Optional[str], first_name: str, last_name: Optional[str] = None):
        """Add or update a user in the database"""
        user_id_str = str(user_id)  # Convert to string for JSON keys
        
        # Check if this is a new user
        is_new = user_id_str not in self.users
        
        # Current time for join date
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Update user data
        self.users[user_id_str] = {
            'username': username if username else 'None',
            'first_name': first_name,
            'last_name': last_name if last_name else 'None',
            'join_date': current_time if is_new else self.users.get(user_id_str, {}).get('join_date', current_time)
        }
        
        # Save changes
        self.save_database()
        
        if is_new:
            logger.info(f"Added new user: {first_name} (ID: {user_id})")
        else:
            logger.info(f"Updated existing user: {first_name} (ID: {user_id})")
    
    def get_all_users(self):
        """Get all users from the database"""
        return {int(k): v for k, v in self.users.items()}
    
    def get_user_name(self, user_id: int) -> str:
        """Get user's full name"""
        user_id_str = str(user_id)
        if user_id_str in self.users:
            first_name = self.users[user_id_str].get('first_name', '')
            last_name = self.users[user_id_str].get('last_name', '')
            if last_name and last_name != 'None':
                return f"{first_name} {last_name}"
            return first_name
        return "Unknown User"
    
    def ban_user(self, user_id: int) -> bool:
        """Ban a user by adding them to the banned list"""
        if str(user_id) not in self.users or user_id == ADMIN_ID:
            return False  # Can't ban users not in database or admin
        
        self.banned_users.add(user_id)
        self.save_banned_users()
        logger.info(f"User {user_id} has been banned")
        return True
    
    def is_banned(self, user_id: int) -> bool:
        """Check if a user is banned"""
        return user_id in self.banned_users
    
    def get_statistics(self):
        """Get user statistics"""
        return {
            'total_users': len(self.users),
            'banned_users': len(self.banned_users),
            'users': self.users
        }

# Initialize databases
db = UserDatabase(DATABASE_FILE)
group_db = GroupDatabase(GROUPS_FILE)

# Command handlers
@bot.message_handler(commands=['start'])
def handle_start(message):
    """Handle /start command"""
    user = message.from_user
    
    # Add user to database
    db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Send welcome message
    bot.reply_to(message, 
        f"👋 Përshëndetje, {user.first_name}!\n\n"
        f"Unë jam Albkings Bot. Unë ndihmoj në menaxhimin e grupit dhe sigurim të funksionaliteteve të dobishme."
    )

@bot.message_handler(commands=['help'])
def handle_help(message):
    """Handle /help command"""
    user_id = message.from_user.id
    
    # Different help text for admin and regular users
    if is_admin(user_id):
        help_text = (
            "🤖 <b>Albkings Bot Komandat</b>\n\n"
            "<b>Komandat e Përdoruesit:</b>\n"
            "/start - Fillo bot-in\n"
            "/help - Shfaq këtë mesazh ndihme\n\n"
            "<b>Komandat e Administratorit:</b>\n"
            "/broadcast - Dërgo një mesazh të gjithë përdoruesve\n"
            "/statistics - Shiko statistikat e përdoruesve\n"
            "/grupistatistikat - Shiko statistikat e grupeve ku jam admin\n"
            "/share - Ndaj një lidhje me të gjithë përdoruesit\n"
            "/ban - Bëj ban një përdorues (përdorni duke iu përgjigjur një mesazhi)\n"
        )
    else:
        help_text = (
            "🤖 <b>Albkings Bot Komandat</b>\n\n"
            "<b>Komandat e Përdoruesit:</b>\n"
            "/start - Fillo bot-in\n"
            "/help - Shfaq këtë mesazh ndihme\n\n"
            "Për ndihmë, thjesht shkruani mesazhin tuaj dhe do të përcillet tek administratori."
        )
    
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

@bot.message_handler(commands=['broadcast'])
def handle_broadcast(message):
    """Handle /broadcast command (admin only)"""
    user_id = message.from_user.id
    
    # Check if user is admin
    if not is_admin(user_id):
        bot.reply_to(message, "⛔ Ju nuk jeni të autorizuar për të përdorur këtë komandë.")
        return
    
    # Extract broadcast message
    broadcast_text = message.text.replace('/broadcast', '', 1).strip()
    
    # Check if message is empty
    if not broadcast_text:
        bot.reply_to(message, 
            "Ju lutem jepni një mesazh për të transmetuar.\n\n"
            "Shembull: /broadcast Përshëndetje të gjithëve! Ky është një njoftim i rëndësishëm."
        )
        return
    
    # Get all users
    users = db.get_all_users()
    successful = 0
    failed = 0
    
    # Send confirmation to admin
    bot.reply_to(message, f"📢 Duke filluar transmetimin tek {len(users)} përdorues...")
    
    # Send broadcast message to all users
    for user_id, user_data in users.items():
        try:
            bot.send_message(
                chat_id=user_id,
                text=f"📢 <b>Njoftim nga Administratori:</b>\n\n{broadcast_text}",
                parse_mode='HTML'
            )
            successful += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to user {user_id}: {e}")
            failed += 1
    
    # Send summary to admin
    bot.send_message(
        message.chat.id,
        f"📢 Transmetimi u kompletua!\n"
        f"✅ Dërguar me sukses: {successful}\n"
        f"❌ Dështuar: {failed}"
    )

@bot.message_handler(commands=['statistics'])
def handle_statistics(message):
    """Handle /statistics command (admin only)"""
    user_id = message.from_user.id
    
    # Check if user is admin
    if not is_admin(user_id):
        bot.reply_to(message, "⛔ Ju nuk jeni të autorizuar për të përdorur këtë komandë.")
        return
    
    # Get statistics
    stats = db.get_statistics()
    total_users = stats.get('total_users', 0)
    banned_users = stats.get('banned_users', 0)
    
    # Format statistics message
    result = f"📊 <b>Statistikat e Bot-it</b>\n\n"
    result += f"👥 <b>Përdorues Total:</b> {total_users}\n"
    result += f"🚫 <b>Përdorues të Bllokuar:</b> {banned_users}\n\n"
    
    # Add recent users if there are any
    if total_users > 0:
        result += f"<b>Përdoruesit e Fundit:</b>\n"
        
        # Get all users and sort by join date (newest first)
        users = stats.get('users', {})
        recent_users = sorted(
            users.items(), 
            key=lambda x: x[1].get('join_date', ''), 
            reverse=True
        )[:10]  # Limit to 10 most recent
        
        for i, (user_id, user_data) in enumerate(recent_users, 1):
            username = user_data.get('username', 'None')
            first_name = user_data.get('first_name', 'Unknown')
            last_name = user_data.get('last_name', '')
            join_date = user_data.get('join_date', 'Unknown')
            
            name_display = f"{first_name} {last_name}".strip()
            username_display = f"@{username}" if username and username != 'None' else "No username"
            
            result += f"{i}. <b>{name_display}</b> ({username_display})\n"
            result += f"   📅 Bashkuar më: {join_date}\n"
    
    # Send statistics message
    bot.send_message(message.chat.id, result, parse_mode='HTML')

@bot.message_handler(commands=['grupistatistikat'])
def handle_group_statistics(message):
    """Handle /grupistatistikat command (admin only)"""
    user_id = message.from_user.id
    
    # Check if user is admin
    if not is_admin(user_id):
        bot.reply_to(message, "⛔ Ju nuk jeni të autorizuar për të përdorur këtë komandë.")
        return
    
    # Get admin groups
    admin_groups = group_db.get_admin_groups()
    
    if not admin_groups:
        bot.reply_to(message, "📊 Nuk u gjet asnjë grup ku jam administrator. Më shto si admin në një grup për të parë statistikat.")
        return
    
    # Format group statistics message
    result = f"📊 <b>Statistikat e Grupeve</b>\n\n"
    result += f"👥 <b>Numri i Grupeve ku Jam Admin:</b> {len(admin_groups)}\n\n"
    
    # Add details for each group
    for i, group in enumerate(admin_groups, 1):
        group_name = group.get('name', 'Grup pa emër')
        member_count = group.get('member_count', 0)
        messages_count = group.get('messages_count', 0)
        join_date = group.get('join_date', 'E panjohur')
        last_update = group.get('last_update', 'E panjohur')
        
        result += f"{i}. <b>{group_name}</b>\n"
        result += f"   👥 Anëtarë: {member_count}\n"
        result += f"   💬 Mesazhe: {messages_count}\n"
        result += f"   📅 Boti u shtua: {join_date}\n"
        result += f"   🔄 Përditësimi i fundit: {last_update}\n\n"
    
    # Send statistics message
    bot.send_message(message.chat.id, result, parse_mode='HTML')

@bot.message_handler(commands=['share'])
def handle_share(message):
    """Handle /share command (admin only)"""
    user_id = message.from_user.id
    
    # Check if user is admin
    if not is_admin(user_id):
        bot.reply_to(message, "⛔ Ju nuk jeni të autorizuar për të përdorur këtë komandë.")
        return
    
    # Parse command arguments
    command_parts = message.text.split(' ', 2)
    
    # Check if we have enough arguments
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
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text=button_text, url=url))
    
    # Get all users
    users = db.get_all_users()
    
    # Send confirmation to admin
    bot.send_message(
        message.chat.id,
        f"🔗 Duke dërguar butonin e ndarjes tek {len(users)} përdorues...",
        reply_markup=keyboard  # Show the admin what the button looks like
    )
    
    # Send to all users
    successful = 0
    failed = 0
    
    for user_id, user_data in users.items():
        try:
            bot.send_message(
                chat_id=user_id,
                text="🔗 <b>Ndarë nga Administratori:</b>",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            successful += 1
        except Exception as e:
            logger.error(f"Failed to send share to user {user_id}: {e}")
            failed += 1
    
    # Send summary to admin
    bot.send_message(
        message.chat.id,
        f"🔗 Ndarja u kompletua!\n"
        f"✅ Dërguar me sukses: {successful}\n"
        f"❌ Dështuar: {failed}"
    )

@bot.message_handler(commands=['ban'])
def handle_ban(message):
    """Ban a user (admin only)"""
    user_id = message.from_user.id
    
    # Check if user is admin
    if not is_admin(user_id):
        bot.reply_to(message, "⛔ Ju nuk jeni të autorizuar për të përdorur këtë komandë.")
        return
    
    # Check if the command is a reply to another message
    if not message.reply_to_message:
        bot.reply_to(message, "Ju lutem përdorni këtë komandë duke iu përgjigjur një mesazhi nga përdoruesi që dëshironi të ndëshkoni.")
        return
    
    # Get the user ID to ban
    ban_user_id = message.reply_to_message.from_user.id
    
    # Check if trying to ban admin
    if is_admin(ban_user_id):
        bot.reply_to(message, "❌ Nuk mund të ndëshkoni administratorin.")
        return
    
    # Ban the user
    user_name = db.get_user_name(ban_user_id)
    
    if db.ban_user(ban_user_id):
        bot.reply_to(message, f"🚫 Përdoruesi {user_name} (ID: {ban_user_id}) u bllokua me sukses.")
        
        # Notify the banned user
        try:
            bot.send_message(
                chat_id=ban_user_id,
                text="⛔ Ju jeni bllokuar nga administratori dhe nuk mund të përdorni më botin."
            )
        except Exception as e:
            logger.error(f"Failed to notify banned user {ban_user_id}: {e}")
    else:
        bot.reply_to(message, f"❌ Nuk mund të bllokojë
