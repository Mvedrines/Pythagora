# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Copyright 2010 B. Kroon <bart@tarmack.eu>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#-------------------------------------------------------------------------------
class Library:
    '''Supplies a storage model for the mpd database.'''
    def __init__(self, mainlist):
        self._songList = []
        self._artists = {}
        self._albums = {}
        self._genres = {}
        self._filesystem = {}
        # parse the list and prepare it for loading in the library browser and the file system view.
        for song in (x for x in mainlist if 'file' in x):
            self._songList.append(song)
            album = song.get('album', 'None')
            appendToList(self._albums, album, song)
            artist = _getField(song, ('artist', 'performer', 'composer'), 'Unknown')
            appendToList(self._artists, artist, song)
            genre = song.get('genre', None)
            if genre:
                appendToList(self._genres, genre, song)

            # Build the file system tree.
            fslist = self._filesystem
            path = song['file'].split('/')
            while path:
                part = path.pop(0)
                if path == []:
                    fslist[part] = song
                else:
                    fslist[part] = fslist.get(part, {})
                    fslist = fslist[part]

    def artists(self):
        '''Returns a list containing all artists in the library.'''
        return [Artist(value, self) for value in self._artists.keys()]

    def albums(self):
        '''Returns a list containing all albums in the library.'''
        return [Album(album, self) for album in self._albums.keys()]

    def songs(self):
        '''Returns a list containing all songs in the library.'''
        return [Song(song, self) for song in self._songList]

    def genres(self):
        '''Returns a list containing all genres in the library.'''
        return [Genre(genre, self) for genre in self._genres.keys()]

    def artistSongs(self, artist):
        '''Returns a list containing all songs from the supplied artist.'''
        return [Song(song, self) for song in self._artists.get(artist, [])]

    def artistAlbums(self, artist):
        '''Returns a list containing all albums the artist is listed on.'''
        albums = set()
        for song in self.artistSongs(artist):
            albums.update(song.album.all())
        return [Album(album, self) for album in albums]

    def artistGenres(self, artist):
        '''Returns a list containing all genres listed in songs by the given artist.'''
        genres = set()
        for song in self.artistSongs(artist):
            genres.update(song.genre.all())
        return [Genre(genre, self) for genre in genres]

    def albumSongs(self, album, artists=[]):
        '''Returns a list containing all songs on the supplied album title.
        The optional artist argument can be used to only get the songs of a particular artist or list of artists.'''
        if type(artists) in (str, unicode):
            artists = [artists]
        songs = (Song(song, self) for song in self._albums.get(album, []))
        if artists != []:
            songs = [song for song in songs if song.artist in artists]
        return songs

    def albumArtists(self, album):
        '''Returns a list containing all artists listed on the album.'''
        artists = set()
        for song in self.albumSongs(album):
            artists.update(song.artist.all())
        return [Artist(artist, self) for artist in artists]

    def albumGenres(self, album):
        '''Returns a list containing all genres listed in songs on the given album.'''
        genres = set()
        for song in self.albumSongs(album):
            genres.update(song.genre.all())
        return [Genre(genre, self) for genre in genres]

    def genreSongs(self, genre):
        '''Returns a list containing all songs in the given genre.'''
        return [Song(song, self) for song in self._genres.get(genre.lower(), [])]

    def genreArtists(self, genre):
        '''Returns a list containing all artists in the given genre.'''
        artists = set()
        for song in self.genreSongs(genre):
            artists.update(song.artist.all())
        return [Artist(artist, self) for artist in artists]

    def genreAlbums(self, genre):
        '''Returns a list containing all albums in the given genre.'''
        albums = set()
        for song in self.genreSongs(genre):
            albums.update(song.album.all())
        return [Album(album, self) for album in albums]

    def ls(self, path, fslist=None):
        '''Returns a list of songs and directories contained in the given path.'''
        if path.startswith('/'):
            path = path[1:]
        if fslist is None:
            fslist = self._filesystem
        part, sep, path = path.partition('/')
        if part == '':
            if type(fslist.get('file', None)) in (str, unicode):
                #return Song(self, fslist)
                return fslist
            else:
                #return [Dir(self, path) for path in fslist.keys()]
                return fslist.keys()
        fslist = fslist.get(part, {})
        return self.ls(path, fslist)

    def attributes(self, path):
        '''Returns whether path is a directory or a song file.'''
        if path.startswith('/'):
            path = path[1:]
        fslist = self._filesystem
        for part in path.split('/'):
            if part:
                fslist = fslist[part]
        if fslist.get('file', None) == path:
            return 'file'
        else:
            return 'directory'


def _getField(song, fields, alt):
    value = alt
    if ('artist' in fields or 'title' in fields) and song['file'].startswith('http://'):
        # mpd puts stream metadata in the title attribute as "{artist} - {song}"
        value = song.get('title', '')
        if ' - ' in value:
            artist, title = value.split(' - ', 1)
            if 'artist' in fields:
                value = artist
            if 'title' in fields:
                value = title
    else:
        for field in fields:
            if field in song:
                value = song[field]
                break
    if getattr(value, '__iter__', False):
        return value[0].strip()
    else:
        return value.strip()

def appendToList(listDict, keys, value, deduplicate=False):
    '''In place add value to listDict at key.
    If any of them are lists the values in those lists are used as value and
    key. Everything gets added to everything. The optional deduplicate makes
    appendToList only add values that are not yet in the list.
    '''
    if type(value) != list:
        value = [value]
    if type(keys) != list:
        keys = [keys]
    for key in keys:
        part = listDict.get(key, [])
        if deduplicate:
            # filter all that are already in there.
            value = [x for x in value if x not in part]
        listDict[key] = part + value



class LibraryObject(object):
    def __new__(cls, value, library):
        if not value:
            value = ''
        if getattr(value, '__iter__', False):
            string = value[0]
        else:
            string = value
        return unicode.__new__(cls, string)

    def __init__(self, value, library):
        self._attributes = {}
        self._library = library
        self._value = value

    def all(self):
        if type(self._value) in (str, unicode):
            return [self._value]
        else:
            return self._value

    def __getattr__(self, attr):
        try:
            funt = self._attributes[attr]
            return funt(self)
        except KeyError:
            raise AttributeError("LibraryObject '%s' has no attribute '%s'"
                    % (self.__class__.__name__, attr))


class Artist(LibraryObject, unicode):
    def __init__(self, value, library):
        LibraryObject.__init__(self, value, library)
        if library:
            self._attributes.update({
                    'songs':    library.artistSongs,
                    'albums':   library.artistAlbums,
                    'genres':   library.artistGenres,
                    })

class Album(LibraryObject, unicode):
    def __init__(self, value, library):
        LibraryObject.__init__(self, value, library)
        if library:
            self._attributes.update({
                    'songs':    library.albumSongs,
                    'artists':  library.albumArtists,
                    'genres':   library.albumGenres,
                    })

class Genre(LibraryObject, unicode):
    def __init__(self, value, library):
        LibraryObject.__init__(self, value, library)
        if library:
            self._attributes.update({
                    'songs':    library.genreSongs,
                    'artists':  library.genreArtists,
                    'albums':   library.genreAlbums,
                    })

class Time(LibraryObject, int):
    def __new__(cls, value, library=None):
        return int.__new__(cls, value)

    def __init__(self, value, library=None):
        LibraryObject.__init__(self, value, library)
        self._value = int(value)
        self._attributes.update({
                'hours':    lambda value: value / 3600,
                'minutes':  lambda value: (value - (value * 3600)) / 60,
                'seconds':  lambda value: value - ((value - (value / 3600 * 3600)) / 60 * 60),
                'human':    self._format,
                })

    def _format(self, time):
        thour = time / 3600
        time -= thour * 3600
        tmin = time / 60
        tsec = time - tmin * 60
        if thour > 0:
            return '%i:%02i:%02i' % (thour, tmin, tsec)
        return '%i:%02i' % (tmin, tsec)


class Text(LibraryObject, unicode):
    def __new__(cls, value, library=None):
        return LibraryObject.__new__(cls, value, library)

    def __init__(self, value, library=None):
        LibraryObject.__init__(self, value, library)

class Song(dict, LibraryObject):
    def __init__(self, value, library):
        dict.__init__(self, value)
        LibraryObject.__init__(self, self, library)
        self._attributes.update({
            'isStream': lambda _: self.file.startswith('http://'),
            'track':    lambda _: ''
            })

    def __getattr__(self, attr):
        try:
            return self.__getitem__(attr)
        except KeyError:
            return LibraryObject.__getattr__(self, attr)

    def __contains__(self, key):
        try:
            self.__getitem__(key)
            return True
        except KeyError:
            return False

    def get(self, key, alt=None):
        try:
            value = self.__getitem__(key)
            if value == '':
                value = value.__class__(alt, value._library)
        except KeyError:
            value = alt
        return value

    def __getitem__(self, item):
        if item == 'artist':
            return Artist(self._getAttr('artist', 'performer', 'composer'),
                    self._library)
        elif item == 'title':
            return Text(self._getAttr('title', 'name', 'file'),
                    self._library)
        elif item == 'album':
            return Album(self._getAttr('album'),
                    self._library)
        elif item == 'genre':
            value = self._getAttr('genre')
            if type(value) != list:
                value = [value]
            return Genre([x.lower() for x in value if type(value) in (str, unicode)],
                    self._library)
        elif item == 'file':
            return File(self._getAttr('file'),
                    self._library)
        elif item == 'time':
            return Time(self._getAttr('time') or 0,
                    self._library)
        elif item == 'station':
            # Only applicable when the Song object
            # is created from a play queue item.
            if self.isStream:
                return Text(self._getAttr('name', 'file'),
                    self._library)
            else:
                return Text('', self._library)
        else:
            value = self._getAttr(item)
            if value is None:
                raise KeyError
            return Text(value, self._library)

    def _getAttr(self, *attrs):
        '''Returns the value for the first key in attrs that exists.'''
        value = None
        if ('artist' in attrs or 'title' in attrs) and self.isStream:
            # mpd puts stream metadata in the title attribute as "{artist} - {song}"
            value = dict.get(self, 'title', '')
            if ' - ' in value:
                artist, title = value.split(' - ', 1)
                if 'artist' in attrs:
                    value = artist
                if 'title' in attrs:
                    value = title
        else:
            for attr in attrs:
                if dict.__contains__(self, attr):
                    value = dict.__getitem__(self, attr)
                    break
        return value.strip() if type(value) in (str, unicode) else value


class Path(unicode, LibraryObject):
    def __new__(cls, value, library=None):
        return unicode.__new__(cls, value)

    def __init__(self, value, library):
        LibraryObject.__init__(self, value, library)
        if isinstance(value, Dir):
            self._parent = value

    def parent(self):
        return self._parent.parent() + self._parent

class File(Path):
    def dir(self):
        return Dir(self.rsplit('/', 1)[0],
                self._library)

class Dir(Path):
    def ls(self):
        return self._library.ls(self)


