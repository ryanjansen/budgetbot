from dotenv import load_dotenv
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, \
    ConversationHandler
import os
import logging
import re
import db

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

categories = ['FOOD', 'SHOPPING', 'TRANSPORTATION', 'ENTERTAINMENT', 'SPORT', 'MISC']
category_alias = {'f': 'FOOD', 'sh': 'SHOPPING', 't': 'TRANSPORTATION', 'e': 'ENTERTAINMENT', 'sp': 'SPORT',
                  'm': 'MISC'}

db = db.Database("budget_bot", "ryan")

number_keyboard = ReplyKeyboardMarkup([
    ['1', '2', '3', 'f'],
    ['4', '5', '6', 'sh'],
    ['7', '8', '9', 'e'],
    ['0', 'sp', 't', 'm']
])

REPEAT = 1

def print_expenses(expenses):
    result = ""
    total = 0
    for cat in categories:
        spending = sum(expense[0] for expense in expenses if expense[2] == cat)
        if spending > 0:
            rounded_spending = round(spending, 1)
            result += f"You've spent ${rounded_spending} on {cat.title()}\n"
            total += spending
    rounded_total = round(total, 1)
    result += f"this month ({date.today().strftime('%B')})\n"
    result += f'TOTAL: ${rounded_total}'
    return result


def get_user_id(chat_id):
    user_id = db.get_user(chat_id)
    if not user_id:
        return False
    else:
        return user_id[0][0]


def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if not get_user_id(chat_id):
        db.add_user(update.effective_user.name, chat_id)

    message = """
              Hi!, I'm Budget Bot, your friendly neighbourhood spending tracker. Here's how I work:
              Option 1: Enter a number and choose a category of spending
              Option 2: Enter a number and category
              Option 3: Enter a number and a shorthand category
              There are six categories: food, shopping, transportation, entertainment, sport and misc.
              Their shorthand forms are: f, sh, t, e, sp and m respectively.
              So to add $10 to food, just type '10 f'

              To see your spending for the month, use the /show command
              That's all! Remember that you can use /help to see this message again! 
            """

    update.message.reply_text(message)


def help_command(update: Update, context: CallbackContext) -> None:
    message = """Hi!, I'm Budget Bot, your friendly neighbourhood spending tracker. Here's how I work:\n  
              Option 1: Enter a number and choose a category of spending\n
              Option 2: Enter a number and category\n
              Option 3: Enter a number and a shorthand category\n
              There are six categories: food, shopping, transportation, entertainment, sport and misc.\n
              Their shorthand forms are: f, sh, t, e, sp and m respectively.\n
              So to add $10 to food, just type '10 f'\n
              
              To see your spending for the month, use the /show command\n
              That's all! Remember that you can use /help to see this message again! 
            """
    update.message.reply_text(message)


def show_expenses(update: Update, context: CallbackContext) -> None:
    user_id = get_user_id(update.message.chat_id)
    all_expenses = db.get_expenses(user_id, date.today())
    if not all_expenses:
        update.message.reply_text("You haven't spent anything yet this month!")
    else:
        update.message.reply_text(print_expenses(all_expenses))


def add_expense_from_message(update: Update, context: CallbackContext) -> None:
    message = update.message.text
    nums = [float(n) for n in re.findall('\d*\.?\d+', message)]
    cat = ""
    for s in message.split():
        if s in category_alias:
            cat = category_alias[s]
            break
        elif s.upper() in categories:
            cat = s.upper()
            break
    if nums and cat:
        user_id = get_user_id(update.message.chat_id)
        db.add_expense(user_id, nums[0], date.today(), cat)
        if nums[0] == int(nums[0]):
            nums[0] = int(nums[0])
        update.message.reply_text(f"Got it, you spent ${nums[0]} on {cat.lower()}")
    elif nums and not cat:
        context.user_data['amount'] = nums[0]
        keyboard = [
            [InlineKeyboardButton(cat.title(), callback_data=cat)] for cat in categories
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(f"Got it, you spent ${nums[0]}.\n Please choose a category: ",
                                  reply_markup=reply_markup)
    else:
        update.message.reply_text("Sorry, I didn't quite get that. Can you try again?")


def choose_category(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    user_id = get_user_id(query.message.chat_id)
    amount = context.user_data['amount']
    category = query.data
    db.add_expense(user_id, amount, date.today(), category)
    query.edit_message_text(text=f"Got it, you spent ${amount} on {category.lower()}")


def undo(update: Update, context: CallbackContext) -> None:
    user_id = get_user_id(update.message.chat_id)
    if db.get_expenses(user_id, date.today()):
        last_expense = db.delete_last_expense(user_id)
        amount, d, cat = last_expense[0]
        update.message.reply_text(f"Deleted last expense:\nSpent ${amount} on {cat.lower()} on {d.strftime('%d %b')} ")

    else:
        update.message.reply_text("You have no expenses to undo!")

def repeat(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Ok, let's add a recurring expense. Please enter an amount and category:")

    return REPEAT

def add_recurring_expense(update: Update, context: CallbackContext) -> int:
    user_id = get_user_id(update.message.chat_id)

def main() -> None:
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("show", show_expenses))
    dispatcher.add_handler(CommandHandler("undo", undo))
    dispatcher.add_handler(CallbackQueryHandler(choose_category))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, add_expense_from_message))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
