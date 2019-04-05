import logging
import pandas

from telegram.ext import CommandHandler, Filters, MessageHandler
from telegram.ext import Updater
from telegram import ReplyKeyboardMarkup, KeyboardButton,ReplyKeyboardRemove


from banks import Bank, BanksGrid
from estimations import PersistentEstimator

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

GOOGLE_API_TOKEN = 'AIzaSyDFn6eczWCBED1adqp2kttHroP7u58UxVo'
BOT_TOKEN = '692895404:AAG4vRQ8zWIVQcP0pajnZXcr1FjdSx2d1F8'
CSV_FILE = 'cajeros-automaticos.csv'
DB_FILE = 'estimacion.db'


def format_bank_list(d_bank_list):
    ret_str = ''
    for index, (distance, bank) in enumerate(d_bank_list):
        ret_str += '{}) {} - {} \n'.format(str(index + 1), bank.name, bank.address)
    if ret_str == '':
        ret_str = 'No hay ningún banco cerca.'
    return ret_str


def generate_googlemapurl(center, positions):
    googlemap_url = 'https://maps.googleapis.com/maps/api/staticmap?' \
                    'center={},{}' \
                    '&zoom=16' \
                    '&size=600x600' \
                    '&markers=color:green%7Clabel:A%7C{},{}' \
                    '&key={}'.format(str(center[0]), str(center[1]),
                                     str(center[0]), str(center[1]),
                                     GOOGLE_API_TOKEN)
    for inx, p in enumerate(positions):
        cache = '&markers=color:red%7Clabel:{}%7C{},{}'.format(str(inx+1),
                                                               str(p[0]), str(p[1]))
        googlemap_url += cache
    return googlemap_url


def command_location(bot, update):
    message = None
    if update.edited_message:
        message = update.edited_message
    else:
        message = update.message
    actual_position = (message.location.latitude, message.location.longitude)

    if message.chat.id in positions:
        cache = positions[message.chat.id]
        del positions[message.chat.id]
        reply_banks(bot, update, cache, actual_position)


def command_link(bot, update, position = None):
    positions[update.message.chat.id] = 'LINK'
    request_position(bot,update)


def command_banelco(bot, update, position = None):
    positions[update.message.chat.id] = 'BANELCO'
    request_position(bot,update)


def request_position(bot,update):
    button_geo = KeyboardButton(text="Enviar", request_location=True)
    # positions[message.chat.id] = actual_position
    keyboard = ReplyKeyboardMarkup(row_width=1, keyboard=[[button_geo]], resize_keyboard=True)
    update.message.reply_text('Por favor enviar su localizacion!', reply_markup=keyboard)
    return


def reply_banks(bot, update, network_name, position = None):
    if position is None:
        button_geo = KeyboardButton(text="Enviar", request_location=True)
        # positions[message.chat.id] = actual_position
        keyboard = ReplyKeyboardMarkup(row_width=1, keyboard=[[button_geo]], resize_keyboard=True)
        update.message.reply_text('Por favor enviar su localizacion!',reply_markup=keyboard)
        return
    current_position = position

    bank_list = bank_grid.nearest_banks(current_position, network_name, estimator)
    bot.send_photo(chat_id=update.message.chat.id,
                   photo=generate_googlemapurl(current_position,
                                               map(lambda x: x[1].position,
                                                   bank_list)))

    update.message.reply_text(format_bank_list(bank_list), reply_markup=ReplyKeyboardRemove())


def load_csv(csv_filename):
    file_csv = open(csv_filename)
    bank_list = []
    data = pandas.read_csv(file_csv, encoding='utf-8', quotechar='"', delimiter=';')
    for row in data.values:
        id, \
        lat, lng, \
        banco, \
        red, \
        dom_orig, \
        *_ = row
        new_bank = Bank(id, red, banco, dom_orig,
                        (float(lat.replace(',', '.')), float(lng.replace(',', '.'))))
        bank_list.append(new_bank)
    bank_grid = BanksGrid(bank_list)
    return bank_grid


def main():
    global estimator, bank_grid, positions
    bank_grid = load_csv(CSV_FILE)
    estimator = PersistentEstimator(DB_FILE)
    positions = dict()

    updater = Updater(token=BOT_TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('link', command_link))
    dispatcher.add_handler(CommandHandler('banelco', command_banelco))
    dispatcher.add_handler(MessageHandler(Filters.location,
                                          command_location, edited_updates=True))
    updater.start_polling()


if __name__ == '__main__':
    main()
