import telebot
import logging
import os
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from environment variables
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

# Admin ID
ADMIN_ID = 7151308102

# Welcome message
WELCOME_MESSAGE = "Mirë se vjen në Albkings të grupi top1 në shqiptari per gjdo ndihm shkruni ketu"

# Create bot instance
bot = telebot.TeleBot(TOKEN)

# Simple function to check if user is admin
def is_admin(user_id):
    return user_id == ADMIN_ID

# Handle join requests - this is the critical part
@bot.chat_join_request_handler()
def handle_join_request(request):
    """Handle chat join requests by auto-approving them"""
    try:
        # Print the entire request object to see its structure
        logger.info(f"Join request object attributes: {dir(request)}")
        
        # Get info about the request (adjusted for the correct attributes)
        chat_id = request.chat.id
        user_id = request.from_user.id  # Changed from request.user.id
        user_name = request.from_user.first_name  # Changed from request.user.first_name
        chat_name = request.chat.title
        
        logger.info(f"Received join request from {user_name} (ID: {user_id}) for group {chat_name}")
        
        # Auto-approve
        bot.approve_chat_join_request(chat_id, user_id)
        logger.info(f"Approved join request from {user_name} (ID: {user_id}) for group {chat_name}")
        
        # Try to send welcome message to user - but this might fail if user hasn't started the bot
        try:
            bot.send_message(
                chat_id=user_id,
                text=WELCOME_MESSAGE
            )
            logger.info(f"Sent welcome message to user {user_id}")
        except Exception as e:
            # This is normal - Telegram doesn't allow bots to message users who haven't messaged them first
            logger.info(f"Note: Could not send direct message to user {user_id}: {e}")
            
            # Instead, try to send a welcome message to the group mentioning the user
            try:
                # Create a welcome message that mentions the user by their name
                group_welcome = f"Mirë se erdhe në grupin tonë, {user_name}! 👋\n\n" \
                               f"Për të marrë mesazhe private dhe njoftime nga boti, " \
                               f"të lutem nis një mesazh në @AlbkingsBot"
                
                # Send the message to the group (this will work only if the bot has permission to speak in the group)
                bot.send_message(
                    chat_id=chat_id,
                    text=group_welcome
                )
                logger.info(f"Sent welcome message to group for user {user_id}")
            except Exception as group_msg_error:
                logger.error(f"Failed to send group welcome message: {group_msg_error}")
        
        # Notify admin
        try:
            admin_message = (
                f"✅ <b>U pranua një kërkesë e re për anëtarësim:</b>\n\n"
                f"👤 <b>Përdoruesi:</b> {user_name}\n"
                f"🆔 <b>ID:</b> {user_id}\n"
                f"👥 <b>Grupi:</b> {chat_name}\n"
            )
            bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_message,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
            
    except Exception as e:
        logger.error(f"Error handling join request: {e}")
        
        # Try to get basic information from the request for error reporting
        try:
            request_info = {
                'chat_id': getattr(request.chat, 'id', 'Unknown'),
                'user_id': getattr(request.from_user, 'id', 'Unknown'),
                'user_name': getattr(request.from_user, 'first_name', 'Unknown'),
                'chat_name': getattr(request.chat, 'title', 'Unknown')
            }
        except:
            request_info = {
                'chat_id': 'Unknown',
                'user_id': 'Unknown',
                'user_name': 'Unknown',
                'chat_name': 'Unknown'
            }
        
        # Notify admin about the failure with available information
        try:
            admin_message = (
                f"❌ <b>Gabim në pranimin e kërkesës për anëtarësim:</b>\n\n"
                f"👤 <b>Përdoruesi:</b> {request_info['user_name']}\n"
                f"🆔 <b>ID:</b> {request_info['user_id']}\n"
                f"👥 <b>Grupi:</b> {request_info['chat_name']}\n"
                f"🆔 <b>ID e Grupit:</b> {request_info['chat_id']}\n\n"
                f"⚠️ <b>Gabimi:</b> {str(e)}"
            )
            bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_message,
                parse_mode='HTML'
            )
        except Exception as ex:
            logger.error(f"Failed to notify admin about error: {ex}")

# Command handler for /accept
@bot.message_handler(commands=['accept'])
def handle_accept_command(message):
    """Handle the /accept command to manually approve join requests"""
    user_id = message.from_user.id
    
    # Only allow admin to use this command
    if not is_admin(user_id):
        bot.reply_to(message, "⛔ Ju nuk jeni të autorizuar për të përdorur këtë komandë.")
        return
    
    # Parse command arguments
    command_parts = message.text.split()
    
    if len(command_parts) > 1:
        try:
            # Try to get chat ID
            chat_id = int(command_parts[1])
            
            # Try to get chat info
            try:
                chat = bot.get_chat(chat_id)
                chat_name = chat.title
                
                # Check if the bot is admin in the chat
                bot_member = bot.get_chat_member(chat_id, bot.get_me().id)
                is_admin_in_chat = bot_member.status in ['administrator', 'creator']
                
                if not is_admin_in_chat:
                    bot.reply_to(message, f"⚠️ Vërejtje: Boti nuk është admin në grupin {chat_name}. Kjo mund të kufizojë funksionalitetin.")
                
                # Try to approve pending requests
                # Since pyTelegramBotAPI doesn't provide a direct method to get pending requests,
                # we can only inform the admin that the bot is configured correctly
                bot.reply_to(message, 
                    f"✅ Boti është konfiguruar për të pranuar automatikisht kërkesat e reja në grupin {chat_name}.\n\n"
                    f"Nëse kërkesat nuk po pranohen automatikisht, ju lutem kontrolloni që boti të ketë privilegjet e duhura në grup:\n"
                    f"- Duhet të jetë admin\n"
                    f"- Duhet të ketë të drejtën 'Add Members'"
                )
                
            except Exception as e:
                logger.error(f"Error getting chat info: {e}")
                bot.reply_to(message, f"❌ Nuk mund të gjej informacion për grupin: {str(e)}")
                
        except ValueError:
            bot.reply_to(message, "❌ ID e grupit duhet të jetë një numër. Përdorimi korrekt: /accept ID_GRUPIT")
            
        except Exception as e:
            logger.error(f"Error handling accept command: {e}")
            bot.reply_to(message, f"❌ Ndodhi një gabim: {str(e)}")
    else:
        bot.reply_to(message, 
            "Përdorimi korrekt: /accept ID_GRUPIT\n\n"
            "Shembull: /accept -1001234567890"
        )

# Start the bot
if __name__ == "__main__":
    logger.info("Starting bot...")
    bot.infinity_polling(allowed_updates=telebot.util.update_types)
