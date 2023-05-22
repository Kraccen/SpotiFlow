import unittest

import bot

import logging

from telegram.ext import ApplicationBuilder, ContextTypes, InlineQueryHandler, CallbackContext, CallbackQueryHandler, \
    CommandHandler, Updater, MessageHandler, filters, ConversationHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, \
    Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


class TestClass(unittest.TestCase):

    def test_bot(self):
        pass

    def test_logs(self):
        logs = bot.Logs("logs")
        logs.write_log("test", "test")
        result = logs.read_log("test")
        self.assertEqual(result, "test\n")
        logs.clear_log("test")
        another_result = logs.read_log("test")
        self.assertEqual(another_result, "")

    def test_selenium_scrape(self):
        result = bot.download_via_scrape('Rammstein - Engel')
        self.assertNotEqual(result, 0)
        self.assertRaises(Exception, result)

