import logging
import os
import time
from moviepy.editor import *
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException


import requests
import selenium_async
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

from pytube import YouTube

import music_tag

from telegram.ext import ApplicationBuilder, ContextTypes, CallbackQueryHandler, \
    CommandHandler,  MessageHandler, filters, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, \
    Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 5):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
# this block helps by detailed logs (if change logging.info to logging.debug in will turn on debug logs)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

log_folder_name = "logs"
# Define a states to Conversation handler
Download_Song_start, Download_Song_ask_url, Download_Song_check_state, Download_Song_final, Register_state,\
    Donate_state = range(6)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(redirect_uri="https://translate.google.com/?sl=de&tl=en&op=translate",
                                               scope="playlist-modify-public"))

cycle_mode = False


# This class describe a user and allow to collect and write it's info to log file
class User:
    bot_token = os.getenv("TOKEN")

    def __init__(self, user_id=None, user_name=None, chat_id=None, user_status=None, spotify_id=None, spotify_secret=None,
                 spotify_redirect=None, log=None):
        self.ID = user_id
        self.name = user_name
        self.chat_id = chat_id
        self.status = user_status
        self.spotify_id = spotify_id
        self.spotify_secret = spotify_secret
        self.spotify_redirect = spotify_redirect
        self.log = log

    def get_user_info(self):
        return f"{self.status} user {self.name} with {self.ID} ID have spotify id - {self.spotify_id} and " \
               f"secret - {self.spotify_secret}, redirect link is {self.spotify_redirect}"

    def log_user_info(self):
        if not os.path.exists(os.path.join(os.getcwd(), log_folder_name)):
            os.mkdir('logs')
        with open(self.log, "w") as file:
            file.write("User ID=" + str(self.ID) + '\n')
            file.write("User name=" + self.name + '\n')
            file.write("Chat id=" + str(self.chat_id) + '\n')
            file.write("User status=" + self.status + '\n')
            file.write("User spotify id=" + str(self.spotify_id) + '\n')
            file.write("User spotify secret=" + str(self.spotify_secret) + '\n')
            file.write("User spotify redirect=" + str(self.spotify_redirect))

    def read_user_info(self):
        mass = {}
        with open(self.log, "r") as file:
            for line in file:
                element, value = line.split(sep='=')
                new_element = {element: value.strip()}
                mass.update(new_element)
        return mass


# example log path
# D:\project\app\logs\5999955_log.txt
class Logs:

    def __init__(self, logs_path):
        self.logs_path = os.path.join(os.getcwd(), logs_path)

    # this method write some message into user's log file
    def write_log(self, message=None, user_id=None):
        if not os.path.exists(self.logs_path):
            os.mkdir(self.logs_path)
        if user_id is None:
            raise AttributeError("No user id was given")
        if message is None:
            raise AttributeError("No message was given")
        log_file_path = os.path.join(self.logs_path, f"{user_id}_log.txt")
        if not os.path.exists(log_file_path):
            with open(log_file_path, "w", encoding="utf-8") as file:
                file.write(message+"\n")
        else:
            with open(log_file_path, "a", encoding="utf-8") as file:
                file.write(message+"\n")

    # read log and return all text inside as string
    def read_log(self, user_id) -> str:
        if not os.path.exists(self.logs_path):
            raise FileNotFoundError("logs folder doesn't exist")
        if user_id is None:
            raise AttributeError("No user id was given")

        log_file_path = os.path.join(self.logs_path, f"{user_id}_log.txt")

        if not os.path.exists(log_file_path):
            raise FileNotFoundError("logs file doesn't exist")
        with open(log_file_path, "r", encoding="utf-8") as file:
            text = ''
            for line in file:
                text += line
            return text

    # clean log by rewriting
    def clear_log(self, user_id):
        if not os.path.exists(self.logs_path):
            raise FileNotFoundError("logs folder doesn't exist")
        if user_id is None:
            raise AttributeError("No user id was given")

        log_file_path = os.path.join(self.logs_path, f"{user_id}_log.txt")

        if not os.path.exists(log_file_path):
            raise FileNotFoundError("logs file doesn't exist")
        else:
            with open(log_file_path, "w", encoding="utf-8") as file:
                file.write("")


logs = Logs("logs")


def function_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = round(end_time - start_time, 2)
        print(f"Total time of {func}", total_time, "sec")

    return wrapper

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu_keyboard = [
        [
            InlineKeyboardButton('Download song', callback_data='download_song')
        ]
    ]
    # I decide to add only admin functionality because of to these functions we need private user information, and
    # it may cause some problems
    admin_keyboard = [
        [
            InlineKeyboardButton('Playlist from favs', callback_data='create_playlist'),
            InlineKeyboardButton('Register', callback_data='register')
        ]

    ]
    menu_markup = InlineKeyboardMarkup(menu_keyboard)
    admin_markup = InlineKeyboardMarkup(admin_keyboard)
    # print out menu with header
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Hello, {update.effective_user.first_name}!"
                                                                    f" This bot created to help you download " 
                                                                    f"music from spotify.\nEnjoy! ",
                                                                    reply_markup=menu_markup)
    # This logic uses class to create a new log with user info
    user_id = update.effective_user.id
    user_name = update.effective_user.name
    chat_id = update.effective_chat.id
    status = "primary"
    admin_id = os.getenv("ADMIN_ID")
    logger.info(f"Admins iD is {admin_id}")
    if str(user_id) in os.getenv("ADMIN_ID"):
        status = "admin"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Spotiflow detected an admin "
                                                                                  f"{user_name}",
                                       reply_markup=admin_markup, protect_content=True)
    else:
        logger.info(f"This user isn't admin")

    user_id = update.effective_user.id
    user_name = update.effective_user.name
    log_folder = os.path.join(os.getcwd(), log_folder_name)
    user_log = os.path.join(log_folder, f"{update.effective_user.id}.txt")

    user = User(user_id=user_id, user_name=user_name, chat_id=chat_id, user_status=status, log=user_log)
    user.spotify_redirect = "link"
    logger.info(user.get_user_info())
    user.log_user_info()
    logger.info(f"User info from log file is {user.read_user_info()}")
    logs = f"User info from log file is {user.read_user_info()}"
    await context.bot.send_message(chat_id=os.getenv("LOGGING_CHAT_ID"), text=logs)


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu_keyboard = [
        [
            InlineKeyboardButton('Download song', callback_data='download_song'),
            InlineKeyboardButton('Playlist from favs', callback_data='create_playlist'),
        ]
    ]
    menu_markup = InlineKeyboardMarkup(menu_keyboard)
    await update.message.reply_text("Please, select an option: ", reply_markup=menu_markup)
    user_status = check_user_info(user_id=update.effective_user.id)['User status']
    logger.info(f'{update.effective_user.id} status is {user_status}')
    if user_status == 'admin':
        admin_keyboard = [
            [
                InlineKeyboardButton('Playlist from favs', callback_data='create_playlist'),
                InlineKeyboardButton('Register', callback_data='register')
            ]

        ]
        admin_markup = InlineKeyboardMarkup(admin_keyboard)
        user_id = update.effective_user.id
        user_name = update.effective_user.name
        status = "primary"
        admin_id = os.getenv("ADMIN_ID")
        logger.info(f"Admins iD is {admin_id}")
        if str(user_id) in os.getenv("ADMIN_ID"):
            status = "admin"
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Spotiflow detected an admin "
                                                                                  f"{user_name}",
                                           reply_markup=admin_markup, protect_content=True)
            global cycle_mode
            cycle_mode = True
        else:
            logger.error(f"This user isn't admin BUT SOMEHOW IT HAVE ADMIN STATUS")

            for admins in os.getenv("ADMIN_ID").split(sep=","):
                await context.bot.send_message(chat_id=admins, text=f'ALARM! Someone get admin status but it is'
                                                                    ' not in admin .env list!')
            unknown_info = check_user_info(user_id)
            await context.bot.send_message(chat_id=os.getenv("LOGGING_CHAT_ID"), text=f"Detected unknown admin user"
                                                                                      f" - {unknown_info}")


async def cycle_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if cycle_mode is True:
        return Download_Song_check_state
    else:
        return ConversationHandler.END


async def cycle_switcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cycle_mode
    if not cycle_mode:
        cycle_mode = True
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Cycle mode on")
    else:
        cycle_mode = False
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Cycle mode of")


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # Get the option selected by the user
    option = query.data
    logger.info(f"{update.effective_user.first_name} choose {option}")
    keyboard = ReplyKeyboardMarkup([[KeyboardButton('Cancel')]], one_time_keyboard=True)

    if option.lower() == "download_song":
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Please, paste a link to song or playlist like"
                                            f" https://open.spotify.com/track/xxxxxxxxxxxxxxxxxxxxxx"
                                            f" or https://open.spotify.com/playlist/xxxxxxxxxxxxxxxxxxxxxx ",
                                       reply_markup=keyboard)
        return Download_Song_check_state
    elif option.lower() == "register":
        await context.bot.send_message(chat_id=update.effective_chat.id, text="If you want to use additional tools, for "
                                                                              "correct work we need your Spotify "
                                                                              "Credentials, here a simple instruction "
                                                                              "how to get it\n "
                                                                              "1. Go to https://developer.spotify.com\n"
                                                                              "2. Create an account\n"
                                                                              "3. Create a new app in 'Dashboard'\n"
                                                                              "4. Name your app as you want, as redirect"
                                                                              "link you can use "
                                                                              "'https://translate.google.com'\n"
                                                                              "5. Go to 'Dashboard', open your app,"
                                                                              "click on 'settings'"
                                                                              "6. Paste a ID, Secret, and Redirecting "
                                                                              "after  as example\n"
                                                                              "'id', 'secret', 'redirect'\n"
                                                                              "Please, keep this order!",
                                       reply_markup=keyboard)
        return Register_state
    elif option.lower() == "donate":
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Not realized yet)")
        await context.bot.send_message(chat_id=os.getenv("LOGGING_CHAT_ID"), text="Someone clicked the donate button")
        return Donate_state
    else:
        logger.info(f"{update.effective_user.first_name} choose {option}, but it have no effect, bug?")


async def check_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    confirmation = update.message.text
    if confirmation.lower() == 'cancel':
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Input Canceled',
                                       reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    if confirmation.find('https://open.') == -1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Invalid link, please, try again")
        return Download_Song_check_state

    # removing si=xxxxx part from end of link and another unuseful stuff
    track_id = confirmation.split("/")[-1].split("?")[0]

    # Checking for folders that will used for downloading and sending files
    if not os.path.exists('Downloaded'):
        os.mkdir('Downloaded')
        user_id = str(update.effective_user.id)
        check_folder = os.path.join(os.getcwd(), "Downloaded")
        if not os.path.exists(os.path.join(check_folder, user_id)):
            os.mkdir(os.path.join(check_folder, user_id))
            download_folder = os.path.join(check_folder, user_id)
        else:
            download_folder = os.path.join(check_folder, user_id)
    else:
        user_id = str(update.effective_user.id)
        check_folder = os.path.join(os.getcwd(), "Downloaded")
        if not os.path.exists(os.path.join(check_folder, user_id)):
            os.mkdir(os.path.join(check_folder, user_id))
            download_folder = os.path.join(check_folder, user_id)
        else:
            download_folder = os.path.join(check_folder, user_id)

    # This block check if link is valid via Spotipy and it's exception, if there a correct link to track or playlist
    # it return a next step (else block). All errors won't appear because I don't use exceptions
    await context.bot.send_message(chat_id=os.getenv("LOGGING_CHAT_ID"),
                                   text=f"{update.effective_user.name} trying to download {confirmation}...")
    user_try_id = update.message.message_id
    try:
        track_href = sp.track(confirmation)
        logger.info(f"{update.effective_user.name} trying to download {confirmation}...")
    # checking url
    except SpotifyException as exp_song:
        try:
            playlist_href = sp.playlist(confirmation)
        except SpotifyException as exp_playlist:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Invalid link, please, try again")
            return Download_Song_check_state

        # Spotify successfully detected a playlist
        else:

            await update.message.reply_text(text=f"{update.effective_user.name} This is a playlist, checking url",
                                            reply_to_message_id=user_try_id)
            logs.write_log(f"{update.effective_user.name} This is a playlist", user_id)
            logger.info(f"URL is correct, try to download it...")
            playlist_href = sp.playlist(confirmation)
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=f"URL is correct, try to download it... ")
            track_uris = [x['track']['uri'] for x in sp.playlist_items(playlist_id=track_id)['items']]
            errors_count = 0
            # print(track_uris)
            for track in track_uris:
                try:
                    track_id = track.strip()
                    download(track_id=track_id, user_id=user_id)
                    log = logs.read_log(user_id=user_id)
                    await context.bot.send_message(chat_id=os.getenv("LOGGING_CHAT_ID"), text=log+f"\n{update.effective_user.name}, {user_id}")
                    logs.clear_log(user_id=user_id)
                except Exception as exp:
                    print(exp)
                    errors_count += 1

            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=f"Done, can't download {errors_count} of music")

    # Spotify successfully detected a track
    else:

        await update.message.reply_text(text=f"{update.effective_user.name} This is a single track, checking url...",
                                        reply_to_message_id=user_try_id)
        logger.info(f"URL is correct, try to download it...")
        logs.write_log(f"{update.effective_user.name} This is a single track", user_id)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"URL is correct, try to download it...")
        try:
            from savify.exceptions import InternetConnectionError

            # FIXME This produce an endless cycle, so need to fix this inside of one of these libs
            # s = Savify(api_credentials=None, quality=Quality.BEST, download_format=Format.MP3,
            #            path_holder=PathHolder(downloads_path=download_folder),
            #            skip_cover_art=False)
            # s.download(confirmation)
            raise Exception("Haven't done yet")
        except Exception as exp:

            await context.bot.send_message(chat_id=update.effective_chat.id, text='Please, wait a little bit...')

            download(track_id=track_id, user_id=user_id)
            log = logs.read_log(user_id=user_id)
            await context.bot.send_message(chat_id=os.getenv("LOGGING_CHAT_ID"), text=log)
            logs.clear_log(user_id=user_id)
            return ConversationHandler.END


# This function scrape music data, download it from youtube, update file metadata and send it to user
def download(track_id, user_id):
    # track_id = confirmation.replace('https://open.spotify.com/track/', '').strip()
    logger.info(f'Get a new spotify ID - {track_id}. Try to download music and update metadate')
    logs.write_log(user_id=user_id, message=f'Get a new spotify ID - {track_id}. Try to download music and update metadate')
    # cycle to get all artists if in song more that one artist

    artist_name = ''
    for artists in sp.track(track_id=track_id)['album']['artists']:
        current_artist_name = artists['name']
        artist_name += f"{current_artist_name}, "

    artist_name = artist_name.strip()[0:-1]
    song_name = sp.track(track_id=track_id)['name']
    album_name = sp.track(track_id=track_id)['album']['name']
    release_date = sp.track(track_id=track_id)['album']['release_date']

    music = f'{artist_name} - "{song_name}"'
    path_to_music = download_via_scrape(music_name=music, user_id=user_id)
    meta = music_tag.load_file(path_to_music)
    meta['album'] = album_name
    meta['artist'] = artist_name
    meta['year'] = release_date
    meta['tracktitle'] = song_name
    meta.save()
    load_dotenv()
    with open(path_to_music, 'rb') as audio:
        payload = {
            'chat_id': user_id,
            'title': f'{music}.mp3',
            'parse_mode': 'HTML'
        }
        files = {
            'audio': audio,
        }
        resp = requests.post(
            "https://api.telegram.org/bot{token}/sendAudio".format(
                token=os.getenv('TOKEN')),
            data=payload,
            files=files).json()

    # delete file for memory saving
    # delete_file(path_to_music)


def async_download(music):
    pass


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    confirmation = update.message.text

    if confirmation.lower() == 'cancel':
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Input Canceled',
                                       reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    # example: register 3adffed607c84e5bb5f34cbcef74154c, 3b291b4ff0044a02bd43e71af9c3da42,
    # https://translate.google.com/?sl=de&tl=en&op=translate
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Checking...')
    not_a_credentials = confirmation.find("http:")
    logger.info(f"{update.effective_user.first_name} result of checking is {not_a_credentials}")
    if not_a_credentials<0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Invalid credentials, please, try again')
        return Register_state
    else:
        elements = confirmation.split(',')
        if len(elements) < 3:
            await context.bot.send_message(chat_id=update.effective_chat.id, text='Invalid credentials, please, try again')
            return Register_state
        client_id, client_secret, redirect_url = elements[0:]
        logger.info(f"{update.effective_user.first_name} credentials is {client_id}, {client_secret}, {redirect_url}")

        # try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                       client_secret=client_secret,
                                                       redirect_uri=redirect_url,
                                                       scope="playlist-modify-public"))
        playlists = sp.current_user_playlists()
        logger.info(f"{update.effective_user.first_name} playlists is {playlists}")
        # except Warning as exp:
        #     await context.bot.send_message(chat_id=update.effective_chat.id,
        #                                    text='Invalid credentials, please, try again')
        #     logger.error(exp)
        #     return Register_state

        await context.bot.send_message(chat_id=update.effective_chat.id, text='Successful!',
                                       reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END


async def donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Not finished yet)')
    return ConversationHandler.END


async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Input Canceled)', reply_markup=ReplyKeyboardRemove)
    return ConversationHandler.END


# This function download a music via name from youtube and return a path to file or error if no music_name
# or failed to download
# @function_time
def download_via_scrape(music_name=None, user_id=None, number_of_cycles=100, checkout_timeout=2, SLEEP=300):
    # checking for attributes and folders
    if music_name is None:
        raise AttributeError("No music name was given")
    if user_id is None:
        raise AttributeError("No user id was given")
    if not os.path.exists('Downloaded'):
        os.mkdir('Downloaded')
        check_folder = os.path.join(os.getcwd(), "Downloaded")
        if not os.path.exists(os.path.join(check_folder, user_id)):
            os.mkdir(os.path.join(check_folder, user_id))
            download_folder = os.path.join(check_folder, user_id)
        else:
            download_folder = os.path.join(check_folder, user_id)
    else:
        check_folder = os.path.join(os.getcwd(), "Downloaded")
        if not os.path.exists(os.path.join(check_folder, user_id)):
            os.mkdir(os.path.join(check_folder, user_id))
            download_folder = os.path.join(check_folder, user_id)
        else:
            download_folder = os.path.join(check_folder, user_id)

    # configure and start web driver
    chrome_prefs = {
        "profile.default_content_setting_values": {
            "images": 0
        },
        "download.default_directory": download_folder
    }
    options = Options()
    # options.add_argument("--window-size=1920,1200")
    options.experimental_options["prefs"] = chrome_prefs
    # options.add_argument('--headless=new')
    options.add_argument("binary = ")
    driver = webdriver.Chrome(options=options)
    actions = ActionChains(driver)
    final_link = ""
    track = music_name.split()
    for word in track:
        final_link += word + "+"
    logger.info(f"current search query is {final_link}")
    logs.write_log(user_id=user_id, message=f"current search query is {final_link}")
    driver.get(f"https://www.youtube.com/results?search_query={final_link}")

    cookies_dialog = WebDriverWait(driver, SLEEP).until(EC.presence_of_element_located((By.ID, "dialog")))
    cookies_button = driver.find_element(By.XPATH, f'//yt-button-shape//button[@class="yt-spec-button-shape-next yt-spec-button-shape-next--filled yt-spec-button-shape-next--call-to-action yt-spec-button-shape-next--size-m "]')
    # actions.scroll_to_element(element=cookies_button)
    driver.execute_script("arguments[0].scrollIntoView();", cookies_button)
    cookies_button.click()

    result = WebDriverWait(driver, SLEEP).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#contents ytd-item-section-renderer>div#contents a#thumbnail")))
    first_song = result.get_attribute('href')
    logger.info(f"got a link - {first_song}")
    logs.write_log(user_id=user_id, message=f"got a link - {first_song}")

    driver.get('https://en.onlymp3.to/192/')

    filling_form = driver.find_element(By.ID, 'txtUrl')
    filling_form.send_keys(first_song)

    submit_button = driver.find_element(By.ID, "btnSubmit")
    submit_button.click()

    # <button class="btn"><a
    try:

        download_link = WebDriverWait(driver, SLEEP).until(EC.presence_of_element_located((By.XPATH, '//button[@class="btn"]//a')))
    except TimeoutException:
        try:
            download_link = WebDriverWait(driver, SLEEP).until(
                EC.presence_of_element_located((By.XPATH, '//button[@class="btn"]//a')))
        except TimeoutException:

            logger.error("Selenium can't find //button[@class='btn'']//a  in Download via scrape")
            logs.write_log(user_id=user_id, message="Selenium can't find //button[@class='btn'']//a  in Download via scrape")
        else:
            driver.get(download_link.get_attribute('href'))
            wait = 0
            while wait < number_of_cycles:
                for dir, subdirs, files in os.walk(download_folder):
                    if files:
                        print('find files')
                        if files[0].endswith('.mp3'):
                            final_path = os.path.join(download_folder, files[0])
                            print(f"{files[0], final_path}")
                            return final_path
                    wait += 1
                    time.sleep(checkout_timeout)
    else:
        driver.get(download_link.get_attribute('href'))
        wait = 0
        while wait < number_of_cycles:
            for dir, subdirs, files in os.walk(download_folder):
                if files:
                    print('find files')
                    if files[0].endswith('.mp3'):
                        final_path = os.path.join(download_folder, files[0])
                        logger.info(f"Got a file {files[0], final_path}")
                        logs.write_log(user_id=user_id, message=f"Successfully downloaded a file {final_path}")
                        return final_path
                wait += 1
                time.sleep(checkout_timeout)
    logs.write_log(user_id=user_id, message="Error, function waited for file for too long")
    # Deleting all files in download folder (if file is too big, it may cause errors if don't delete it's non-downloaded file
    for x, y, files in os.walk(download_folder):
        for file in files:
            os.remove(os.path.join(download_folder, file))
    raise TimeoutError("Function awaited for too long and didn't get an argument, file must be"
                       " too big or there is Connection error")


# FIXME This shit actualy won't works with paths like D:\\pythonProject\\pythonProject\\spofity_parser\\Downloaded\\5853213577\\onlymp3.to - 2517 Жду чуда-LP2PsZ71pig-256k-1658342574476.mp3
def rename_file(path_to_file, title, artist) -> str:
    music_name = path_to_file.split("\\")[-1]
    updated_name = f"{artist}-{title}.mp3"
    final_path = path_to_file.replace(music_name, updated_name)
    os.rename(path_to_file, final_path)
    return final_path


def mp4_tagging():
    track = "spotify:track:4xF4ZBGPZKxECeDFrqSAG4"
    x = sp.track(track)
    print(x['name'])

def format_string_for_win_filesystem(string) -> str:
    string = string.replace(" ", '_').replace(":", '_').replace(";", '_').replace("?", '_').replace('/', '_')
    return string


# This function return a dictionary with user info previously created with User class
def check_user_info(user_id):
    mass = {}
    log = os.path.join(log_folder_name, f"{user_id}.txt")
    with open(log, "r") as file:
        for line in file:
            element, value = line.split(sep='=')
            new_element = {element: value.strip()}
            mass.update(new_element)
    return mass


def delete_file(path):
    os.remove(path)


# this function write some information into txt file and can return this info or delete file




def main():
    load_dotenv()
    # os.getenv() to get token
    application = ApplicationBuilder().token(os.getenv('TOKEN')).build()
    # Download_Song_ask_url_state, Download_Song_check_state, Download_Song_final
    start_command_handler = CommandHandler('start', start)
    menu_command_handler = CommandHandler('menu', menu)
    cycle_mode_command_handler = CommandHandler("cycle", cycle_switcher)
    menu_callback_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_callback)],
        states={
            Download_Song_start: [MessageHandler(filters.TEXT & (~filters.COMMAND), menu_callback)],
            # Download_Song_ask_url: [MessageHandler(filters.TEXT & (~filters.COMMAND), ask_url)],
            Download_Song_check_state: [MessageHandler(filters.TEXT & (~filters.COMMAND), check_url)],
            Download_Song_final: [MessageHandler(filters.TEXT & (~filters.COMMAND), download)],
            Register_state: [MessageHandler(filters.TEXT & (~filters.COMMAND), register)],
            Donate_state: [MessageHandler(filters.TEXT & (~filters.COMMAND), donate)],
        },
        fallbacks=[MessageHandler(filters.TEXT & filters.Regex('^Cancel$'), fallback)]
    )
    cycle_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & (~filters.COMMAND), cycle_state)],
        states={
            Download_Song_check_state: [MessageHandler(filters.TEXT & (~filters.COMMAND), check_url)],
            Download_Song_final: [MessageHandler(filters.TEXT & (~filters.COMMAND), download)],
        },
        fallbacks=[MessageHandler(filters.TEXT & filters.Regex('^Cancel$'), fallback)]
    )
    application.add_handler(start_command_handler)
    application.add_handler(menu_callback_conversation)
    application.add_handler(menu_command_handler)
    application.add_handler(cycle_conversation)
    application.add_handler(cycle_mode_command_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
    # mp4_tagging()
    # file = download_via_scrape(music_name="Батько наш бандера", user_id="5853213577")
    # print(file)
    # rename_file(path_to_file=r"D:\pythonProject\pythonProject\spofity_parser\Downloaded\5853213577\onlymp3.to - 2517 Жду чуда-LP2PsZ71pig-256k-1658342574476.mp3", title="Жду чуда", artist=r"25\17")