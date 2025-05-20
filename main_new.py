import logging
import os
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import configurations
from config import TELEGRAM_BOT_TOKEN, ADMIN_ID, WELCOME_MESSAGE
from database import db

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Helper function to check if user is admin
def is_admin(user_id: int) -> bool:
    """Check if a user is an admin"""
    return user_id == ADMIN_ID

# Command handlers
def start(update: Update, context: CallbackContext) -> None:
    """Handler for the /start command"""
    user = update.effective_user
    
    # Add the user to the database
    db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    update.message.reply_html(
        f"👋 Përshëndetje, {user.first_name}!\n\n"
        f"Unë jam Albkings Bot. Unë ndihmoj në menaxhimin e grupit dhe sigurim të funksionaliteteve të dobishme."
    )

def help_command(update: Update, context: CallbackContext) -> None:
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
    update.message.reply_html(help_text)

# Admin commands
def broadcast(update: Update, context: CallbackContext) -> None:
    """Handler for the /broadcast command - Admin only"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        update.message.reply_text("⛔ Ju nuk jeni të autorizuar për të përdorur këtë komandë.")
        return
        
    message_text = update.message.text.replace('/broadcast', '', 1).strip()
    
    if not message_text:
        update.message.reply_text(
            "Ju lutem jepni një mesazh për të transmetuar.\n\n"
            "Shembull: /broadcast Përshëndetje të gjithëve! Ky është një njoftim i rëndësishëm."
        )
        return
    
    # Get all users
    users = db.get_all_users()
    successful_sends = 0
    failed_sends = 0
    
    # Send a confirmation message first
    update.message.reply_text(f"📢 Duke filluar transmetimin tek {len(users)} përdorues...")
    
    # Broadcast the message to all users
    for user_id in users:
        try:
            context.bot.send_message(
                chat_id=user_id,
                text=f"📢 <b>Njoftim nga Administratori:</b>\n\n{message_text}",
                parse_mode='HTML'
            )
            successful_sends += 1
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {e}")
            failed_sends += 1
    
    # Send summary
    update.message.reply_text(
        f"📢 Transmetimi u kompletua!\n"
        f"✅ Dërguar me sukses: {successful_sends}\n"
        f"❌ Dështuar: {failed_sends}"
    )

def statistics(update: Update, context: CallbackContext) -> None:
    """Handler for the /statistics command - Admin only"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        update.message.reply_text("⛔ Ju nuk jeni të autorizuar për të përdorur këtë komandë.")
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
    
    update.message.reply_html(result)

def share_command(update: Update, context: CallbackContext) -> None:
    """Handler for the /share command - Admin only"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        update.message.reply_text("⛔ Ju nuk jeni të autorizuar për të përdorur këtë komandë.")
        return
        
    args = context.args
    
    # Check if we have enough arguments
    if not args or len(args) < 2:
        update.message.reply_text(
            "Ju lutem jepni tekstin e butonit dhe URL-në.\n\n"
            "Shembull: /share 'Bashkohu në Kanalin Tonë' https://t.me/albkings"
        )
        return
    
    # The first argument is the button text, and the rest is the URL
    button_text = args[0]
    url = args[1]
    
    # Validate URL (basic check)
    if not url.startswith(('http://', 'https://', 't.me/')):
        update.message.reply_text(
            "Ju lutem jepni një URL të vlefshme që fillon me http://, https://, ose t.me/"
        )
        return
    
    # Create share button
    keyboard = [[InlineKeyboardButton(button_text, url=url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Get all users
    users = db.get_all_users()
    
    # Send confirmation
    update.message.reply_text(
        f"🔗 Duke dërguar butonin e ndarjes tek {len(users)} përdorues...",
        reply_markup=reply_markup  # Show the admin what the button looks like
    )
    
    # Send to all users
    successful_sends = 0
    failed_sends = 0
    
    for user_id in users:
        try:
            context.bot.send_message(
                chat_id=user_id,
                text="🔗 <b>Ndarë nga Administratori:</b>",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            successful_sends += 1
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {e}")
            failed_sends += 1
    
    # Send summary
    update.message.reply_text(
        f"🔗 Ndarja u kompletua!\n"
        f"✅ Dërguar me sukses: {successful_sends}\n"
        f"❌ Dështuar: {failed_sends}"
    )

def welcome_new_member(update: Update, context: CallbackContext) -> None:
    """Welcome new members and send private message"""
    for new_member in update.message.new_chat_members:
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
                context.bot.send_message(
                    chat_id=new_member.id,
                    text=f"👋 {WELCOME_MESSAGE}"
                )
                logger.info(f"Welcome message sent to user {new_member.id}")
            except Exception as e:
                logger.error(f"Failed to send welcome message to user {new_member.id}: {e}")

def error_handler(update: Update, context: CallbackContext) -> None:
    """Log errors caused by updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    # If we can, inform the user there was a problem
    if update and update.effective_message:
        update.effective_message.reply_text(
            "Na vjen keq, ndodhi një gabim gjatë përpunimit të kërkesës suaj."
        )

def main() -> None:
    """Start the bot."""
    logger.info("Starting AlbkingsBot...")
    
    # Create the Updater and pass it the bot's token
    updater = Updater(TELEGRAM_BOT_TOKEN)
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("broadcast", broadcast))
    dispatcher.add_handler(CommandHandler("statistics", statistics))
    dispatcher.add_handler(CommandHandler("share", share_command, pass_args=True))
    
    # Register chat member handler for auto-accepting members and sending welcome messages
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome_new_member))
    
    # Register error handler
    dispatcher.add_error_handler(error_handler)
    
    # Start the Bot
    logger.info("Bot is starting up...")
    updater.start_polling()
    
    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
