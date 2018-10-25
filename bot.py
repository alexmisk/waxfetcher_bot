from telegram.ext import Updater
from os import environ
import logging
import requests
import bs4
import sys
from dotenv import load_dotenv

# setup env
load_dotenv()
try:
    bot_token = environ['BOT_TOKEN']
    fetch_url = environ['FETCH_URL']
    chat_id = environ['CHAT_ID']
    fetch_interval = int(environ['FETCH_INTERVAL'])
except:
    print('There is an error in ENV variables.')

# setup bot instance
updater = Updater(token=bot_token)
job = updater.job_queue


# setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


def greet(bot, job):
    bot.send_message(chat_id=chat_id,
                     text="Waxfetcher is ready.")


def get_records() -> set:
    # What is going on here:
    # 1. 'requests.get(fetch_url).text' return an HTML from fetch_url
    # 2. 'bs4.BeautifulSoup' parse this HTML
    # 3. '.select('.item')' extract elements with 'class=item'
    # 5. 'set()' put all these elements in a set for easing further operations (e.g. finding new records)

    return set(bs4.BeautifulSoup(requests.get(fetch_url).text, features="lxml").select('.item'))


# get an initial list of records
old_records = get_records()

# greet on start
job.run_once(greet, when=0)


def send_record_updates(bot, job):
    global old_records
    new_records = get_records()
    updates = new_records.difference(old_records)

    for record in updates:
        rec_artist = record.h3.text
        rec_title = record.p.text
        rec_picture = 'http://long-play.ru' + \
            record.find_all('div')[0].contents[0]['src']
        rec_price = record.find_all('div')[1].text
        rec_link = 'http://long-play.ru' + record['href']

        message = '[{rec_artist} — {rec_title}]({rec_link})\n{rec_price}'.format(rec_artist=rec_artist,
                                                                                 rec_title=rec_title,
                                                                                 rec_price=rec_price,
                                                                                 rec_link=rec_link)
        bot.send_photo(chat_id=chat_id,
                       photo=rec_picture)

        bot.send_message(chat_id=chat_id,
                         text=message,
                         parse_mode='Markdown',
                         disable_web_page_preview=True)

    old_records = new_records


job.run_repeating(send_record_updates,
                  interval=fetch_interval,
                  first=0)

updater.start_polling()
