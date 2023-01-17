# -*- coding: utf-8 -*-
"""Simple inline keyboard bot with multiple CallbackQueryHandlers.
This Bot uses the Updater class to handle the bot.
First, a few callback functions are defined as callback query handler. Then, those functions are
passed to the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot that uses inline keyboard that has multiple CallbackQueryHandlers arranged in a
ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line to stop the bot.
"""
import logging
import os
import csv
import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


# Stages
FIRST, SECOND, THIRD = range(3)

# Callback data
ONE, TWO, THREE, FOUR = range(4)

# Acciones
EDIT, REPLY = range(2)

# Ciudades
ciudades = {'RT':'Rada Tilly', 'CR':'Comodoro Rivadavia'}


def str_hoy():
    fecha = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    if fecha.hour < 9:
        fecha = fecha - datetime.timedelta(days=1)
    return fecha.strftime("%d/%m/%Y")


def es_ciudad(diccionario, ciudad):
    return (diccionario['Ciudad'] == ciudad)


def es_dia(diccionario, dia):
    return (diccionario['Fecha'] == dia)


def filtrar_farmacias(dia, ciudad):
    with open('./data/farmacias.csv', 'r', encoding='utf-8') as csvfile:
        lista = list(filter(lambda elem: es_ciudad(elem, ciudad) and es_dia(elem, dia),
                            csv.DictReader(csvfile, delimiter=',')))
    return lista
    # for elemento in lista:
    #     print('Farmacia: {} Dirección: {} Teléfono: {}'.format(elemento['Farmacia'], elemento['Direccion'],
    #                                                            elemento['Telefono']))


def buscar_farmacias(fila):
    with open('./data/farmacias.csv', 'r', encoding='utf-8') as csvfile:
        lista = list(filter(lambda elem: elem['PK'] == fila,
                            csv.DictReader(csvfile, delimiter=',')))
    return lista[0]


def start(update, context):
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    # Build InlineKeyboard where each button has a displayed text
    # and a string as callback_data
    # The keyboard is a list of button rows, where each row is in turn
    # a list (hence `[[...]]`).
    keyboard = [
        [InlineKeyboardButton("Rada Tilly", callback_data='RT'),
         InlineKeyboardButton("Comodoro Rivadavia", callback_data='CR')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    update.message.reply_text(
        "Este es el buscador de farmacias de turno. Elija la ciudad",
        reply_markup=reply_markup
    )
    # Tell ConversationHandler that we're in state `FIRST` now
    return FIRST


def start_over(update, context):
    """Prompt same text & keyboard as `start` does but not as new message"""
    # Get CallbackQuery from Update
    query = update.callback_query
    # Get Bot from CallbackContext
    bot = context.bot
    keyboard = [
        [InlineKeyboardButton("Rada Tilly(2)", callback_data=str(ONE)),
         InlineKeyboardButton("Comodoro Rivadavia(2)", callback_data=str(TWO))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Instead of sending a new message, edit the message that
    # originated the CallbackQuery. This gives the feeling of an
    # interactive menu.
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="Este es el buscador de farmacias de turno. Elija la ciudad",
        reply_markup=reply_markup
    )
    return FIRST


def botones_farmacias(update, context, ciudad, accion):
    # Refactoring all CommanHandlers (accion=REPLY) and CallbackQueryHandlers (accion=EDIT)
    keyboard = []
    for i in filtrar_farmacias(str_hoy(), ciudad):
        botones = [InlineKeyboardButton(i["Farmacia"], callback_data=i["PK"])]
        keyboard.append(botones)
    reply_markup = InlineKeyboardMarkup(keyboard)
    if accion == EDIT:
        query = update.callback_query
        bot = context.bot
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text="Farmacias de turno en "+ciudades[ciudad],
            reply_markup=reply_markup
        )
    elif accion == REPLY:
        update.message.reply_text(
            "Farmacias de turno en "+ciudades[ciudad],
            reply_markup=reply_markup
        )


def cr(update, context):
    """Show new choice of buttons"""
    botones_farmacias(update, context, 'CR', EDIT)
    return THIRD


def rt(update, context):
    """Show new choice of buttons"""
    botones_farmacias(update, context, 'RT', EDIT)
    return THIRD


def cr_init(update, context):
    """Show initial filtered choice of buttons"""
    botones_farmacias(update, context, 'CR', REPLY)
    return THIRD


def rt_init(update, context):
    """Show initial filtered choice of buttons"""
    botones_farmacias(update, context, 'RT', REPLY)
    return THIRD


def button(update, context):
    data = update.callback_query.data
    farmacia = buscar_farmacias(str(data))
    # for elemento in lista:
    #     print('Farmacia: {} Dirección: {} Teléfono: {}'.format(elemento['Farmacia'], elemento['Direccion'],
    #                                                            elemento['Telefono']))
    update.callback_query.message.reply_html(
        "<b>Farmacia: {}</b> - Ubicación: {} - Teléfono: {} - Mapa: {}".format(farmacia['Farmacia'], farmacia['Direccion'], farmacia['Telefono'],  farmacia['URL'])
    )
    return ConversationHandler.END


def end(update, context):
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over"""
    query = update.callback_query
    bot = context.bot
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="¡Hasta pronto!"
    )
    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    # Create the Updater and pass it your bot's token.
    telegram_token = os.environ.get("TOKEN")
    #updater = Updater(telegram_token, use_context=True)
    updater = Updater(telegram_token)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Setup conversation handler with the states FIRST and SECOND
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),
                      CommandHandler('inicio', start),
                      CommandHandler('rt', rt_init),
                      CommandHandler('cr', cr_init)],
        states={
            FIRST: [CallbackQueryHandler(rt, pattern='^' + 'RT' + '$'),
                    CallbackQueryHandler(cr, pattern='^' + 'CR' + '$')],
            # SECOND: [CallbackQueryHandler(start_over, pattern='^' + str(ONE) + '$'),
            #          CallbackQueryHandler(end, pattern='^' + str(TWO) + '$')],
            THIRD: [CallbackQueryHandler(button)]
        },
        fallbacks=[CommandHandler('start', start)]
    )

    # Add ConversationHandler to dispatcher that will be used for handling updates
    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
