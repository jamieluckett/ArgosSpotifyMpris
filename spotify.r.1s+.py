#!/usr/bin/env python3
# Spotify argos extension
# by Jamie Luckett https://github.com/jamieluckett

import os
import traceback

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


def get_spotify_object():
    bus = SessionBus()
    return bus.get(BUS_NAME, OBJECT_PATH)


def print_unclickable(text):
    print("{0} | color={1}".format(text, UNCLICKABLE_COLOUR))


def print_control_menu(playback_status):
    if playback_status in ["Stopped", "Paused"]:
        print("<b>Play</b>/Pause | "
              "iconName=media-playback-start "
              "bash='dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify "
              "/org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.PlayPause' "
              "terminal=false")
    elif playback_status == "Playing":
        print("Play/<b>Pause</b> | "
              "iconName=media-playback-pause "
              "bash='dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify "
              "/org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.PlayPause' "
              "terminal=false")

    print("Previous | "
          "iconName=media-skip-backward "
          "bash='dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify "
          "/org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.Previous' "
          "terminal=false")
    print("Next | "
          "iconName=media-skip-forward "
          "bash='dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify "
          "/org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.Next' "
          "terminal=false")


if __name__ == "__main__":
    try:
        spotify_object = get_spotify_object()
        metadata = spotify_object.Metadata
        if os.environ.get("DEBUG", 0) == "1":
            print(metadata)
        artist_list = metadata['xesam:artist']
        if artist_list:
            primary_artist = metadata['xesam:artist'][0]
            playback_status = spotify_object.PlaybackStatus
            song_title = metadata['xesam:title']
            art_url = metadata['mpris:artUrl']
            album_name = metadata['xesam:album']
            print("{0} - {1} | iconName={2} useMarkup=false unescape=true".format(
                primary_artist, song_title, PLAYBACK_STATUS_ICON_MAPPING[playback_status]))
            print("---")
            print_unclickable("Song Title: {0}".format(song_title))
            print_unclickable("Album: {0}".format(album_name))
            if len(artist_list) > 1:
                # If only the plural of Artist was Artist...
                # Spotify never seems to actually return more than 1 artist through mpris though but maybe one day
                print_unclickable("Artists: {0}".format(", ".join(artist_list)))
            else:
                print_unclickable("Artist: {0}".format(", ".join(artist_list)))
            print_control_menu(playback_status)
        else:
            print("Nothing Playing | iconName=media-playback-stop")

    except GError as e:
        # A GError indicates that (most likely) Spotify isn't open.
        print("Spotify isn't open! | iconName=media-playback-stop")
        print("---")
        print("Open Spotify | iconName={0} bash='spotify U%' terminal=false".format(SPOTIFY_ICON_NAME))
    except Exception as e:
        # Catch generic exception here so it can be displayed in the dropdown
        print("Something went wrong! | iconName=dialog-warning")
        print("---")
        print("<b>Exception Details:</b>")
        tb = traceback.format_exc()
        print(tb.replace("\n", "\\n"), "| font=monospace useMarkup=false unescape=true")
