#!/usr/bin/env python3
"""
Spotify media controller argos extension for GNOME 3.
Documentation and source-code (you're already looking at the latter) can be found at:
https://github.com/jamieluckett/ArgosSpotifyMpris
"""

import base64
import hashlib
import os
import sys
import traceback
from collections import namedtuple

ext_modules_error = None

try:
    from pydbus import SessionBus
    import gi
    import requests
except ModuleNotFoundError as e:
    ext_modules_error = e


# USER CONFIGURATION ############################################################################
# Directory to cache previously loaded album art in                                             #
IMAGE_CACHE_DIR = ".config/argos/spotify/"                                                      #
# Icon definitions - icons can be the icon of a program or any built-in GNOME icon              #
SPOTIFY_ICON = "spotify-client"                                                                 #
PAUSE_ICON = "media-playback-pause"                                                             #
PLAY_ICON = "media-playback-start"                                                              #
STOP_ICON = "media-playback-stop"                                                               #
BACKWARD_ICON = "media-skip-backward"                                                           #
FORWARD_ICON = "media-skip-forward"                                                             #
ERROR_ICON = "dialog-warning"                                                                   #
# Colour of the unclickable song information lines                                              #
UNCLICKABLE_COLOUR = "#888888"                                                                  #
# Album Art width (albums are usually square so this is also the height!)                       #
IMAGE_WIDTH = 400                                                                               #
# END OF USER CONFIGURATION #####################################################################

# Dictionary mapping current song state to the icon appearing in the ticker
PLAYBACK_STATUS_ICON_MAPPING = {
    "Paused": PAUSE_ICON,
    "Playing": PLAY_ICON,
    "Stopped": STOP_ICON
}

BUS_NAME = "org.mpris.MediaPlayer2.spotify"  # Spotify dbus bus name
OBJECT_PATH = "/org/mpris/MediaPlayer2"

# Currently (05/05/2020) - The artURL returned by Spotify's MPRIS data 404s.
# It is however possible to get the image from a different cdn server by building the URL out of
# this domain and the ID in the provided artURL.
# https://community.spotify.com/t5/Desktop-Linux/MPRIS-cover-art-url-file-not-found/m-p/4929877/highlight/true#M19504
BACKUP_ART_URL = "https://i.scdn.co/image/"

Song = namedtuple("Song", ["title", "primary_artist", "playback_status", "art_url", "artist_list", "album_name"])


class NoSongException(Exception):
    pass


def debug_print(body):
    """Prints debug messages if the environment flag "DEBUG" is 1."""
    if os.environ.get("DEBUG") == "1":
        print(body)


def make_image_cache_dir(directory_path=IMAGE_CACHE_DIR):
    """Creates the image cache directory (IMAGE_CACHE_DIR) if it doesn't exist yet.
    :return: bool: Whether the image cache directory exists or not.
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception:
        debug_print("Failed to create Image Cache directory {0}".format(directory_path))
        # For some reason the above makedirs failed (even with exist_ok set to True...)
        # So we'll just check that directory_path is a directory and continue.
        return os.path.isdir(directory_path)


def argos_print(body="", **kwargs):
    """
    Generic function to print nicely in the correct argos format the passed body and arguments.
    :param body: str: The text to print on the line
    :param kwargs: {String, String} mappings to be appended to the body as Argos properties
    """
    def arg_format(arg):
        """Reads in passed argument and generates line to put after pipe in argos.
        Wraps values with spaces in quotation marks."""
        name = arg[0]
        value = arg[1]
        if type(value) == str and ' ' in value:
            # Arguments with spaces in must be wrapped in quotation marks
            return "{0}='{1}'".format(name, value)
        return "{0}={1}".format(name, value)

    if kwargs:
        arguments = " ".join([arg_format(arg) for arg in kwargs.items()])
        print("{0} | {1}".format(body, arguments))
    else:
        print(body)


def print_argos_separator():
    """Prints an argos line separator."""
    print("---")


def get_spotify_object():
    """Gets Spotify current song information from dbus via pydbus.
    :rtype CompositeObject"""
    bus = SessionBus()
    return bus.get(BUS_NAME, OBJECT_PATH)


def get_art(art_url):
    """Returns a base64 encoded jpeg of the album art at art_url.
    Saves all downloaded images to IMAGE_CACHE_DIR under the name of art_url md5 hashed.
    Checks the IMAGE_CACHE_DIR first, prioritising any image found there over downloading a new one.
    :param art_url: str: URL of album art to get.
    :return str: Returns the album art after being base64 encoded.
    """
    art_url_hash = hashlib.md5(art_url.encode('utf-8')).hexdigest()
    image_location = IMAGE_CACHE_DIR + art_url_hash
    try:
        # We attempt to read the art from the cache as this is both faster for us (no time wasted b64 encoding a jpeg),
        # and much less heavy on Spotify's servers (and our outbound connections)
        with open(image_location, 'r') as f:
            return f.read()
    except FileNotFoundError:
        request = requests.get(art_url)
        if request.status_code != 200:
            # Use BACKUP_ART_URL domain to get art
            request = requests.get(BACKUP_ART_URL + art_url.split('/')[4])
        image = request.content
        b64_encoded = base64.b64encode(image)
        b64_string = b64_encoded.decode()

        # Cache the art we just downloaded
        dir_exists = make_image_cache_dir(IMAGE_CACHE_DIR)
        if dir_exists:
            with open(image_location, 'w') as f:
                f.write(b64_string)
    return b64_string


def print_control_menu(playback_status):
    """Prints the music control menu options.
    :param playback_status: str: Status of the current song's playback.
    """
    print_music_controls(playback_status)
    print_argos_separator()


def print_music_controls(playback_status):
    if playback_status in ["Stopped", "Paused"]:
        argos_print("<b>Play</b>/Pause",
                    iconName=PLAY_ICON,
                    bash="dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify "
                         "/org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.PlayPause",
                    terminal="false")
    elif playback_status == "Playing":
        argos_print("Play/<b>Pause</b>",
                    iconName=PAUSE_ICON,
                    bash="dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify "
                         "/org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.PlayPause",
                    terminal="false")

    argos_print("Previous",
                iconName=BACKWARD_ICON,
                bash="dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify "
                     "/org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.Previous",
                terminal="false")
    argos_print("Next",
                iconName=FORWARD_ICON,
                bash="dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify "
                     "/org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.Next",
                terminal="false")


def print_lastfm_controls():
    # TODO - Add LastFM controls
    pass


def get_current_song():
    """
    Gets information on the current playing song from the DBus, raises a SpotifyClosedException if it cannot.
    :return Song: A Song object created with song attributes pulled from the dbus.
    """
    # Get Spotify data from dbus
    spotify_object = get_spotify_object()
    metadata = spotify_object.Metadata
    debug_print(metadata)

    # Try and return a Song object, otherwise give up and admit that no song is playing
    try:
        return Song(
            title=metadata['xesam:title'],
            primary_artist=metadata['xesam:artist'][0],
            playback_status=spotify_object.PlaybackStatus,
            art_url=metadata['mpris:artUrl'],
            artist_list=metadata['xesam:artist'],
            album_name=metadata['xesam:album']
        )
    except (IndexError, KeyError) as e:
        raise NoSongException(e)


def print_song(song):
    """
    Prints the current song's information and album art, along with the relevant controls for the playback state.
    :param song: Song: Song to print to the navbar.
    """
    argos_print("{0} - {1}".format(song.primary_artist, song.title),
                iconName=PLAYBACK_STATUS_ICON_MAPPING[song.playback_status],
                useMarkup="false",
                unescape="true")
    print_argos_separator()
    argos_print("Song Title: {0}".format(song.title), color=UNCLICKABLE_COLOUR, useMarkup="false")
    argos_print("Album: {0}".format(song.album_name), color=UNCLICKABLE_COLOUR, useMarkup="false")

    if len(song.artist_list) > 1:
        # Spotify never seems to actually return more than 1 artist through mpris, but maybe one day...
        argos_print("Artists: {0}".format(", ".join(song.artist_list)),
                    color=UNCLICKABLE_COLOUR, useMarkup="false")
    else:
        argos_print("Artist: {0}".format(song.artist_list[0]), color=UNCLICKABLE_COLOUR, useMarkup="false")
    print_control_menu(song.playback_status)
    # TODO - Make clicking the album art bring spotify to the foreground.
    argos_print(image=get_art(song.art_url), imageWidth=IMAGE_WIDTH)


def print_last_exception():
    """
    Prints the last thrown Exception out.
    Also debug_prints it in case the issue lives in argos_print.
    """
    last_exception = traceback.format_exc()
    debug_print(last_exception)
    argos_print("Something went wrong!", iconName=ERROR_ICON)
    print_argos_separator()
    argos_print("<b>Exception Details:</b>")
    argos_print(last_exception.replace("\n", "\\n"), font="monospace", useMarkup="false", unescape="true")


def main():
    """
    Main function for SpotifyArgos.
    """
    if ext_modules_error:
        argos_print("SpotifyArgos Error!", iconName=ERROR_ICON)
        print_argos_separator()
        argos_print("Failed to import third party libraries, please install them using pip.")

        exception_txt_formatted = str(ext_modules_error).replace("\n", "\\n")
        argos_print(
            "ModuleNotFoundError: {0}".format(exception_txt_formatted),
            font="monospace",
            useMarkup="false",
            unescape="true"
        )
        sys.exit(1)
    try:
        current_song = get_current_song()
        print_song(current_song)
    except NoSongException:
        argos_print("Nothing Playing", iconName=STOP_ICON)
    except gi.repository.GLib.GError:
        # A GError indicates that (most likely) Spotify isn't open.
        argos_print("Spotify", iconName=SPOTIFY_ICON)
        print_argos_separator()
        argos_print("Open Spotify", bash="spotify", terminal="false")
    except Exception:
        # Catch generic exception here so it can be displayed in the dropdown
        print_last_exception()
        raise


if __name__ == "__main__":
    main()
