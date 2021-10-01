from dotenv import load_dotenv
from datetime import date
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import os
import logging
import re
from functools import  reduce

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

"""
Simple Bot to reply to Telegram messages.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

expenses = []
categories = ['FOOD', 'SHOPPING', 'TRANSPORTATION', 'ENTERTAINMENT', 'SPORT']


def add_expense(amount, category, date):
    expenses.append({'amount': amount, 'category': category, 'date': date})
    return expenses


def get_expenses():
    result = ""
    for cat in categories:
        spending = sum(expense['amount'] for expense in expenses if expense['category'] == cat)
        if spending == int(spending):
            spending = int(spending)
        if spending > 0:
            result += f"You've spent ${spending} on {cat.title()}\n"
    return result

# Define a few command handlers. These usually take the two arguments update and
# context.


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def show_expenses(update: Update, context: CallbackContext) -> None:
    all_expenses = get_expenses()
    if not all_expenses:
        update.message.reply_text("You haven't spent anything yet this month!")
    else:
        update.message.reply_text(all_expenses)


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    message = update.message.text
    nums = [float(n) for n in re.findall('\d*\.?\d+', message)]
    cat = [s.upper() for s in message.split() if s.upper() in categories]
    if nums and cat:
        add_expense(nums[0], cat[0], date.today())
        if nums[0] == int(nums[0]):
            nums[0] = int(nums[0])
        update.message.reply_text(f"Got it, you spent ${nums[0]} on {cat[0].lower()}")
    else:
        update.message.reply_text("Sorry, I didn't quite get that. Can you try again?")

def main() -> None:
    """Start the bot."""
    # add_expense(100, 'FOOD', date.today())
    # add_expense(20, 'FOOD', date.today())
    # add_expense(15, 'SHOPPING', date.today())
    # add_expense(29.4, 'SHOPPING', date.today())
    # print(get_expenses())
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("show", show_expenses))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()