import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


async def start(update, context):
    await update.message.reply_text('Welcome to ClalitBot!')


async def help(update, context):
    await update.message.reply_text('work in progress...')


async def hello(update: Update, context) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')


async def schedule(update: Update, context) -> None:
    # do post request to clalit server
    chat_id = update.message.chat_id
    print(chat_id)
    await update.message.reply_text(f'wip')


with open("/etc/clalit_config.json") as config_file:
    config = json.load(config_file)
    token = config.get('TELEGRAM_TOKEN', None)
    assert token, 'Bot token not found'

app = ApplicationBuilder().token(token).build()

app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))
app.add_handler(CommandHandler("schedule", schedule))

app.run_polling()
