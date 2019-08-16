#!/usr/bin/env python3
# Spotify argos extension
# by Jamie Luckett https://github.com/jamieluckett
import base64
import os
import traceback

import requests
from gi.repository.GLib import GError
from pydbus import SessionBus

BUS_NAME = "org.mpris.MediaPlayer2.spotify"
OBJECT_PATH = "/org/mpris/MediaPlayer2"
SPOTIFY_ICON_NAME = "spotify-client"
PLAYBACK_STATUS_ICON_MAPPING = {
    "Paused": "media-playback-pause",
    "Playing": "media-playback-start",
    "Stopped": "media-playback-stop"
}

UNCLICKABLE_COLOUR = "#888888"


def argos_print(body, **kwargs):
    """
    :type body: str
    """
    def arg_format(arg):
        """"""
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
    """Prints an argos line seperator (---)"""
    print("---")


def get_spotify_object():
    """Gets Spotify current song information from dbus via pydbus
    :rtype CompositeObject"""
    bus = SessionBus()
    return bus.get(BUS_NAME, OBJECT_PATH)


def get_art(art_url):
    """GETs the image from art_url and base64 encodes it
    :type art_url: string
    :rtype string
    """
    image = requests.get(art_url).content
    b64_encoded = base64.b64encode(image)
    # Return the encoded image without the pesky b' at the beginning
    return repr(b64_encoded)[1:]


def print_control_menu(playback_status):
    """Prints the music control menu options
    :type playback_status: str
    """
    if playback_status in ["Stopped", "Paused"]:
        argos_print("<b>Play</b>/Pause",
                    iconName="media-playback-start",
                    bash="dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify "
                         "/org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.PlayPause",
                    terminal="false")
    elif playback_status == "Playing":
        argos_print("Play/<b>Pause</b>",
                    iconName="media-playback-pause",
                    bash="dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify "
                         "/org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.PlayPause",
                    terminal="false")

    argos_print("Previous",
                iconName="media-skip-backward",
                bash="dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify "
                     "/org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.Previous",
                terminal="false")
    argos_print("Next",
                iconName="media-skip-forward",
                bash="dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify "
                     "/org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.Next",
                terminal="false")


if __name__ == "__main__":
    try:
        spotify_object = get_spotify_object()
        metadata = spotify_object.Metadata
        if os.environ.get("DEBUG") == "1":
            print(metadata)
        artist_list = metadata['xesam:artist']
        if artist_list:
            primary_artist = metadata['xesam:artist'][0]
            playback_status = spotify_object.PlaybackStatus
            song_title = metadata['xesam:title']
            art_url = metadata['mpris:artUrl']
            album_name = metadata['xesam:album']
            argos_print("{0} - {1}".format(primary_artist, song_title),
                        iconName=PLAYBACK_STATUS_ICON_MAPPING[playback_status],
                        useMarkup="false",
                        unescape="true")
            print_argos_separator()
            argos_print("Song Title: {0}".format(song_title), color=UNCLICKABLE_COLOUR)
            argos_print("Album: {0}".format(album_name), color=UNCLICKABLE_COLOUR)
            if len(artist_list) > 1:
                # If only the plural of Artist was Artist...
                # Spotify never seems to actually return more than 1 artist through mpris though but maybe one day
                argos_print("Artists: {0}".format(", ".join(artist_list)), color=UNCLICKABLE_COLOUR)
            else:
                argos_print("Artist: {0}".format(", ".join(artist_list)), color=UNCLICKABLE_COLOUR)
            print_control_menu(playback_status)
            argos_print("", image=get_art(art_url), imageWidth="200")
        else:
            argos_print("Nothing Playing", iconName="media-playback-stop")

    except GError as e:
        # A GError indicates that (most likely) Spotify isn't open.
        argos_print("Spotify isn't open!", iconName="media-playback-stop")
        print_argos_separator()
        argos_print("Open Spotify", iconName=SPOTIFY_ICON_NAME, bash="spotify U%", terminal="false")
    except Exception as e:
        # Catch generic exception here so it can be displayed in the dropdown
        argos_print("Something went wrong!", iconName="dialog-warning")
        print_argos_separator()
        argos_print("<b>Exception Details:</b>")
        tb = traceback.format_exc()
        argos_print(tb.replace("\n", "\\n"), font="monospace", useMarkup="false", unescape="true")
