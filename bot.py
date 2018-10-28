from telegram.ext import Updater
from telegram.ext import CommandHandler
from os import environ
import logging
import requests
import bs4
import sys
import time
from dotenv import load_dotenv

# setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

# setup env
load_dotenv()


class TelegramRecordBot:

    def __init__(self):

        self.token = environ['BOT_TOKEN']
        self.chat_id = environ['CHAT_ID']
        self.fetch_interval = int(environ['FETCH_INTERVAL'])

        self.updater = Updater(token=self.token)
        self.dispatcher = self.updater.dispatcher
        self.job = self.updater.job_queue

        self.reccount_handler = CommandHandler(
            'count', self.send_records_count)
        self.start_handler = CommandHandler('start', self.start)
        self.dispatcher.add_handler(self.reccount_handler)
        self.dispatcher.add_handler(self.start_handler)
        self.job.run_once(self.greet, 0)
        self.job.run_repeating(self.send_record_updates,
                               interval=self.fetch_interval, first=30)
        self.updater.start_polling()

    def start(self, bot, update):
        bot.send_message(chat_id=self.chat_id, text="Hi!")

    def greet(self, bot, job):
        bot.send_message(chat_id=self.chat_id, text="Waxfetcher started")

    def send_records_count(self, bot, update):
        bot.send_message(
            chat_id=self.chat_id,
            text="Counting LPs, hang on...")
        bot.send_message(
            chat_id=self.chat_id,
            text="long-play.ru has {} EDM records in the store for the moment".format(str(longPlayStore.get_records_count())))

    def send_record_updates(self, bot, job):
        longPlayStore.get_updates()

        for record in longPlayStore.new_records:

            message = '[{artist} — {title}]({link})\n{price}'.format(artist=record['artist'],
                                                                      title=record['title'],
                                                                      link=record['link'],
                                                                      price=record['price']
                                                                      )

            bot.send_photo(chat_id=self.chat_id,
                           photo=record['picture']
                          )

            bot.send_message(chat_id=self.chat_id,
                             text=message,
                             parse_mode='Markdown',
                             disable_web_page_preview=True)


class RecordStore:

    def __init__(self):
        """Get an initial list of records"""
        self.fetch_url = environ['FETCH_URL']
        self.initial_record_pool = self.get_records_from_site()

    def get_records_from_site(self) -> set:
        """Fetch and parse HTML from site"""

        # What is going on here:
        # 1. 'requests.get(fetch_url).text' return an HTML from fetch_url
        # 2. 'bs4.BeautifulSoup' parse this HTML
        # 3. '.select('.item')' extract elements with 'class=item'
        # 4. 'set()' put all these elements in a set for easing further operations (e.g. finding new records)

        return set(bs4.BeautifulSoup(requests.get(self.fetch_url).text, features="lxml").select('.item'))

    def get_records_count(self) -> int:
        """Return number of records"""
        return len(self.get_records_from_site())

    def get_updates(self) -> None:
        """Return a set of new LPs"""
        self.updated_record_pool = self.get_records_from_site()
        self.initial_record_pool.pop()
        self.new_records_unparsed = self.updated_record_pool.difference(
            self.initial_record_pool)
        self.new_records = []

        # Parse an unparsed record pool
        for record in self.new_records_unparsed:
            self.new_records.append(
                {'artist': record.h3.text,
                 'title': record.p.text,
                 'picture': 'http://long-play.ru' + record.find_all("div")[0].contents[0]["src"],
                 'price': record.find_all('div')[1].text,
                 'link': 'http://long-play.ru' + record['href']
                 }
            )

        self.initial_record_pool = self.updated_record_pool


waxfetcher = TelegramRecordBot()
longPlayStore = RecordStore()



"""


def send_record_updates(bot, job):

    for record in longPlayStore.get_updates():
        rec_artist=record.h3.text
        rec_title=record.p.text
        rec_picture='http://long-play.ru' + \
            record.find_all('div')[0].contents[0]['src']
        rec_price=record.find_all('div')[1].text
        rec_link='http://long-play.ru' + record['href']

        message='[{rec_artist} — {rec_title}]({rec_link})\n{rec_price}'.format(rec_artist=rec_artist,
                                                                                 rec_title=rec_title,
                                                                                 rec_price=rec_price,
                                                                                 rec_link=rec_link)
        bot.send_photo(chat_id=chat_id,
                       photo=rec_picture)

        bot.send_message(chat_id=chat_id,
                         text=message,
                         parse_mode='Markdown',
                         disable_web_page_preview=True)









"""
