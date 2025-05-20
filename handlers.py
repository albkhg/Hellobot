import logging
from typing import Dict, List, Any, Optional
from telegram import Update, User, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from config import WELCOME_MESSAGE, ADMIN_ID
from database import db

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
        f"👋 Hello, {user.mention_html()}!\n\n"
        f"I am the Albkings Group Bot. I help manage the group and provide useful features."
    )

async def help_command(update: Update, context: CallbackContext) -> None:
    """Handler for the /help command"""
    help_text = (
        "🤖 <b>Albkings Bot Commands</b>\n\n"
        "<b>User Commands:</b>\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n\n"
        "<b>Admin Commands:</b>\n"
        "/broadcast - Send a message to all users\n"
        "/statistics - View user statistics\n"
        "/share - Share a link with all users\n"
    )
    await update.message.reply_html(help_text)

@admin_required
async def broadcast(update: Update, context: CallbackContext) -> None:
    """Handler for the /broadcast command - Admin only"""
    message_text = update.message.text.replace('/broadcast', '', 1).strip()
    
    if not message_text:
        await update.message.reply_text(
            "Please provide a message to broadcast.\n\n"
            "Example: /broadcast Hello everyone! This is an important announcement."
        )
        return
    
    # Get all users
    users = db.get_all_users()
    successful_sends = 0
    failed_sends = 0
    
    # Send a confirmation message first
    await update.message.reply_text(f"📢 Starting broadcast to {len(users)} users...")
    
    # Broadcast the message to all users
    for user_id in users:
        success = await safe_send_message(
            context=context, 
            chat_id=user_id, 
            text=f"📢 <b>Announcement from Admin:</b>\n\n{message_text}"
        )
        
        if success:
            successful_sends += 1
        else:
            failed_sends += 1
    
    # Send summary
    await update.message.reply_text(
        f"📢 Broadcast completed!\n"
        f"✅ Successfully sent: {successful_sends}\n"
        f"❌ Failed: {failed_sends}"
    )

@admin_required
async def statistics(update: Update, context: CallbackContext) -> None:
    """Handler for the /statistics command - Admin only"""
    stats = db.get_statistics()
    formatted_stats = format_statistics(stats)
    
    await update.message.reply_html(formatted_stats)

@admin_required
async def share_command(update: Update, context: CallbackContext) -> None:
    """Handler for the /share command - Admin only"""
    args = context.args
    
    # Check if we have enough arguments
    if len(args) < 2:
        await update.message.reply_text(
            "Please provide both button text and URL.\n\n"
            "Example: /share 'Join Our Channel' https://t.me/albkings"
        )
        return
    
    # The first argument is the button text, and everything after is the URL
    button_text = args[0]
    url = args[1]
    
    # Validate URL (basic check)
    if not url.startswith(('http://', 'https://', 't.me/')):
        await update.message.reply_text(
            "Please provide a valid URL that starts with http://, https://, or t.me/"
        )
        return
    
    # Create share button
    share_markup = create_share_button(button_text, url)
    
    # Get all users
    users = db.get_all_users()
    
    # Send confirmation
    await update.message.reply_text(
        f"🔗 Sending share button to {len(users)} users...",
        reply_markup=share_markup  # Show the admin what the button looks like
    )
    
    # Send to all users
    successful_sends = 0
    failed_sends = 0
    
    for user_id in users:
        success = await safe_send_message(
            context=context,
            chat_id=user_id,
            text="🔗 <b>Shared by Admin:</b>",
            reply_markup=share_markup
        )
        
        if success:
            successful_sends += 1
        else:
            failed_sends += 1
    
    # Send summary
    await update.message.reply_text(
        f"🔗 Share completed!\n"
        f"✅ Successfully sent: {successful_sends}\n"
        f"❌ Failed: {failed_sends}"
    )

async def chat_member_handler(update: Update, context: CallbackContext) -> None:
    """
    Handle chat member updates (joining, leaving, etc.)
    This is used to automatically accept new members
    """
    chat_member_update: ChatMemberUpdated = update.chat_member
    
    # Extract the chat and user information
    chat: Chat = chat_member_update.chat
    user = chat_member_update.new_chat_member.user
    
    # Get the status change
    old_status = chat_member_update.old_chat_member.status
    new_status = chat_member_update.new_chat_member.status
    
    # Log the status change
    logger.info(
        f"User {user.id} ({user.first_name}) status changed from {old_status} to {new_status} in chat {chat.id}"
    )
    
    # If a user requested to join the group (pending)
    if old_status == ChatMember.BANNED and new_status == ChatMember.MEMBER:
        # The user has been accepted (likely by bot in auto-accept mode)
        logger.info(f"User {user.id} ({user.first_name}) was accepted to the group {chat.id}")
        
        # Add user to database
        db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Try to send welcome message to the user privately
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=f"👋 {WELCOME_MESSAGE}"
            )
            logger.info(f"Welcome message sent to user {user.id}")
        except Exception as e:
            logger.error(f"Failed to send welcome message to user {user.id}: {e}")
    
    elif new_status == "member" and old_status != "member":
        # New member joined directly (no approval needed)
        logger.info(f"User {user.id} ({user.first_name}) joined the group {chat.id}")
        
        # Add user to database
        db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Try to send welcome message to the user privately
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=f"👋 {WELCOME_MESSAGE}"
            )
            logger.info(f"Welcome message sent to user {user.id}")
        except Exception as e:
            logger.error(f"Failed to send welcome message to user {user.id}: {e}")

async def error_handler(update: Update, context: CallbackContext) -> None:
    """Log errors caused by updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    # If we can, inform the user there was a problem
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, an error occurred while processing your request."
        )
