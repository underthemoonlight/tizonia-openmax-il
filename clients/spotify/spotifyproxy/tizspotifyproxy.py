# Copyright (C) 2011-2020 Aratelia Limited - Juan A. Rubio and contributors
#
# This file is part of Tizonia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""@package tizspotifyproxy
Simple Spotify API proxy/wrapper.

Access Spotify servers to retrieve audio track URIs and create a playback queue.

"""

import sys
import os
import logging
import random
import unicodedata
import re
import spotipy
import spotipy.util as util
import configparser
from spotipy.oauth2 import SpotifyClientCredentials
from fuzzywuzzy import process
from fuzzywuzzy import fuzz

# For use during debugging
# from pprint import pprint

FORMAT = (
    "[%(asctime)s] [%(levelname)5s] [%(thread)d] "
    "[%(module)s:%(funcName)s:%(lineno)d] - %(message)s"
)

logging.captureWarnings(True)
logging.getLogger().setLevel(logging.DEBUG)

if os.environ.get("TIZONIA_SPOTIFYPROXY_DEBUG"):
    logging.basicConfig(format=FORMAT)
    from traceback import print_exception
else:
    logging.getLogger().addHandler(logging.NullHandler())


class ConfigColors:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(
            os.path.join(os.getenv("HOME"), ".config/tizonia/tizonia.conf")
        )
        active_theme = self.config.get(
            "color-themes", "active-theme", fallback="tizonia"
        )
        active_theme = active_theme + "."
        self.FAIL = (
            "\033["
            + self.config.get("color-themes", active_theme + "C08", fallback="91")
            .replace(",", ";")
            .split("#", 1)[0]
            .strip()
            + "m"
        )
        self.OKGREEN = (
            "\033["
            + self.config.get("color-themes", active_theme + "C09", fallback="92")
            .replace(",", ";")
            .split("#", 1)[0]
            .strip()
            + "m"
        )
        self.WARNING = (
            "\033["
            + self.config.get("color-themes", active_theme + "C10", fallback="93")
            .replace(",", ";")
            .split("#", 1)[0]
            .strip()
            + "m"
        )
        self.OKBLUE = (
            "\033["
            + self.config.get("color-themes", active_theme + "C11", fallback="94")
            .replace(",", ";")
            .split("#", 1)[0]
            .strip()
            + "m"
        )
        self.OKMAGENTA = (
            "\033["
            + self.config.get("color-themes", active_theme + "C12", fallback="95")
            .replace(",", ";")
            .split("#", 1)[0]
            .strip()
            + "m"
        )
        self.ENDC = "\033[0m"


_Colors = ConfigColors()


def pretty_print(color, msg=""):
    """Print message with color.

    """
    print(color + msg + _Colors.ENDC)


def print_msg(msg=""):
    """Print a normal message.

    """
    pretty_print(_Colors.OKGREEN + msg + _Colors.ENDC)


def print_nfo(msg=""):
    """Print an info message.

    """
    pretty_print(_Colors.OKBLUE + msg + _Colors.ENDC)


def print_adv(msg=""):
    """Print an advisory message.

    """
    pretty_print(_Colors.OKMAGENTA + msg + _Colors.ENDC)


def print_wrn(msg=""):
    """Print a warning message.

    """
    pretty_print(_Colors.WARNING + msg + _Colors.ENDC)


def print_err(msg=""):
    """Print an error message.

    """
    pretty_print(_Colors.FAIL + msg + _Colors.ENDC)


def exception_handler(exception_type, exception, traceback):
    """A simple handler that prints the exception message.

    """

    print_err("[Spotify] (%s) : %s" % (exception_type.__name__, exception))

    if os.environ.get("TIZONIA_SPOTIFYPROXY_DEBUG"):
        print_exception(exception_type, exception, traceback)


sys.excepthook = exception_handler


class TizEnumeration(set):
    """A simple enumeration class.

    """

    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError


def to_ascii(msg):
    """Unicode to ascii helper.

    """

    if sys.version[0] == "2":
        return unicodedata.normalize("NFKD", str(msg)).encode("ASCII", "ignore")
    return msg


class TrackInfo(object):
    """ Class that represents a Spotify track in the queue.

    """

    def __init__(self, track, album_name=None):
        """ class members. """
        logging.info("TrackInfo")
        self.title = track["name"]
        self.artist = track["artists"][0]["name"] if track.get("artists") else ""
        self.artist_uri = track["artists"][0]["uri"] if track.get("artists") else ""
        self.album = track["album"]["name"] if track.get("album") else album_name
        self.album_uri = (
            track["album"]["uri"]
            if track.get("album") and track.get("album").get("uri")
            else ""
        )
        if track.get("release_date"):
            self.release_date = track["release_date"]
        else:
            self.release_date = (
                track["album"]["release_date"]
                if track.get("album") and track.get("album").get("release_date")
                else "n/a"
            )
        self.duration = track["duration_ms"] / 1000 if track["duration_ms"] else 0
        m, s = divmod(self.duration, 60)
        h, m = divmod(m, 60)
        if h > 0:
            self.duration_str = str(
                "{:d}h:{:d}m:{:02d}s".format(int(h), int(m), round(s))
            )
        elif m > 0:
            self.duration_str = str("{:d}m:{:02d}s".format(int(m), round(s)))
        else:
            self.duration_str = str("{:02d}s".format(round(s)))
        self.uri = track["uri"]
        self.thumb_url = (
            track["album"]["images"][0]["url"]
            if track.get("album") and track.get("album").get("images")
            else None
        )
        self.explicit = track["explicit"]
        logging.info("TrackInfo end %s", track["explicit"])


class tizspotifyproxy(object):
    """A class that accesses Spotify servers, retrieves track URLs and creates and
    manages a playback queue.

    """

    SPOTIPY_CLIENT_SECRET = "69a32dec47b34e42a72e6a1bde457d65"
    SPOTIPY_CLIENT_ID = "a86ba5bbc8484c56b13c01491aa80edc"
    SPOTIPY_REDIRECT_URI = "http://localhost:8080"

    def __init__(self, user, password):
        self.queue = list()
        self.queue_index = -1
        self.play_queue_order = list()
        self.play_modes = TizEnumeration(["NORMAL", "SHUFFLE"])
        self.current_play_mode = self.play_modes.NORMAL
        self.explicit_filter_modes = TizEnumeration(["ALLOW", "DISALLOW"])
        self.current_explicit_filter_mode = self.explicit_filter_modes.DISALLOW
        self.ntracks_removed_from_queue = 0
        self.now_playing_track = None
        self.user = user
        self._spotify = None  # Lazily initialized

    def set_play_mode(self, mode):
        """ Set the playback mode.

        :param mode: current valid values are "NORMAL" and "SHUFFLE"

        """
        self.current_play_mode = getattr(self.play_modes, mode)
        self._update_play_queue_order()

    def set_explicit_track_filter(self, filter_mode):
        """ Set the explicit track filter.

        :param filter_mode: current valid values are "ALLOW" and "DISALLOW"

        """
        logging.info("")
        self.current_explicit_filter_mode = getattr(
            self.explicit_filter_modes, filter_mode
        )
        if self.current_explicit_filter_mode == self.explicit_filter_modes.DISALLOW:
            self._remove_explicit_tracks()

    def enqueue_tracks(self, arg):
        """Search Spotify for audio tracks and add them to the playback queue.

        :param arg: a search string

        """
        arg_dec = arg
        logging.info("arg : %s", arg_dec)
        print_msg("[Spotify] [Track search] '{0}'.".format(arg_dec))
        try:
            self._login_with_client_credentials()
            count = len(self.queue)
            results = self._spotify.search(arg_dec, limit=50, offset=0, type="track")
            tracks = results["tracks"]
            for i, track in enumerate(tracks["items"]):
                self._enqueue_track(track)

            self._finalise_play_queue(count, arg_dec)

        except ValueError:
            raise ValueError(
                str(
                    "Track not found : %s (or no suitable tracks in queue)"
                    % to_ascii(arg_dec)
                )
            )

    def enqueue_artist(self, arg):
        """Obtain an artist from Spotify and add all the artist's audio tracks
        to the playback queue.

        :param arg: an artist search term

        """
        arg_dec = arg
        logging.info("arg : %s", arg_dec)
        print_msg("[Spotify] [Artist search] '{0}'.".format(arg_dec))
        try:
            self._login_with_client_credentials()
            count = len(self.queue)
            artist = self._search_artists(arg_dec)

            if not artist:
                logging.info(
                    "No artist found with search : %s. Going with a track search",
                    arg_dec,
                )
                results = self._spotify.search(
                    arg_dec, limit=20, offset=0, type="track"
                )
                tracks = results["tracks"]
                for i, track in enumerate(tracks["items"]):
                    artist_id = track["artists"][0]["id"]
                    artist_name = track["artists"][0]["name"]
                    logging.info("Artist found with track search : %s", artist_name)
                    artist = self._spotify.artist(artist_id)
                    if artist:
                        break
            if artist:
                self._enqueue_artist(artist)

            self._finalise_play_queue(count, arg_dec)

        except ValueError:
            raise ValueError(
                str(
                    "Artist not found : %s (or no suitable tracks in queue)"
                    % to_ascii(arg_dec)
                )
            )

    def enqueue_album(self, arg):
        """Obtain an album from Spotify and add all its tracks to the playback
        queue.

        :param arg: an album search term

        """
        arg_dec = arg
        logging.info("arg : %s", arg_dec)
        print_msg("[Spotify] [Album search] '{0}'.".format(arg_dec))
        try:
            self._login_with_client_credentials()
            count = len(self.queue)
            results = self._spotify.search(arg_dec, limit=10, offset=0, type="album")
            albums = results["albums"]
            for i, album in enumerate(albums["items"]):
                if album:
                    self._enqueue_album(album)
                break

            self._finalise_play_queue(count, arg_dec)

        except ValueError:
            raise ValueError(
                str(
                    "Album not found : '%s' (or no suitable tracks in queue)"
                    % to_ascii(arg_dec)
                )
            )

    def enqueue_global_playlist(self, arg):
        """Obtain an album from Spotify and add all its tracks to the playback
        queue.

        :param arg: an album search term

        """
        arg_dec = arg
        logging.info("arg : %s", arg_dec)
        try:
            count = len(self.queue)

            self._enqueue_global_playlist(arg)

            self._finalise_play_queue(count, arg_dec)

        except ValueError:
            raise ValueError(
                str(
                    "Playlist not found : '%s' (or no suitable tracks in queue)"
                    % to_ascii(arg_dec)
                )
            )

    def enqueue_playlist(self, arg, owner):
        """Add all audio tracks in a Spotify playlist to the playback queue.

        :param arg: a playlist search term

        """
        arg_dec = arg
        logging.info("arg : %s", arg_dec)
        print_msg(
            "[Spotify] [Playlist search] '{0}' (owner: {1}).".format(arg_dec, owner)
        )
        try:
            count = len(self.queue)

            if owner != "anyuser" and owner != self.user:
                self._login_with_client_credentials()
                playlist = self._search_playlist(arg_dec, owner, is_featured=False)
                if playlist:
                    results = self._spotify.user_playlist(
                        owner, playlist["id"], fields="tracks,next"
                    )
                    self._enqueue_playlist(results)
            elif owner == self.user:
                self._enqueue_user_playlist(arg)

            if count == len(self.queue) or owner == "anyuser":
                self._enqueue_global_playlist(arg)

            self._finalise_play_queue(count, arg_dec)

        except (ValueError):
            raise ValueError(
                str(
                    "Playlist not found or no audio tracks in playlist : %s"
                    % to_ascii(arg_dec)
                )
            )

    def enqueue_related_artists(self, arg):
        """Search Spotify for an artist and add top tracks from a set of related
        artists.

        :param arg: an artist search term

        """
        arg_dec = arg
        logging.info("arg : %s", arg_dec)
        try:
            self._login_with_client_credentials()
            count = len(self.queue)
            artist = self._search_artists(arg_dec)

            if artist:
                self._enqueue_related_artists(artist)

            self._finalise_play_queue(count, arg_dec)

        except ValueError:
            raise ValueError(
                str(
                    "Artist not found : %s (or no suitable tracks in queue)"
                    % to_ascii(arg_dec)
                )
            )

    def enqueue_featured_playlist(self, arg):
        """Add all audio tracks in a Spotify featured playlist to the playback queue.

        :param arg: a playlist search term

        """
        arg_dec = arg
        logging.info("arg : %s", arg_dec)
        print_msg("[Spotify] [Featured playlist search] '{0}'.".format(arg_dec))
        try:
            self._login_with_client_credentials()
            count = len(self.queue)
            playlist = self._search_playlist(arg_dec, owner=None, is_featured=True)
            if playlist:
                results = self._spotify.user_playlist(
                    playlist["owner"]["id"], playlist["id"], fields="tracks,next"
                )
                self._enqueue_playlist(results)

            self._finalise_play_queue(count, arg_dec)

        except ValueError:
            raise ValueError(
                str(
                    "Playlist not found or no audio tracks in playlist : %s"
                    % to_ascii(arg_dec)
                )
            )

    def enqueue_new_releases(self, arg):
        """Obtain a newly released album from Spotify and add all its tracks to the
        playback queue.

        :param arg: an album search term

        """
        arg_dec = arg
        logging.info("arg : %s", arg_dec)
        print_msg("[Spotify] [New Releases search] '{0}'.".format(arg_dec))
        try:
            self._login_with_client_credentials()
            count = len(self.queue)
            album = None
            album_name = None
            album_dict = dict()
            album_names = list()
            results = self._spotify.new_releases()
            albums = results["albums"]
            for i, alb in enumerate(albums["items"]):
                name = alb["name"]
                print_nfo("[Spotify] [Album] '{0}'.".format(name))
                if arg_dec.lower() == name.lower():
                    album_name = name
                    album = alb
                    break
                if fuzz.partial_ratio(arg_dec, name) > 50:
                    album_dict[name] = alb
                    album_names.append(name)

            if not album_name:
                if len(album_names) > 1:
                    album_name = process.extractOne(arg_dec, album_names)[0]
                    album = album_dict[album_name]
                elif len(album_names) == 1:
                    album_name = album_names[0]
                    album = album_dict[album_name]

            if album:
                if arg_dec.lower() != album_name.lower():
                    print_adv(
                        "[Spotify] '{0}' not found. "
                        "Playing '{1}' instead.".format(arg_dec, album_name)
                    )
                self._enqueue_album(album)

            self._finalise_play_queue(count, arg_dec)

        except ValueError:
            raise ValueError(
                str(
                    "Album not found : '%s' (or no suitable tracks in queue)"
                    % to_ascii(arg_dec)
                )
            )

        #
        # Unfortunately, podcasts URLs are not supported by libspotify
        #
        #     def enqueue_show(self, arg):
        #         """Obtain a show/podcast from Spotify and add all its tracks to the playback
        #         queue.

        #         :param arg: a show/podcast search term

        #         """
        #         arg_dec = arg
        #         logging.info("arg : %s", arg_dec)
        #         print_msg("[Spotify] [Podcast search] '{0}'.".format(arg_dec))
        #         try:
        #             self._login_with_user_token('user-read-playback-position')
        #             count = len(self.queue)
        #             results = self._spotify.search(arg_dec, limit=10, offset=0, type="show")
        #             shows = results["shows"]
        #             for i, show in enumerate(shows["items"]):
        #                 if show:
        #                     self._enqueue_show(show)
        #                 break

        #             self._remove_explicit_tracks()
        #             if count == len(self.queue):
        #                 raise ValueError

        #             self._update_play_queue_order()
        #             self.print_queue()

        # except ValueError:

        #             raise ValueError(
        #                 str(
        #                     "Show not found : '%s' (or no suitable tracks in queue)"
        #                     % to_ascii(arg_dec)
        #                 )
        #             )

    def enqueue_track_id(self, trackid):
        """Add an audio track to the playback queue.

        :param id: an track ID, URI, or URL

        """
        logging.info("id : %s", trackid)
        print_msg("[Spotify] [Track id] '{0}'.".format(trackid))
        try:
            self._login_with_client_credentials()
            count = len(self.queue)
            track = self._spotify.track(trackid)

            if track:
                self._enqueue_track(track)

            self._finalise_play_queue(count, trackid)

        except ValueError:
            raise ValueError(str("Track not found : %s" % to_ascii(trackid)))

    def enqueue_artist_id(self, trackid):
        """Obtain an artist from Spotify and add all the artist's audio tracks
        to the playback queue.

        :param trackid: an artist ID, URI, or URL

        """
        logging.info("id : %s", trackid)
        print_msg("[Spotify] [Artist id] '{0}'.".format(trackid))
        try:
            self._login_with_client_credentials()
            count = len(self.queue)
            artist = self._spotify.artist(trackid)

            if artist:
                self._enqueue_artist(artist)

            self._finalise_play_queue(count, trackid)

        except ValueError:
            raise ValueError(
                str(
                    "Artist not found : %s (or no suitable tracks in queue)"
                    % to_ascii(trackid)
                )
            )

    def enqueue_album_id(self, trackid):
        """Obtain an album from Spotify and add all its audio tracks to the playback
        queue.

        :param trackid: an album ID, URI, or URL

        """
        logging.info("id : %s", trackid)
        print_msg("[Spotify] [Album id] '{0}'.".format(trackid))
        try:
            self._login_with_client_credentials()
            count = len(self.queue)
            album = self._spotify.album(trackid)

            if album:
                self._enqueue_album(album)

            self._finalise_play_queue(count, trackid)

        except ValueError:
            raise ValueError(
                str(
                    "Album not found : '%s' (or no suitable tracks in queue)"
                    % to_ascii(trackid)
                )
            )

    def enqueue_playlist_id(self, trackid, owner):
        """Add all audio items from a playlist to the playback queue.

        :param trackid: an playlist ID, URI, or URL

        """
        logging.info("id : %s", trackid)
        print_msg("[Spotify] [Playlist id] '{0}' (owner: {1}).".format(trackid, owner))
        try:
            self._login_with_client_credentials()
            count = len(self.queue)
            playlist = self._spotify.user_playlist(owner, trackid)

            if playlist:
                self._enqueue_playlist(playlist)

            self._finalise_play_queue(count, trackid)

        except ValueError:
            raise ValueError(str("Playlist not found : %s" % to_ascii(trackid)))

    def enqueue_recommendations_by_track_id(self, trackid):
        """Obtain Spotify recommendations by track id and add tracks to the playback
        queue.

        :param trackid: a Spotify track ID, URI, or URL

        """
        logging.info("id : %s", trackid)
        print_msg("[Spotify] [Recomendations by track id] '{0}'.".format(trackid))
        try:
            count = len(self.queue)
            self._recommendations_by_track_id(trackid)
            self._finalise_play_queue(count, trackid)

        except ValueError:
            raise ValueError(str("Track not found : %s" % to_ascii(trackid)))

    def enqueue_recommendations_by_artist_id(self, trackid):
        """Obtain Spotify recommendations by artist id and add tracks to the playback
        queue.

        :param trackid: a Spotify artist ID, URI, or URL

        """
        logging.info("id : %s", trackid)
        print_msg("[Spotify] [Recomendations by artist id] '{0}'.".format(trackid))
        try:
            count = len(self.queue)
            self._recommendations_by_artist_id(trackid)
            self._finalise_play_queue(count, trackid)

        except ValueError:
            raise ValueError(str("Artist not found : %s" % to_ascii(trackid)))

    def enqueue_recommendations_by_track(self, arg):
        """Obtain Spotify recommendations by track name and add tracks to the playback
        queue.

        :param arg: a track name or search term

        """
        logging.info("arg : %s", arg)
        print_msg("[Spotify] [Recomendations by track] '{0}'.".format(arg))
        try:
            author = ""
            if arg != "":
                word_list = arg.split()
                if len(word_list) > 2 and word_list[-2] == "by":
                    author = word_list[-1]
                    arg = arg.rsplit(" ", 1)[0]
                    arg = arg.rsplit(" ", 1)[0]
            count = len(self.queue)
            self._login_with_client_credentials()
            track_name = None
            artist_name = None
            track_dict = dict()
            track_names = list()
            results = self._spotify.search(arg, limit=20, offset=0, type="track")
            tracks = results["tracks"]
            for i, trk in enumerate(tracks["items"]):
                name = trk["name"]
                artist = trk["artists"][0]
                artist_name = artist["name"]
                print_wrn("[Spotify] [Track] '{0}' by {1}.".format(name, artist_name))
                if (
                    arg.lower() in name.lower()
                    and author.lower() in artist_name.lower()
                ):
                    track_name = name
                    track = trk
                    break
                if fuzz.partial_ratio(arg, name) > 50:
                    track_dict[name] = trk
                    track_names.append(name)

            if not track_name:
                if len(track_names) > 1:
                    track_name = process.extractOne(arg, track_names)[0]
                    track = track_dict[track_name]
                elif len(track_names) == 1:
                    track_name = track_names[0]
                    track = track_dict[track_name]

            if track:
                print_nfo(
                    "[Spotify] [Recomendations by track] Seeding recommendations search with '{0}' by {1}.".format(
                        track_name, artist_name
                    )
                )
                self._recommendations_by_track_id(track["id"])

            self._finalise_play_queue(count, arg)

        except ValueError:
            raise ValueError(str("Tracks not found : %s" % to_ascii(arg)))

    def enqueue_recommendations_by_artist(self, arg):
        """Obtain Spotify recommendations by artist name and add tracks to the playback
        queue.

        :param arg: an artist name or search term

        """
        logging.info("arg : %s", arg)
        print_msg("[Spotify] [Recomendations by artist] '{0}'.".format(arg))
        try:
            count = len(self.queue)
            self._login_with_client_credentials()
            artist = self._search_artists(arg)
            if not artist:
                results = self._spotify.search(arg, limit=1, offset=0, type="track")
                if results:
                    tracks = results["tracks"]
                    track = tracks["items"][0]
                    artist = track["artists"][0]

            print_nfo(
                "[Spotify] [Recommendations by artist] Seeding recommendations search with '{0}'.".format(
                    artist["name"]
                )
            )
            self._recommendations_by_artist_id(artist["id"])

            self._finalise_play_queue(count, arg)

        except ValueError:
            raise ValueError(str("Artist not found : %s" % to_ascii(arg)))

    def enqueue_recommendations_by_genre(self, arg):
        """Obtain Spotify recommendations by genre and add tracks to the playback
        queue.

        :param id: a genre name or search term

        """
        arg_dec = arg
        logging.info("id : %s", arg_dec)
        print_msg("[Spotify] [Recomendations by genre] '{0}'.".format(arg_dec))
        try:
            self._login_with_client_credentials()
            count = len(self.queue)
            genre_seed = list()
            genre_name = None
            genre_names = list()
            results = self._spotify.recommendation_genre_seeds()
            tracks = None
            for gen in results["genres"]:
                print_nfo("[Spotify] [Genre] '{0}'.".format(to_ascii(gen)))
                if arg_dec.lower() == gen.lower():
                    genre_name = gen
                    break
                if fuzz.partial_ratio(arg_dec, gen) > 50:
                    genre_names.append(gen)

            if not genre_name:
                if len(genre_names) > 1:
                    genre_name = process.extractOne(arg_dec, genre_names)[0]
                elif len(genre_names) == 1:
                    genre_name = genre_names[0]

            if genre_name:
                genre_seed.append(genre_name)
                print_wrn("[Spotify] [Genre] Playing '{0}'.".format(genre_name))
                tracks = self._spotify.recommendations(
                    seed_artists=None,
                    seed_genres=genre_seed,
                    seed_tracks=None,
                    limit=100,
                )
            if tracks:
                for track in tracks["tracks"]:
                    self._enqueue_track(track)

            self._finalise_play_queue(count, arg_dec)

        except ValueError:
            raise ValueError(str("Genre not found : %s" % to_ascii(arg_dec)))

    def enqueue_user_liked_tracks(self):
        """Search the current user's liked tracks and add them to the playback queue.

        """
        print_msg("[Spotify] [{0}'s Liked Tracks].".format(self.user))
        try:
            self._login_with_user_token("user-library-read")
            count = len(self.queue)
            tracks = self._spotify.current_user_saved_tracks(limit=50, offset=0)
            for i, track in enumerate(tracks["items"]):
                self._enqueue_track(track["track"])

            self._finalise_play_queue(count, self.user)

        except ValueError:
            raise ValueError(
                str(
                    "No tracks found : %s (or no suitable tracks in queue)"
                    % to_ascii(self.user)
                )
            )

    def enqueue_user_recent_tracks(self):
        """Search the current user's recent tracks and add them to the playback queue.

        """
        print_msg("[Spotify] [{0}'s Recently Played].".format(self.user))
        try:
            self._login_with_user_token("user-read-recently-played")
            count = len(self.queue)
            tracks = self._spotify.current_user_recently_played(limit=50)
            for i, track in enumerate(tracks["items"]):
                self._enqueue_track(track["track"])

            self._finalise_play_queue(count, self.user)

        except ValueError:
            raise ValueError(
                str(
                    "No tracks found : %s (or no suitable tracks in queue)"
                    % to_ascii(self.user)
                )
            )

    def enqueue_user_top_tracks(self):
        """Search the current user's top tracks and add them to the playback queue.

        """
        print_msg("[Spotify] [{0}'s Top Tracks].".format(self.user))
        try:
            self._login_with_user_token("user-top-read")
            count = len(self.queue)
            tracks = self._spotify.current_user_top_tracks(limit=50)
            for i, track in enumerate(tracks["items"]):
                self._enqueue_track(track)

            self._finalise_play_queue(count, self.user)

        except ValueError:
            raise ValueError(
                str(
                    "No tracks found : %s (or no suitable tracks in queue)"
                    % to_ascii(self.user)
                )
            )

    def enqueue_user_top_artists(self):
        """Search the current user's top artists and add their top tracks to the
        playback queue.

        """
        print_msg("[Spotify] [{0}'s Top Artists].".format(self.user))
        try:
            self._login_with_user_token("user-top-read")
            count = len(self.queue)
            artists = self._spotify.current_user_top_artists(limit=20)
            for i, artist in enumerate(artists["items"]):
                self._enqueue_artist(artist, include_albums=False)

            self._finalise_play_queue(count, self.user)

        except ValueError:
            raise ValueError(
                str(
                    "No tracks found : %s (or no suitable tracks in queue)"
                    % to_ascii(self.user)
                )
            )

    def enqueue_user_playlist(self, arg):
        """Add all audio tracks in a Spotify playlist to the playback queue.

        :param arg: a playlist search term

        """
        arg_dec = arg
        logging.info("arg : %s", arg_dec)
        print_msg(
            "[Spotify] [Playlist search] '{0}' (owner: {1}).".format(arg_dec, self.user)
        )
        try:
            count = len(self.queue)

            self._enqueue_user_playlist(arg)

            self._finalise_play_queue(count, self.user)

        except (ValueError):
            raise ValueError(
                str(
                    "Playlist not found or no audio tracks in playlist : %s"
                    % to_ascii(arg_dec)
                )
            )

    def current_track_title(self):
        """ Retrieve the current track's title.

        """
        logging.info("current_track_title")
        track = self.now_playing_track
        title = ""
        if track:
            title = track.title
        return to_ascii(title)

    def current_track_artist(self):
        """ Retrieve the current track's artist.

        """
        logging.info("current_track_artist")
        track = self.now_playing_track
        artist = ""
        if track:
            artist = track.artist
        return to_ascii(artist)

    def current_track_album(self):
        """ Retrieve the current track's album.

        """
        logging.info("current_track_album")
        track = self.now_playing_track
        album = ""
        if track:
            album = track.album
        return to_ascii(album)

    def current_track_release_date(self):
        """ Retrieve the current track's publication date.

        """
        logging.info("current_track_release_date")
        track = self.now_playing_track
        date = ""
        if track:
            date = track.release_date
        return to_ascii(date)

    def current_track_duration(self):
        """ Retrieve the current track's duration.

        """
        logging.info("current_track_duration")
        track = self.now_playing_track
        duration = 0
        if track:
            duration = track.duration
        return duration

    def current_track_album_art(self):
        """ Retrieve the current track's album_art.

        """
        logging.info("current_track_album_art")
        track = self.now_playing_track
        album_art = ""
        if track and track.thumb_url:
            album_art = track.thumb_url
        return to_ascii(album_art)

    def current_track_uri(self):
        """ Retrieve the Spotify URI of the current track.

        """
        logging.info("current_track_uri")
        track = self.now_playing_track
        spotify_uri = ""
        if track:
            spotify_uri = track.uri
        return to_ascii(spotify_uri)

    def current_track_artist_uri(self):
        """ Retrieve the current track's artist URI.

        """
        logging.info("current_track_artist_uri")
        track = self.now_playing_track
        artist_uri = ""
        if track:
            artist_uri = track.artist_uri
        return to_ascii(artist_uri)

    def current_track_album_uri(self):
        """ Retrieve the current track's album URI.

        """
        logging.info("current_track_album_uri")
        track = self.now_playing_track
        album_uri = ""
        if track:
            album_uri = track.album_uri
        return to_ascii(album_uri)

    def current_track_explicitness(self):
        """ Returns 'Explicit' if the current tracks is a 'explicit' track, empty
        string otherwise.

        """
        logging.info("current_track_explicitness")
        track = self.now_playing_track
        explicitness = ""
        if track and track.explicit:
            explicitness = "Explicit"
        return to_ascii(explicitness)

    def current_track_queue_index_and_queue_length(self):
        """ Retrieve index in the queue (starting from 1) of the current track and the
        length of the playback queue.

        """
        qindex = self.queue_index + 1
        qlen = len(self.queue)
        logging.info(
            "current_track_queue_index_and_queue_length: {0} of {1}".format(
                qindex, qlen
            )
        )
        return qindex, qlen

    def clear_queue(self):
        """ Clears the playback queue.

        """
        self.queue = list()
        self.queue_index = -1

    def print_queue(self):
        """ Print the contents of the playback queue.

        """

        for i in range(0, len(self.queue)):
            track = self.queue[self.play_queue_order[i]]
            order_num = str("#{:0{}d}".format(i + 1, len(str(len(self.queue)))))
            info_str = str(
                "[Spotify] [Track] [{0}] '{1}' [{2}] ({3})".format(
                    order_num,
                    to_ascii(track.title),
                    to_ascii(track.artist),
                    to_ascii(track.duration_str),
                )
            )

            # Make sure explicit track titles are not printed if these are not
            # allowed.
            if not track.explicit:
                print_nfo(info_str + ".")
            elif track.explicit and (
                self.current_explicit_filter_mode == self.explicit_filter_modes.ALLOW
            ):
                print_nfo(info_str + " <Explicit>.")

        print_nfo("[Spotify] [Tracks in queue] '{0}'.".format(len(self.queue)))

    def remove_current_uri(self):
        """Remove the currently active uri from the playback queue.

        """
        logging.info("%d - %d", self.queue_index, len(self.queue))
        if len(self.queue) and self.queue_index >= 0:
            track = self.queue[self.queue_index]
            print_nfo("[Spotify] [Track] '{0}' removed.".format(to_ascii(track.title)))
            del self.queue[self.queue_index]
            self.queue_index -= 1
            if self.queue_index < 0:
                self.queue_index = 0
            self._update_play_queue_order()

    def next_uri(self):
        """ Retrieve the uri of the next track in the playback queue.

        """
        logging.info("")
        try:
            if len(self.queue):
                logging.info("")
                self.queue_index += 1
                if (self.queue_index < len(self.queue)) and (self.queue_index >= 0):
                    logging.info("")
                    next_track = self.queue[self.play_queue_order[self.queue_index]]
                    return self._retrieve_track_uri(next_track)
                else:
                    logging.info("%d - %d", self.queue_index, len(self.queue))
                    self.queue_index = -1
                    return self.next_uri()
            else:
                logging.info("")
                return ""
        except (KeyError, AttributeError):
            # TODO: We don't remove this for now
            # del self.queue[self.queue_index]
            logging.info("exception")
            return self.next_uri()

    def prev_uri(self):
        """ Retrieve the uri of the previous track in the playback queue.

        """
        logging.info("")
        try:
            if len(self.queue):
                self.queue_index -= 1
                if (self.queue_index < len(self.queue)) and (self.queue_index >= 0):
                    prev_track = self.queue[self.play_queue_order[self.queue_index]]
                    return self._retrieve_track_uri(prev_track)
                else:
                    self.queue_index = len(self.queue)
                    return self.prev_uri()
            else:
                return ""
        except (KeyError, AttributeError):
            # TODO: We don't remove this for now
            # del self.queue[self.queue_index]
            logging.info("exception")
            return self.prev_uri()

    def get_uri(self, position=None):
        """Retrieve the uri on a particular position in the playback queue. If no
        position is given, the uri at the current position of the playback is returned.

        """
        logging.info("get_uri {}".format(position if position else "-1"))
        try:
            if len(self.queue):
                queue_pos = self.play_queue_order[self.queue_index]
                if position and position > 0 and position <= len(self.queue):
                    self.queue_index = position - 1
                    queue_pos = self.play_queue_order[self.queue_index]
                logging.info("get_uri : self.queue_index {}".format(self.queue_index))
                logging.info(
                    "get_uri : play_queue_order {}".format(
                        self.play_queue_order[self.queue_index]
                    )
                )
                track = self.queue[queue_pos]
                return self._retrieve_track_uri(track)
            else:
                return ""
        except (KeyError, AttributeError):
            # TODO: We don't remove this for now
            # del self.queue[self.queue_index]
            logging.info("exception")
            return ""

    def _enqueue_track(self, track):
        """ Add a track to the playback queue.

        :param track: a track object

        """
        if track:
            track_info = TrackInfo(track)
            self._add_to_playback_queue(track_info)

    def _enqueue_artist(self, artist, include_albums=True):
        """ Add an artist tracks to the playback queue.

        :param artist: a artist object

        """
        if artist:
            artist_name = artist["name"]
            print_wrn("[Spotify] [Artist top tracks] '{0}'.".format(artist_name))

            track_results = self._spotify.artist_top_tracks(artist["id"])
            tracks = track_results["tracks"]
            for i, track in enumerate(tracks):
                track_info = TrackInfo(track)
                self._add_to_playback_queue(track_info)

            if include_albums:
                # Now enqueue albums
                try:
                    album_results = self._spotify.artist_albums(artist["id"], limit=30)
                    album_items = album_results["items"]
                    for i, album in enumerate(album_items):
                        print_wrn("[Spotify] [Album] '{0}'.".format(album["name"]))
                        tracks = self._spotify.album_tracks(
                            album["id"], limit=50, offset=0
                        )
                        for j, track in enumerate(tracks["items"]):
                            track_info = TrackInfo(track, album["name"])
                            self._add_to_playback_queue(track_info)
                except:
                    pass

    def _enqueue_related_artists(self, artist):
        """ Add an artist tracks to the playback queue.

        :param artist: a artist object

        """
        if artist:
            artist_name = artist["name"]
            print_wrn("[Spotify] [Related artists] '{0}'.".format(artist_name))
            try:
                self._enqueue_artist(artist, include_albums=False)
                artist_results = self._spotify.artist_related_artists(artist["id"])
                artists = artist_results["artists"]
                for i, art in enumerate(artists):
                    self._enqueue_artist(art, include_albums=False)
            except:
                pass

    def _enqueue_album(self, album):
        """ Add an album tracks to the playback queue.

        :param album: a album object

        """
        logging.info("_enqueue_album")
        if album:
            album_name = album["name"]
            print_wrn("[Spotify] [Album] '{0}'.".format(album_name))
            try:
                results = self._spotify.album_tracks(album["id"], limit=50, offset=0)
                for track in results["items"]:
                    track_info = TrackInfo(track, album_name)
                    self._add_to_playback_queue(track_info)
            except:
                pass

    #
    # Unfortunately, podcasts URLs are not supported by libspotify
    #
    #     def _enqueue_show(self, show):
    #         """ Add an show tracks to the playback queue.

    #         :param show: a show object

    #         """
    #         logging.info("_enqueue_show")
    #         if show:
    #             show_name = show["name"]
    #             print_wrn("[Spotify] [Show] '{0}'.".format(show_name))
    #             try:
    #                 results = self._spotify.show_episodes(show["id"], limit=50, offset=0)
    #                 for track in results["items"]:
    #                     #pprint(track)
    #                     track_info = TrackInfo(track, show_name)
    #                     self._add_to_playback_queue(track_info)
    #             except:
    #                 pass

    def _enqueue_playlist(self, playlist):
        """ Add an playlist tracks to the playback queue.

        :param playlist: a playlist object

        """
        if playlist:
            tracks = playlist["tracks"]
            while tracks:
                for i, item in enumerate(tracks["items"]):
                    track = item["track"]
                    track_info = TrackInfo(track)
                    self._add_to_playback_queue(track_info)
                if tracks["next"]:
                    tracks = self._spotify.next(tracks)
                else:
                    tracks = None

    def _enqueue_user_playlist(self, arg):
        """Add all audio tracks in a Spotify playlist to the playback queue.

        :param arg: a playlist search term

        """
        arg_dec = arg
        logging.info("arg : %s", arg_dec)
        try:
            count = len(self.queue)
            owner = self.user
            self._login_with_user_token("playlist-read-private")
            playlist = self._search_playlist(arg_dec, owner, is_featured=False)
            if playlist:
                results = self._spotify.user_playlist(
                    owner, playlist["id"], fields="tracks,next"
                )
                self._enqueue_playlist(results)

            if count == len(self.queue):
                print_adv(
                    "[Spotify] [Playlist search] '{0}' not found in the user's library. ".format(
                        arg_dec
                    )
                )

            if count == len(self.queue):
                self._enqueue_global_playlist(arg)

        except (ValueError):
            raise ValueError(
                str(
                    "Playlist not found or no audio tracks in playlist : %s"
                    % to_ascii(arg_dec)
                )
            )

    def _enqueue_global_playlist(self, arg):
        """Obtain an album from Spotify and add all its tracks to the playback
        queue.

        :param arg: an album search term

        """
        arg_dec = arg
        logging.info("arg : %s", arg_dec)
        try:
            self._login_with_client_credentials()
            count = len(self.queue)
            playlist = None
            playlist_name = None
            playlist_dict = dict()
            playlist_names = list()
            results = self._spotify.search(arg_dec, limit=20, offset=0, type="playlist")
            playlists = results["playlists"]
            for i, pl in enumerate(playlists["items"]):
                if pl:
                    owner = pl["owner"]["id"]
                    name = pl["name"]
                    print_msg(
                        "[Spotify] [Global playlist search] '{0}' (owner: {1}).".format(
                            arg_dec, owner
                        )
                    )
                    if arg_dec.lower() == name.lower():
                        playlist_name = name
                        playlist = pl
                        break
                    if fuzz.partial_ratio(arg_dec, name) > 50:
                        playlist_dict[name] = pl
                        playlist_names.append(name)

            if not playlist_name:
                if len(playlist_names) > 1:
                    playlist_name = process.extractOne(arg_dec, playlist_names)[0]
                    playlist = playlist_dict[playlist_name]
                elif len(playlist_names) == 1:
                    playlist_name = playlist_names[0]
                    playlist = playlist_dict[playlist_name]

            if playlist:
                if arg_dec.lower() != playlist_name.lower():
                    print_adv(
                        "[Spotify] '{0}' not found. "
                        "Playing '{1}' instead.".format(arg_dec, playlist_name)
                    )
                results = self._spotify.user_playlist(
                    playlist["owner"]["id"], playlist["id"], fields="tracks,next"
                )
                self._enqueue_playlist(results)

        except ValueError:
            raise ValueError(
                str(
                    "Playlist not found : '%s' (or no suitable tracks in queue)"
                    % to_ascii(arg_dec)
                )
            )

    def _search_artists(self, arg):
        """ Add an artist tracks to the playback queue.

        :param artist: a artist object

        """
        artist = None
        if arg:
            artist_name = None
            artist_dict = dict()
            artist_names = list()
            results = self._spotify.search(arg, limit=20, offset=0, type="artist")
            artists = results["artists"]
            for i, art in enumerate(artists["items"]):
                name = art["name"]
                print_wrn("[Spotify] [Artist] '{0}'.".format(name))
                if arg.lower() == name.lower():
                    artist_name = name
                    artist = art
                    break
                if fuzz.partial_ratio(arg, name) > 50:
                    artist_dict[name] = art
                    artist_names.append(name)

            if not artist_name:
                if len(artist_names) > 1:
                    artist_name = process.extractOne(arg, artist_names)[0]
                    artist = artist_dict[artist_name]
                elif len(artist_names) == 1:
                    artist_name = artist_names[0]
                    artist = artist_dict[artist_name]

        return artist

    def _search_playlist(self, arg, owner=None, is_featured=False):
        """ Add an artist tracks to the playback queue.

        :param artist: a artist object

        """
        playlist = None
        if arg:
            playlists = None
            playlist_name = None
            playlist_dict = dict()
            playlist_names = list()
            playlist_count = 0
            if is_featured:
                featured_playlists = self._spotify.featured_playlists()
                if featured_playlists:
                    playlists = featured_playlists["playlists"]
            elif owner == self.user:
                playlists = self._spotify.current_user_playlists()
            else:
                playlists = self._spotify.user_playlists(owner)
            while playlists:
                for i, plist in enumerate(playlists["items"]):
                    playlist_count += 1
                    print_nfo(
                        "[Spotify] [Playlist {0}] '{1}' ({2} tracks).".format(
                            playlist_count,
                            to_ascii(plist["name"]),
                            plist["tracks"]["total"],
                        )
                    )
                    name = plist["name"]
                    if arg.lower() == name.lower():
                        playlist_name = name
                        playlist = plist
                        break
                    if fuzz.partial_ratio(arg, name) > 50:
                        playlist_dict[name] = plist
                        playlist_names.append(name)

                if not playlist_name:
                    if playlists["next"]:
                        playlists = self._spotify.next(playlists)
                    else:
                        playlists = None
                else:
                    break

            if not playlist_name:
                if len(playlist_names) > 1:
                    playlist_name = process.extractOne(arg, playlist_names)[0]
                    playlist = playlist_dict[playlist_name]
                elif len(playlist_names) == 1:
                    playlist_name = playlist_names[0]
                    playlist = playlist_dict[playlist_name]

            if playlist_name:
                if arg.lower() != playlist_name.lower():
                    print_adv(
                        "[Spotify] [Playlist search] '{0}' not found. "
                        "Playing '{1}' instead.".format(arg, playlist_name)
                    )
                else:
                    print_wrn(
                        "[Spotify] [Playlist] Playing '{0}'.".format(playlist_name)
                    )

        return playlist

    def _recommendations_by_track_id(self, trackid):
        """Obtain Spotify recommendations by track id and add tracks to the playback
        queue.

        :param trackid: a Spotify track ID, URI, or URL

        """
        logging.info("id : %s", trackid)
        try:
            self._login_with_client_credentials()
            track_seed = list()
            track_seed.append(trackid)
            tracks = self._spotify.recommendations(
                seed_artists=None, seed_genres=None, seed_tracks=track_seed, limit=100
            )
            if tracks:
                for track in tracks["tracks"]:
                    self._enqueue_track(track)

        except ValueError:
            raise ValueError(str("Track not found : %s" % to_ascii(trackid)))

    def _recommendations_by_artist_id(self, trackid):
        """Obtain Spotify recommendations by artist id and add tracks to the playback
        queue.

        :param trackid: a Spotify artist ID, URI, or URL

        """
        logging.info("id : %s", trackid)
        try:
            self._login_with_client_credentials()
            artist_seed = list()
            artist_seed.append(trackid)
            tracks = self._spotify.recommendations(
                seed_artists=artist_seed, seed_genres=None, seed_tracks=None, limit=100
            )
            if tracks:
                for track in tracks["tracks"]:
                    self._enqueue_track(track)

        except ValueError:
            raise ValueError(str("Artist not found : %s" % to_ascii(trackid)))

    def _update_play_queue_order(self):
        """ Update the queue playback order.

        A sequential order is applied if the current play mode is "NORMAL" or a
        random order if current play mode is "SHUFFLE"

        """
        total_tracks = len(self.queue)
        if total_tracks:
            if not len(self.play_queue_order):
                # Create a sequential play order, if empty
                self.play_queue_order = list(range(total_tracks))
            if self.current_play_mode == self.play_modes.SHUFFLE:
                random.shuffle(self.play_queue_order)

    def _remove_explicit_tracks(self):
        """ Remove all explicit tracks from the playback queue.

        """
        ntracks_in_queue_before = len(self.queue)
        logging.info(
            "_remove_explicit_tracks : %s - tracks before %d",
            self.current_explicit_filter_mode,
            ntracks_in_queue_before,
        )
        if (
            self.current_explicit_filter_mode == self.explicit_filter_modes.DISALLOW
            and ntracks_in_queue_before > 0
        ):
            logging.info("")
            self.queue[:] = [t for t in self.queue if t.explicit == False]
            logging.info("")
            if len(self.queue) == 0:
                self.queue_index = -1
            elif self.queue_index >= len(self.queue):
                self.queue_index = 0

            logging.info("_remove_explicit_tracks : tracks after %d", len(self.queue))
            if ntracks_in_queue_before > len(self.queue):
                self.ntracks_removed_from_queue = ntracks_in_queue_before - len(
                    self.queue
                )
                print_nfo(
                    "[Spotify] [Queue] '{0}' explicit tracks removed ({1} now in queue).".format(
                        self.ntracks_removed_from_queue, len(self.queue)
                    )
                )

    def _retrieve_track_uri(self, track):
        """ Retrieve a track uri

        """
        try:
            self.now_playing_track = track
            return track.uri

        except AttributeError:
            logging.info("Could not retrieve the track uri!")
            raise

    def add_track_to_playlist(self, arg):
        arg_dec = arg

        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
        print_msg(
            "[Spotify] [Playlist search] '{0}' (owner: {1}).".format(arg_dec, self.user)
        )
        try:
            sp.playlist_add_items(self.enqueue_user_recent_tracks(self), self.current_track_uri(self))
            print_msg(
                "[Spotify] [Add Track to Playlist] '{0}' (owner: {1}).".format(arg_dec, self.user)
            )

        except (ValueError):
            raise ValueError(
                str(
                    "Playlist not found or no audio tracks in playlist : %s"
                    % to_ascii(arg_dec)
                )
            )

    def _add_to_playback_queue(self, track):
        """ Add to the playback queue. """

        self.queue.append(track)

    def _finalise_play_queue(self, count, arg):
        """ Helper function to grou the various actions needed to ready play
        queue.

        """

        self._remove_explicit_tracks()
        if count == len(self.queue):
            logging.info("no tracks found arg : %s", arg)
            raise ValueError
        self._update_play_queue_order()
        self.print_queue()

    def _login_with_client_credentials(self):
        """ Create a Spotify object that access the service with the client's credentials. """

        credentials = SpotifyClientCredentials(
            client_id=self.SPOTIPY_CLIENT_ID, client_secret=self.SPOTIPY_CLIENT_SECRET
        )
        self._spotify = spotipy.Spotify(client_credentials_manager=credentials)

    def _login_with_user_token(self, scope):
        """Create a Spotify object that access the service with the users token and the
        Spotify scope.

        """

        # scope = 'user-top-read'
        # scope = 'user-library-read'
        # scope = 'playlist-read-collaborative'
        # scope = 'playlist-read-private'
        # scope = 'user-read-recently-played'

        auth_cache = os.path.join(
            os.getenv("HOME"),
            ".config/tizonia/"
            + ".spotify-"
            + str(self.user)
            + "-auth-token-"
            + str(scope),
        )

        sp_oauth = spotipy.SpotifyOAuth(
            self.SPOTIPY_CLIENT_ID,
            self.SPOTIPY_CLIENT_SECRET,
            self.SPOTIPY_REDIRECT_URI,
            scope=scope,
            cache_path=auth_cache,
            show_dialog=False,
        )

        print_adv(
            "[Spotify] [Authorization] "
            "Verifying if an authorization token exists for scope '{0}'.".format(
                str(scope)
            )
        )
        print_adv(
            "[Spotify] [Authorization] "
            "You may be asked to input your Spotify credentials on your browser to grant "
            "Tizonia access to your private playlists."
        )
        print_adv(
            "[Spotify] [Authorization] "
            "If a new browser session is not created, please manually copy this URL into your browser:"
        )
        print_adv(
            "[Spotify] [Authorization] '{0}'.".format(sp_oauth.get_authorize_url())
        )

        token = util.prompt_for_user_token(
            self.user,
            scope,
            self.SPOTIPY_CLIENT_ID,
            self.SPOTIPY_CLIENT_SECRET,
            self.SPOTIPY_REDIRECT_URI,
            cache_path=auth_cache,
            oauth_manager=sp_oauth,
            show_dialog=True,
        )
        self._spotify = spotipy.Spotify(auth=token)


if __name__ == "__main__":
    tizspotifyproxy()
