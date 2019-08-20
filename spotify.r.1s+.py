#!/usr/bin/env python3
# Spotify argos extension
# by Jamie Luckett https://github.com/jamieluckett

import base64
import hashlib
import os
import traceback

import requests
from gi.repository.GLib import GError
from pydbus import SessionBus

BUS_NAME = "org.mpris.MediaPlayer2.spotify"
OBJECT_PATH = "/org/mpris/MediaPlayer2"

IMAGE_CACHE_DIR = ".config/argos/spotify/"

SPOTIFY_ICON = "spotify-client"
PAUSE_ICON = "media-playback-pause"
PLAY_ICON = "media-playback-start"
STOP_ICON = "media-playback-stop"
BACKWARD_ICON = "media-skip-backward"
FORWARD_ICON = "media-skip-forward"

PLAYBACK_STATUS_ICON_MAPPING = {
    "Paused": PAUSE_ICON,
    "Playing": PLAY_ICON,
    "Stopped": STOP_ICON
}

UNCLICKABLE_COLOUR = "#888888"


def debug_print(body):
    """Prints debug messages if the environment flag DEBUG is 1."""
    if os.environ.get("DEBUG") == "1":
        print(body)


def make_image_cache_dir():
    """Creates IMAGE_CACHE_DIR if it doesn't exist yet."""
    os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)


def argos_print(body="", **kwargs):
    """
    :type body: str
    """
    def arg_format(arg):
        """Reads in passed argument and generates line to put after pipe in argos.
        Wraps values with spaces in quotation marks."""
        name = arg[0]
        value = arg[1]
        if type(value) == str and ' ' in value:
            return "{0}='{1}'".format(name, value)
        return "{0}={1}".format(name, value)

    if kwargs:
        arguments = " ".join([arg_format(arg) for arg in kwargs.items()])
        print("{0} | {1}".format(body, arguments))
    else:
        print(body)


def print_argos_separator():
    """Prints an argos line separator (---)"""
    print("---")


def get_spotify_object():
    """Gets Spotify current song information from dbus via pydbus.
    :rtype CompositeObject"""
    bus = SessionBus()
    return bus.get(BUS_NAME, OBJECT_PATH)


def get_art(art_url):
    """Returns a base64 encoded jpeg of the album art at art_url.
    Saves all downloaded images to IMAGE_CACHE_DIR under the name of art_url md5 hashed.
    :type art_url: string
    :rtype string
    """
    art_url_hash = hashlib.md5(art_url.encode('utf-8')).hexdigest()
    image_location = IMAGE_CACHE_DIR + art_url_hash
    try:
        # We attempt to read the art from the cache as this is both faster for us (no time wasted b64 encoding a jpeg),
        # and much less heavy on Spotify's servers (and our outbound connections)
        with open(image_location, 'r') as f:
            return f.read()
    except FileNotFoundError:
        image = requests.get(art_url).content
        b64_encoded = base64.b64encode(image)
        # TODO - Find a nicer way to return this byte object as a string without b'
        b64_string = repr(b64_encoded)[1:]
        make_image_cache_dir()
        with open(image_location, 'w') as f:
            f.write(b64_string)
        return b64_string


def print_control_menu(playback_status):
    """Prints the music control menu options.
    :type playback_status: str
    """
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


if __name__ == "__main__":
    try:
        spotify_object = get_spotify_object()
        metadata = spotify_object.Metadata
        debug_print(metadata)
        artist_list = metadata['xesam:artist']
        if artist_list:
            # Get current song information
            primary_artist = metadata['xesam:artist'][0]
            playback_status = spotify_object.PlaybackStatus
            song_title = metadata['xesam:title']
            art_url = metadata['mpris:artUrl']
            album_name = metadata['xesam:album']
            # Print current song
            argos_print("{0} - {1}".format(primary_artist, song_title),
                        iconName=PLAYBACK_STATUS_ICON_MAPPING[playback_status],
                        useMarkup="false",
                        unescape="true")
            print_argos_separator()
            argos_print("Song Title: {0}".format(song_title), color=UNCLICKABLE_COLOUR)
            argos_print("Album: {0}".format(album_name), color=UNCLICKABLE_COLOUR)
            if song_title:
                # If only the plural of Artist was Artist...
                # Spotify never seems to actually return more than 1 artist through mpris though but maybe one day
                argos_print("Artists: {0}".format(", ".join(artist_list)), color=UNCLICKABLE_COLOUR)
            else:
                argos_print("Artist: {0}".format(artist_list[0]), color=UNCLICKABLE_COLOUR)
            print_control_menu(playback_status)
            argos_print(image=get_art(art_url), imageWidth="200")
        else:
            argos_print("Nothing Playing", iconName=STOP_ICON)

    except GError as e:
        # A GError indicates that (most likely) Spotify isn't open.
        argos_print("Spotify isn't open!", iconName=STOP_ICON)
        print_argos_separator()
        argos_print("Open Spotify", iconName=SPOTIFY_ICON, bash="spotify U%", terminal="false")
    except Exception as e:
        # Catch generic exception here so it can be displayed in the dropdown
        argos_print("Something went wrong!", iconName="dialog-warning")
        print_argos_separator()
        argos_print("<b>Exception Details:</b>")
        tb = traceback.format_exc()
        argos_print(tb.replace("\n", "\\n"), font="monospace", useMarkup="false", unescape="true")
