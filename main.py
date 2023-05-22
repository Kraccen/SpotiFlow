import datetime
import logging
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import argparse

import subprocess
import multiprocessing

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

import mouse
import keyboard

import time
import datetime
import os
# high-oriented operations with files and dirs
import shutil

from tkinter import *

import mutagen
from eyed3 import mp3

from savify import Savify
from savify.types import Type, Format, Quality
from savify.utils import PathHolder
import asyncio


def program():
    root = Tk()

    def click(number):
        label_number = Label(root, text=number)
        label_number.pack()

    button1 = Button(text='Write 1', command=lambda: click(1))
    button2 = Button(text='Write 2', command=lambda: click(2))
    button3 = Button(text='Write 3', command=lambda: click(3))
    button1.pack()
    button2.pack()
    button3.pack()

    root.mainloop()


def function_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = round(end_time - start_time, 2)
        print(f"Total time of {func}", total_time, "sec")

    return wrapper


def load(email, password, songs_count=275):
    from selenium.webdriver.chrome.options import Options
    # This blocks images and javascript requests
    chrome_prefs = {
        "profile.default_content_setting_values": {
            "images": 0
        }
    }
    # Now I just read two script files and add their text to string to use them after
    # get_token_path = r"D:\pythonProject\pythonProject\spofity_parser\get_token.js"
    # get_token_script = ''
    # with open(get_token_path, 'r') as js:
    #     for line in js:
    #         get_token_script = get_token_script + line
    #
    create_playlist_path = r"D:\pythonProject\pythonProject\spofity_parser\add_item_to_playlist.js"
    create_playlist_script = ''
    # # TODO This script is working, so I need to add all formatted links from list to this playlist
    with open(create_playlist_path, 'r') as js:
        for line in js:
            create_playlist_script = create_playlist_script + line

    # installing driver for selenium and it's options
    options = Options()

    # if True - window will be in background
    # options.headless = True

    options.add_argument("--window-size=1920,1200")

    options.experimental_options["prefs"] = chrome_prefs

    driver = webdriver.Chrome(options=options)

    with open('music.txt', 'w') as f:
        f.write('this is list of music \n')

    # get the site name and search for block with list of music
    driver.get("https://accounts.spotify.com/ru/login?continue=https%3A%2F%2Fopen.spotify.com%2F")

    # title = driver.execute_script('return document.title')
    # print(title)

    # time.sleep(10)

    # search for forms to input account info
    email_element = driver.find_element(By.ID, 'login-username')
    pass_element = driver.find_element(By.ID, 'login-password')

    # pass a keys to these forms
    email_element.send_keys(email)
    pass_element.send_keys(password)

    # get the button and click on it
    submit = driver.find_element(By.ID, 'login-button')
    submit.click()

    # just wait for loading
    waited_button = WebDriverWait(driver, 200).until(EC.presence_of_element_located((
        By.CLASS_NAME, "Z35BWOA10YGn5uc9YgAp")))

    # user_token = driver.execute_script(get_token_script)
    # print(user_token)

    # change to favorite songs page
    file = driver.get('https://open.spotify.com/collection/tracks')

    # wait until page load by checking element with class (menu of songs)
    ok = WebDriverWait(driver, 200).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'JUa6JJNj7R_Y3i4P8YUX')))

    # define action function(scroll, move)
    actions = ActionChains(driver)
    # create a playlist with top 1 user's track
    # user_playlist = driver.execute_script(create_playlist_script)
    # print(user_playlist)

    # create a js script for scrolling
    java_script = "window.scrollBy(0, 1000);"

    # using count of songs in playlist, move through all playlist
    for i in range(2, songs_count + 2):
        # because of not all elements are visible, move mouse down

        # wait until element appear, if program stuck, move mouse down
        wait_cycle = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f'//div[@aria-rowindex="{i}"]')))
        # search for current element in list
        song = driver.find_element(By.XPATH, f'//div[@aria-rowindex="{i}"]//a[@data-testid="internal-track-link"]')

        driver.execute_script("arguments[0].scrollIntoView();", song)
        # get the link of it
        print(song.get_attribute('href'), song.text)
        # write link into txt file
        with open('music.txt', 'a') as f:
            f.write(song.get_attribute('href') + '\n')


# This function takes .txt file with spotify links to music, format them and makes a playlist of them and return an
# id of playlist
def format_file_to_spotify(file_path):
    print("[+] Start")
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="3adffed607c84e5bb5f34cbcef74154c",
                                                   client_secret="3b291b4ff0044a02bd43e71af9c3da42",
                                                   redirect_uri="https://translate.google.com/?sl=de&tl=en&op=translate",
                                                   scope="playlist-modify-public"
                                                   ))
    playlists = sp.current_user_playlists()
    playlist_id = ''
    playlist_url = ''
    get_link = False
    for i, item in enumerate(playlists['items']):
        if item['name'] == "My download playlist":
            print("[+] Found a same playlist, decision >>")
            answer = input('Playlist with same name exist, add music to it(y)? Or just get link?(n) (y, n) \n')
            if answer.lower() == 'y':
                print("[+] Found a same playlist, decision >> Use this playlist")
                playlist_id = item['id']
                playlist_url = item['external_urls']['spotify']
                break
            elif answer.lower() == 'n':
                print("[+] Found a same playlist, decision >> just get a link of it")
                playlist_url = item['external_urls']['spotify']
                get_link = True
                break
        else:
            user_id = sp.me()['id']
            sp.user_playlist_create(user=user_id, name="My download playlist",
                                    description="This playlist was created by SpotiFlow.py")
            playlist_id = item['id']
            playlist_url = item['external_urls']['spotify']
            break

    if get_link:
        return playlist_url
    with open(file_path, 'r') as music:
        next(music)
        for line in music:
            new_line = line.replace('https://open.', '').replace('.com/', ':').replace('/', ':').replace('spotify:track:', '')
            print(line)
            sp.playlist_add_items(playlist_id, [f'{new_line.strip()}'])
            print(f"{new_line.strip()} added to playlist")
    return playlist_url



def open_spotiflier():
    subprocess.run(r'D:\programs\sp\SpotiFlyer.exe')


# this function download music from txt file via spotifier, using keyboard and mouse (yes, this is disgusting)
def download(playlist_url):
    # https://open.spotify.com/track/3CRDbSIZ4r5MsZ0YwxuEkn
    # move to search placeholder
    # open a Spotiflyer
    p = multiprocessing.Process(target=open_spotiflier)
    p.start()

    input('Maximize this window and press Enter')
    time.sleep(5)
    mouse.drag(1034, 138, 1035, 138, absolute=True, duration=1)
    mouse.click()
    time.sleep(0.05)

    # if delay too low may be incorrect input
    keyboard.write(playlist_url, delay=0.05)
    # click on search button
    mouse.drag(767, 214, 768, 214, absolute=True, duration=0.8)
    mouse.click()
    time.sleep(4)
    # click on download button
    mouse.drag(767, 780, 768, 780, absolute=True, duration=1)
    mouse.click()
    time.sleep(4)
    # click on exit button (on add)
    mouse.drag(918, 274, 918, 273, absolute=True, duration=0.5)
    mouse.click()
    # # click on back button
    # mouse.drag(26, 50, 25, 50, absolute=True, duration=0.5)
    # mouse.click()


def debug():
    x = 2
    while x == 1:
        file_path = 'D:\pythonProject\pythonProject\spofity_parser\music.txt'
        with open(file_path, 'r', newline='') as music:
            next(music)
            for line in music:
                i = 1
                line.split(' ')
                print(line[0:-1])
                if i == 5:
                    break
                else:
                    continue
            break
    while x == 3:
        keyboard.wait('k')
        line = 'http.3535'
        mouse.drag(1034, 138, 1035, 138, absolute=True, duration=1)
        # choose previous text and delete it
        mouse.click()
        mouse.click()
        mouse.click()
        time.sleep(0.05)
        keyboard.press('delete')
        # rewrite text to new song link (split to delete \n new line
        keyboard.write(line, delay=0.05)

    while x == 4:
        keyboard.wait('k')
        n = 'n'
        path = f'E:\its'
        new_path = 'E:\eera'
        os.chdir(path)
        for dir_path, dir_names, filenames in os.walk(path):
            for file in filenames:
                shutil.copy2(os.path.join(path, file), new_path)
                os.rename(file, file)


# function takes a path to folder with music, extract metadata and sort by artist, albums and number in album
# and renaming by these parameters
def song_filter(path, scan_sub_dirs=False, delay=0):
    # get a list with current directories, subdirs and files in current directory
    if delay > 0:
        # this need to use this function with other functions (like one that create a music file that i need to put in
        # right place)
        time.sleep(delay)
    for files in os.walk(path):
        # define a directory and list of music on directory
        directory = files[0]
        music_in_directory = files[2]
        # if there are no music in directory, break or continue depending on patameter
        if not music_in_directory:
            if not scan_sub_dirs:
                break
            else:
                continue
        # this cycle read list of music and sort it by artist, album, number and name (creating folders and renaming)
        for music in music_in_directory:
            # define path to file, it's type and it's metadata
            path_to_music = os.path.join(directory, music)
            # check if there any files inside directory
            dummy_len = len(path_to_music)
            music_type = path_to_music[dummy_len - 3:dummy_len]
            # because of some files in directory isn't music or music without metadata, i place them in new folder
            try:
                music_file = mutagen.File(path_to_music)
            except Exception as err:
                print("++++++++++")
                print(err)
                print(f"Move unknown file - {path_to_music} to 'unknown' directory")
                new_path_to_unknown = os.path.join(path, 'unknown')
                if not os.path.exists(new_path_to_unknown):
                    os.mkdir(new_path_to_unknown)
                os.rename(path_to_music, os.path.join(new_path_to_unknown, music))
                continue

            # get the music bitrate via mutagen and other meta using eyeD3
            bitrate = music_file.info.bitrate / 1000

            music_file = mp3.Mp3AudioFile(path_to_music)

            # because of Windows amazing file system, path mustn't contain some specific symbol, more common i replaced
            artist = str(music_file.tag.artist).replace(" ", '_').replace(":", '_').replace(";", '_').replace("?",
                                                                                                              '_').replace(
                '/', '_').replace('.', ',')
            song_name = str(music_file.tag.title).replace(" ", '_').replace(":", '_').replace(";", '_').replace("?",
                                                                                                                '_').replace(
                '/', '_').replace('.', ',')

            album_name = str(music_file.tag.album).replace(" ", '_').replace(":", '_').replace(";", '_').replace("?",
                                                                                                                 '_').replace(
                '/', '_').replace('.', ',')
            number_in_album = music_file.tag.track_num.count

            print(f"File {path_to_music} and info >> {bitrate} bitrate, {artist} - artist, {song_name} - song,"
                  f" {album_name} - album, {number_in_album} - number in album")
            # This cycle check if artist\album\song directory exist and create dirs if no, and then check file bitrate
            #  if it's exist
            while True:
                # check if artist folder exist
                if os.path.exists(os.path.join(path, str(f"{artist}"))):
                    print('[+] PATH ARTIST EXIST>>CHECK ALBUM')
                    new_path = os.path.join(path, str(f"{artist}"))

                    if os.path.exists(os.path.join(new_path, str(f"{album_name}"))):
                        print('[+] PATH ARTIST/ALBUM EXIST>>CHECK SONG')
                        # album and artist folder exists, so, check if file with same name here
                        new_path_album = os.path.join(new_path, str(f"{album_name}"))
                        file_to_write = str(f"{number_in_album}_{song_name}.{music_type}")

                        if os.path.exists(os.path.join(new_path_album, file_to_write)):
                            print('[+] PATH ARTIST/ALBUM/SONG EXIST>>CHECK BITRATE')
                            # same file detected so we check their bitrates and rewrite that one with lover bitrate
                            existing_music = mutagen.File(os.path.join(new_path_album, file_to_write))
                            bitrate_of_file = existing_music.info.bitrate / 1000

                            if float(bitrate) > float(bitrate_of_file):
                                print('[+] NEW FILE HAVE A BETTER BITRATE>>REWRITING...')
                                # if new file have highest bitrate, rewrite old file with rename func that takes as
                                # argument two path, old and new path
                                os.rename(path_to_music, os.path.join(new_path_album, file_to_write))
                                print('[+] SUCCESSFUL!')
                                break
                            else:
                                print('[+] NEW FILE HAVE A SAME OR SMALLER BITRATE>>SKIP...')
                                # file_to_write = str(f"{number_in_album}_{song_name}.{music_type}")
                                # os.rename(path_to_music, os.path.join('Copy', file_to_write))
                                os.remove(path_to_music)
                                break
                        else:
                            print("[+] PATH ARTIST/ALBUM/SONG DOESN'T EXIST, MOVING FILE TO NEW PATH...")
                            print(os.path.join(new_path_album, file_to_write))

                            # file doesn't exist, so just move it's to new directory
                            os.rename(path_to_music, os.path.join(new_path_album, file_to_write))
                            print('[+] SUCCESSFUL!')
                            break
                    # if some directory doesn't exist, create it and cycle do a new step
                    else:
                        print('[+] PATH ARTIST/ALBUM NOT FOUND, CREATING IT...!')
                        print(new_path, album_name)

                        os.mkdir(os.path.join(new_path, str(f"{album_name}")))
                else:
                    print('[+] PATH ARTIST NOT FOUND, CREATING IT...')
                    print(path, artist)
                    os.mkdir(os.path.join(path, str(f"{artist}")))
        # to prevent work of algorithm inside of subdirectories, break cycle after first directory
        if not scan_sub_dirs:
            break


# TODO Add this function to telegram to detect user's playlists and ask from which of them download music (or from all of them)
@function_time
def get_user_playlist():

    # p = multiprocessing.Process(target=open_spotiflier)
    # p.start()
    track_id = "7lz6NyGH5jL5qrHj1PKUbI"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(redirect_uri=r'https://translate.google.com/?sl=de&tl=en&op=translate'))
    artist_name = sp.track(track_id=track_id)['album']['artists'][0]['name']
    song_name = sp.track(track_id=track_id)
    album_name = sp.track(track_id=track_id)['album']['name']
    release_date = sp.track(track_id=track_id)['album']['release_date']
    print(song_name)
    for i in song_name:
        print(i)
    # print(playlists)

    # for i, item in enumerate(playlists['items']):
    #     print("%d %s %s" % (i, item['name'], item['external_urls']['spotify']))





def get_user_token():
    pass


def spotify_download():
    # # initialize a new safify object with ID and Secret
    # s = Savify(api_credentials=("3adffed607c84e5bb5f34cbcef74154c", "3b291b4ff0044a02bd43e71af9c3da42"),
    #            download_format=Format.MP3, path_holder=PathHolder(downloads_path=r'E:\new_folder'))
    #
    # s.download("https://open.spotify.com/track/11s2w6ITKTKH4JGwoUKhCo")

    import logging

    from savify import Savify
    from savify.types import Type, Format, Quality
    from savify.utils import PathHolder

    # Quality Options: WORST, Q32K, Q96K, Q128K, Q192K, Q256K, Q320K, BEST
    # Format Options: MP3, AAC, FLAC, M4A, OPUS, VORBIS, WAV
    s = Savify(api_credentials=None, quality=Quality.BEST, download_format=Format.MP3,
           path_holder=PathHolder(downloads_path='path/for/downloads'), group='%artist%/%album%',
           skip_cover_art=False)
    s.download('https://open.spotify.com/track/7lz6NyGH5jL5qrHj1PKUbI')

if __name__ == '__main__':
    load(email="Kraccenmoney@gmail.com", password="cqzijmbn12345", songs_count=279)
    format_file_to_spotify(file_path=r'D:\pythonProject\pythonProject\spofity_parser\music.txt')

    # while True:
    #     song_filter(r'E:\music\SpotiFlyer\Playlists\My_download_playlist', delay=1, scan_sub_dirs=False)


    # debug()
    # #program()
    #spotify_download()
    # get_user_playlist()
