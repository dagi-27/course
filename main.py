import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler
)

# ===== CONFIGURATION =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.getenv('7541911520:AAGIQ0QE1XFgnv05d0IdK640E68fuQy5ZPM')
CHANNEL_ID = os.getenv('2098341933')
GROUP_ID = os.getenv('2028960321')

# Conversation states
SEARCHING = 1

# Emoji collections
WELCOME_EMOJIS = "🎓📚🔥🚀💡"
FILE_TYPE_EMOJIS = {
    'pdf': '📄',
    'image': '🖼️',
    'exam': '📝'
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Attractive welcome message with user's name"""
    user = update.effective_user
    welcome_message = (
        f"{WELCOME_EMOJIS}\n\n"
        f"🌟 Welcome {user.first_name}! 🌟\n\n"
        "📢 *Welcome to JUCS Course Archive Bot!*\n\n"
        "Your one-stop solution for:\n"
        f"{FILE_TYPE_EMOJIS['pdf']} Lecture PDFs\n"
        f"{FILE_TYPE_EMOJIS['image']} Study Images\n"
        f"{FILE_TYPE_EMOJIS['exam']} Exam Collections\n\n"
        "✨ *Getting Started:*\n"
        "1. Use commands below to search\n"
        "2. Type at least 3 characters\n"
        "3. Get instant results!\n\n"
        "🔍 *Quick Commands:*\n"
        "/pdf - Search lecture PDFs\n"
        "/image - Find study images\n"
        "/exam - Get exam papers\n"
        "/help - Show help guide\n"
        "/about - About this bot"
    )
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌟 Start Searching Now 🌟", callback_data='search')]
        ])
    )

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PDF search command"""
    context.user_data['search_type'] = 'pdf'
    await update.message.reply_text(
        f"{FILE_TYPE_EMOJIS['pdf']} Enter PDF search terms:\n"
        "Example: 'CS101 Module3'"
    )
    return SEARCHING

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image search command"""
    context.user_data['search_type'] = 'image'
    await update.message.reply_text(
        f"{FILE_TYPE_EMOJIS['image']} Enter image search terms:\n"
        "Example: 'Network Diagram'"
    )
    return SEARCHING

async def handle_exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle exam search command"""
    context.user_data['search_type'] = 'exam'
    await update.message.reply_text(
        f"{FILE_TYPE_EMOJIS['exam']} Enter exam search terms:\n"
        "Example: '2023 Midterm'"
    )
    return SEARCHING

async def perform_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the search operation"""
    search_type = context.user_data.get('search_type', 'all')
    query = update.message.text.strip().lower()
    
    if len(query) < 3:
        await update.message.reply_text("🔍 Please enter at least 3 characters")
        return ConversationHandler.END
    
    results = [
        f for f in context.bot_data.get('materials', [])
        if (search_type == 'all' or f['type'] == search_type) and
        query in f['caption']
    ][:10]
    
    if not results:
        await update.message.reply_text(
            f"❌ No {search_type} results found for '{query}'\n"
            "Try different keywords or check spelling!"
        )
        return ConversationHandler.END
    
    # Send results with progress indicator
    progress_msg = await update.message.reply_text(f"🚀 Found {len(results)} items...")
    
    for idx, item in enumerate(results, 1):
        try:
            caption = f"{idx}. {item['caption'].capitalize()}\n⭐ {search_type.upper()} RESOURCE"
            if item['type'] == 'pdf':
                await context.bot.send_document(
                    chat_id=update.message.chat_id,
                    document=item['id'],
                    caption=caption
                )
            else:
                await context.bot.send_photo(
                    chat_id=update.message.chat_id,
                    photo=item['id'],
                    caption=caption
                )
        except Exception as e:
            logging.error(f"Error sending file: {e}")
    
    await progress_msg.edit_text(
        f"✅ Search complete!\n"
        f"Found {len(results)} {search_type} resources for '{query}'"
    )
    return ConversationHandler.END

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """About command handler"""
    await update.message.reply_text(
        "📚 *JUCS Course Archive Bot*\n\n"
        "Version: 2.0\n"
        "Created for Jimma University CS Students\n\n"
        "🌟 Features:\n"
        "- Instant resource access\n"
        "- Smart search technology\n"
        "- Always free to use\n\n"
        "Maintained by [Your Name/Team]",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler"""
    await update.message.reply_text(
        "🆘 *Help Guide*\n\n"
        "🔍 *Search Commands:*\n"
        "/pdf - Find lecture notes\n"
        "/image - Search diagrams\n"
        "/exam - Get past papers\n\n"
        "📌 *Tips:*\n"
        "- Use specific keywords\n"
        "- Combine terms (e.g. 'cs101 exam')\n"
        "- Minimum 3 characters\n\n"
        "❓ Contact @username for support",
        parse_mode='Markdown'
    )

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add content handler
    application.add_handler(MessageHandler(
        filters.Chat([CHANNEL_ID, GROUP_ID]) &
        (filters.Document.PDF | filters.PHOTO),
        lambda update, ctx: handle_channel_content(update, ctx)
    ))
    
    # Conversation handlers for searches
    search_handler = ConversationHandler(
        entry_points=[
            CommandHandler('pdf', handle_pdf),
            CommandHandler('image', handle_image),
            CommandHandler('exam', handle_exam)
        ],
        states={
            SEARCHING: [MessageHandler(filters.TEXT & ~filters.COMMAND, perform_search)]
        },
        fallbacks=[]
    )
    
    # Core commands
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('about', about))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(search_handler)
    
    application.run_polling()

# (Keep the handle_channel_content and other utility functions from previous version)

"""
===== ENHANCED FEATURES =====
1. Personalized welcome message with user's name
2. Dedicated commands:
   - /pdf - Search lecture materials
   - /image - Find diagrams/charts
   - /exam - Get exam papers
3. Rich visual feedback with emojis
4. Progress indicators during search
5. Detailed help and about sections
6. Error-resistant search operations

===== USAGE EXAMPLE =====
User: /exam
Bot: "📝 Enter exam search terms:"
User: "2023 final"
Bot: Shows matching exam papers with numbers and captions
"""