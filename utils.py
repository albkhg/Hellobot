import logging
from typing import Dict, List, Any, Callable, Optional, Union
from telegram import Update, User, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from config import ADMIN_ID

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    """Check if a user is an admin"""
    return user_id == ADMIN_ID

def admin_required(func: Callable) -> Callable:
    """Decorator to restrict commands to admin only"""
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        if not is_admin(user_id):
            logger.warning(f"Unauthorized access attempt by user {user_id}")
            update.message.reply_text("⛔ You are not authorized to use this command.")
            return
        return func(update, context, *args, **kwargs)
    return wrapper

def extract_user_data(user: User) -> Dict[str, Any]:
    """Extract relevant user data from a Telegram User object"""
    return {
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name
    }

def create_share_button(text: str, url: str) -> InlineKeyboardMarkup:
    """Create a share button with the given text and URL"""
    keyboard = [
        [InlineKeyboardButton(text, url=url)]
    ]
    return InlineKeyboardMarkup(keyboard)

def safe_send_message(
    context: CallbackContext, 
    chat_id: int, 
    text: str, 
    reply_markup: Optional[InlineKeyboardMarkup] = None
) -> bool:
    """
    Safely send a message to a user, handling potential exceptions
    
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    try:
        context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        return True
    except Exception as e:
        logger.error(f"Error sending message to user {chat_id}: {e}")
        return False

def format_statistics(stats: Dict[str, Any]) -> str:
    """Format statistics for display"""
    total_users = stats.get('total_users', 0)
    
    # Start with the header and total count
    result = f"📊 <b>Bot Statistics</b>\n\n"
    result += f"👥 <b>Total Users:</b> {total_users}\n\n"
    
    # Add recent users if there are any
    if total_users > 0:
        result += f"<b>Recent Users:</b>\n"
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
            result += f"   📅 Joined: {join_date}\n"
    
    return result
