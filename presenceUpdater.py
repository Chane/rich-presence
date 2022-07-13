import logging
import sys
import time
import dbus
import pypresence
import discogs_client
import argparse

from config import APPLICATION_ID, DISCOG_USER_TOKEN

class PresenceUpdater:
    def __init__(self):
        parser = argparse.ArgumentParser();
        parser.add_argument(
            '-d', '--debug',
            help = "Log debug information",
            action = "store_const", dest = "loglevel", const = logging.DEBUG,
            default = logging.WARNING
        )

        parser.add_argument(
            '-v', '--verbose',
            help = "Log verbose information",
            action = "store_const", dest = "loglevel", const = logging.INFO
        )

        args = parser.parse_args();

        logging.basicConfig(stream = sys.stdout, level = args.loglevel)
        self.logger = logging.getLogger(__name__)
        self.writeMessage("Initializing Presence Updater")

        self.bus = dbus.SessionBus()
        self.client = pypresence.Presence(APPLICATION_ID)

        discogClient = discogs_client.Client('DiscordRPCovers/0.1', user_token=DISCOG_USER_TOKEN)

        self.discogsClient = discogClient

    def writeMessage(self, message):
        self.logger.log(logging.INFO, message)
        # print("[INFO][PresenceUpdater]" + message)

    def writeDebug(self, message):
        self.logger.log(logging.DEBUG, message)
        # print("[ERROR][PresenceUpdater]" + message)

    def run(self):
        while True:
            try: 
                self.writeMessage("Connecting to Strawberry MP3 player")
                self.player = self.bus.get_object("org.mpris.MediaPlayer2.strawberry", '/org/mpris/MediaPlayer2')
                self.playerInterace = dbus.Interface(self.player, dbus_interface="org.freedesktop.DBus.Properties")

                self.writeMessage("[Connecting to Discord")
                self.client.connect()

                self.presence_loop()
            
            except dbus.exceptions.DBusException as e:
                self.writeDebug("Connection to Strawberry failed : %s" %str(e))
                self.writeMessage("Reconnecting in 5s")
                self.player = None
                self.playerInterace = None
                time.sleep(5)

            except (pypresence.exceptions.InvalidID) as e:
                self.writeDebug("Connection to Discord failed : %s" % str(e))
                self.writeMessage("Reconnecting in 5s")
                time.sleep(5)

    def presence_loop(self):
        self.writeMessage("Reading data from Strawberry / Updating Discord")
        mprisId = "org.mpris.MediaPlayer2.Player"
        last_album_music = None
        cover = None

        while True:
            try:
                metadata = self.playerInterace.Get(mprisId, "Metadata")
                position = self.playerInterace.Get(mprisId, "Position") / 1000000
                playback_status = self.playerInterace.Get(mprisId, "PlaybackStatus")
            except dbus.exceptions.DBusException as e:
                self.client.clear()
                raise e

            artist_music = None
            album_music = None
            largeText = None

            start = None

            if playback_status == "Stopped":
                small_image = "stop_circle"
                details = "Idle"
                songTitle = None
                artist_music = None
                # TODO: Check other sources to see if they should be displayed
            else:
                temp_metadata = dict()
                for key, value in metadata.items():
                    temp_metadata[key.replace(':', '-')] = value
                try:
                    songTitle = "{xesam-title}".format(**temp_metadata) + " "
                    artist_music = "{xesam-artist[0]}".format(**temp_metadata)
                    album_music = "{xesam-album}".format(**temp_metadata)
                except KeyError:
                    pass

                if artist_music and album_music:
                    details = artist_music + ": " + album_music
                elif artist_music:
                    details = artist_music
                elif album_music:
                    details = "Unknown Artist" + album_music
                elif not artist_music and not album_music:
                    details = "Unknown"

                largeText = songTitle + ' - ' + artist_music

            if last_album_music != album_music:
                try:
                    self.writeMessage("Calling Discogs for " + album_music)
                    results = self.discogsClient.search(album_music, artist=artist_music, type='release')
                    if results.count != 0:
                        cover = self.discogsClient.release(results[0].id).images[0]['uri']
                    last_album_music = album_music
                except KeyError:
                    pass

            if playback_status == "Paused":
                small_image = "pause_si"
                # TODO: If paused also check other sources

            if playback_status == "Playing":
                small_image = "play_si"
            try:
                time_now = time.time()
                start = time_now - position
            except KeyError:
                pass

            self.client.update(large_image=cover,
                    small_image=small_image,
                    small_text=playback_status,
                    large_text=largeText,
                    details=details,
                    state=songTitle,
                    start=start)

            time.sleep(1)