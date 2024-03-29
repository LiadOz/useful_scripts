import json
from telegram import Update
from telegram.ext import (
        ApplicationBuilder,
        CommandHandler,
        PicklePersistence
)
from telegram_utils import get_token
from clalit_utils import (
        add_job, verify_job_msg, remove_entry, server_is_up, get_previous_job
)


async def start(update, context):
    await update.message.reply_text('Welcome to ClalitBot!')
    await update.message.reply_text('Type /help to get to learn how to use me')


async def help(update, context):
    message = """/schedule {visit_json} to start looking for new visits
example command: /schedule {"clinic_id": "865179", "doctor_code": "92"}
    visit_json must contain:
        - clinic_id
        - doctor_code
    Example Codes:
        - clinic_id = "865179"
        - doctor_code = "91" dentist
        - doctor_code = "92" dental hygienist
    Only dental schedules are supported

/unschedule removes schedule request
/is_up verifies schedule server is running
/reschedule repeat last schedule command
    """
    await update.message.reply_text(message)


async def hello(update: Update, context) -> None:
    msg = f'Hello {update.effective_user.first_name}'
    await update.message.reply_text(msg)


async def is_up(update: Update, context) -> None:
    if server_is_up():
        await update.message.reply_text('Everything looks fine')
    else:
        await update.message.reply_text('Schedule server is down')


async def unschedule(update: Update, context) -> None:
    chat_id = update.message.chat_id
    remove_entry(chat_id)
    await update.message.reply_text("All entries were removed")


async def schedule(update: Update, context) -> None:
    # do post request to clalit server
    chat_id = update.message.chat_id
    client_msg = update.message.text.split(' ', 1)[1]
    try:
        message = json.loads(client_msg)
    except json.JSONDecodeError:
        await update.message.reply_text(f"Can't decode {client_msg}")
        return

    err = verify_job_msg(message)
    if err:
        await update.message.reply_text(f"Failed to schedule {err}")
        return

    err = add_job(chat_id, job_data=message)
    if err:
        await update.message.reply_text(err)
        return

    await update.message.reply_text(f"Schdule started {message}")


async def reschedule(update: Update, context) -> None:
    chat_id = update.message.chat_id
    previous_job = get_previous_job(chat_id)
    if not previous_job:
        await update.message.reply_text("Can't reschedule no previous job found")
        return

    add_job(chat_id, job_data=previous_job)
    await update.message.reply_text("Rescheduled with previous job")


persistance = PicklePersistence('telegram_persistance_file')
app = ApplicationBuilder() \
        .token(get_token()) \
        .persistence(persistence=persistance) \
        .build()

app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))
app.add_handler(CommandHandler("is_up", is_up))
app.add_handler(CommandHandler("schedule", schedule))
app.add_handler(CommandHandler("reschedule", reschedule))
app.add_handler(CommandHandler("unschedule", unschedule))

app.run_polling()
