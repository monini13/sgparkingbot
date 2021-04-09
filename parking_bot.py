
import pandas as pd
import csv
import sqlite3
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


def build_df(path):
    df = pd.read_csv(path,index_col=0)
    df = df.rename(columns={"Name": "name", "Street Address": "address", "Postal Code":"postal", "Parking Rates":"rates"})
    return df
    
def load_sql(df):
    conn = sqlite3.connect('parking.db')
    c = conn.cursor()
    # Create the table
    c.execute("""DROP TABLE IF EXISTS parking_rates;""")
    c.execute(
        """ 
        CREATE TABLE parking_rates(
        name TEXT,
        address TEXT,
        postal INT,
        rates TEXT)
        """
    )
    conn.commit()
    df.to_sql('parking_rates', conn, if_exists='append', index=False)
    conn.close()
    return None

def start(update: Update, _: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_markdown_v2(
        f'Hi {user.mention_markdown_v2()}\!\nSend me either name of building, address, or postal code',
#         reply_markup=ForceReply(selective=True),
    )
    return None


def help_command(update: Update, _: CallbackContext) -> None:
    update.message.reply_text('Help!')
    return None

def echo(update: Update, _: CallbackContext) -> None:
    """Echo the user message."""
    text = update.message.text
    print(update.effective_user['first_name'], text)
    conn = sqlite3.connect('parking.db')
    c = conn.cursor()
    if text.isnumeric() and len(text)>4:
        temp = c.execute('SELECT * FROM parking_rates WHERE postal = {}'.format(text)).fetchone()
    else:
        text = "%{}%".format(text) if len(text)>3 else text+'%'
        temp = c.execute('SELECT * from parking_rates WHERE name LIKE "{}"'.format(text)).fetchone()
        if not temp:
            temp = c.execute('SELECT * from parking_rates WHERE address LIKE "%{}%"'.format(text)).fetchone()
    if temp:
        name, address, postal, rates = temp
        postal = str(postal).zfill(6)
        to_view = name + "\n"
        to_view += "{}, S({})\n\n".format(address,postal)
        to_view += rates
    else:
        to_view = "Sorry, unable to find parking rate from our database\n\n"
        to_view += "If it is an acronym, try adding parenthesis around it. For example: (smu)"
    update.message.reply_text(to_view)
    return None

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
    return None

if __name__ == "__main__":
    df = build_df("carpark_rates.csv")
    load_sql(df)
    main()