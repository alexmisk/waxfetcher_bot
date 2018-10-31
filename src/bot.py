from telegram.ext import Updater
from telegram.ext import CommandHandler
from os import environ
import logging
import requests
import bs4
import sys
import time

# setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

class TelegramRecordBot:

    def __init__(self):
        
        # setup bot params
        self.token = environ['BOT_TOKEN']
        self.chat_id = environ['CHAT_ID']
        self.fetch_interval = int(environ['FETCH_INTERVAL'])
        
        # general setup for recurring jobs & command handling
        self.updater = Updater(token=self.token)
        self.dispatcher = self.updater.dispatcher
        self.job = self.updater.job_queue

        # setup command handlers
        self.reccount_handler = CommandHandler('count', self.send_records_count)
        self.start_handler = CommandHandler('start', self.start)
        self.dispatcher.add_handler(self.reccount_handler)
        self.dispatcher.add_handler(self.start_handler)
        
        # setup bot jobs
        self.job.run_once(self.greet, 0)
        self.job.run_repeating(self.send_record_updates,
                               interval=self.fetch_interval, 
                               first=30)
        
        # start bot
        self.updater.start_polling()
    
    def greet(self, bot, job) -> None:
        """Greet on bot start"""
        bot.send_message(chat_id=self.chat_id, text="Waxfetcher started")

    def start(self, bot, update) -> None:
        """/start command"""
        bot.send_message(chat_id=self.chat_id, text="Hi!")

    def send_records_count(self, bot, update) -> None:
        """/count command"""
        bot.send_message(
             chat_id=self.chat_id,
             text="Counting LPs, hang on...")
        bot.send_message(
             chat_id=self.chat_id,
             text="long-play.ru has {} EDM records in the store for the moment".format(str(longPlayStore.get_records_count())))
    
    def send_record_updates(self, bot, job) -> None:
        """Core function: send record updates"""
        longPlayStore.get_updates()

        for record in longPlayStore.new_records:

            message = '[{artist} — {title}]({link})\n{price}'.format(
                                                                     artist=record['artist'],
                                                                     title=record['title'],
                                                                     link=record['link'],
                                                                     price=record['price'])

            bot.send_photo(chat_id=self.chat_id,
                           photo=record['picture'])

            bot.send_message(chat_id=self.chat_id,
                             text=message,
                             parse_mode='Markdown',
                             disable_web_page_preview=True)


class RecordStore:

    def __init__(self) -> None:
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
        self.new_records_unparsed = self.updated_record_pool.difference(
            self.initial_record_pool)
        self.new_records = []

        # parse an unparsed record pool
        for record in self.new_records_unparsed:
            self.new_records.append(
                {
                 'artist': record.h3.text,
                 'title': record.p.text,
                 'picture': 'http://long-play.ru' + record.find_all("div")[0].contents[0]["src"],
                 'price': record.find_all('div')[1].text,
                 'link': 'http://long-play.ru' + record['href']
                 }
            )

        self.initial_record_pool = self.updated_record_pool


waxfetcher = TelegramRecordBot()
longPlayStore = RecordStore()