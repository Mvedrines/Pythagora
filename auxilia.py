# -*- coding: utf-8 -*
#-------------------------------------------------------------------------------
# Copyright 2009 E. A. Graham Jr. <txcrackers@gmail.com>.
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
import locale
import re
import sys
from PyQt4.QtCore import SIGNAL, QTimer
from PyQt4.QtGui import QAction, QTabBar, QIcon

try:
    if "--nokde" in sys.argv:
        raise ImportError
    from PyKDE4.kdeui import KIcon
    KDE = True
except ImportError:
    KDE = False

locale.setlocale(locale.LC_ALL, "")

def songTitle(song):
    value = song.get('title', song.get('name', song['file']))
    return _getTextField(value)

def songArtist(song, alt=''):
    value = song.get('artist', song.get('performer', song.get('composer', alt)))
    return _getTextField(value)

def songAlbum(song, alt=''):
    value = song.get('album', alt)
    return _getTextField(value)

def songTrack(song, alt=''):
    value = song.get('track', alt)
    return _getTextField(value)

def _getTextField(value):
    if getattr(value, '__iter__', False):
        return value[0]
    else:
        return value

def songTime(song):
    stime = int(song.get('time', '0'))
    thour = stime / 3600
    stime -= thour * 3600
    tmin = stime / 60
    tsec = stime - tmin * 60
    if thour > 0:
        return '%i:%02i:%02i' % (thour, tmin, tsec)
    return '%i:%02i' % (tmin, tsec)

def cmpUnicode(a, b):
    return locale.strcoll(a, b)#filter(lambda x: x.isalnum(), a), filter(lambda x: x.isalnum(), b))

def cmpTracks(a, b):
    try:
        return int(re.match('^\d+', a).group()) - int(re.match('^\d+', b).group())
    except:
        return cmpUnicode(a, b)

def fileName(name):
    return filter(lambda x: x != '/' , name)

# Actions
#==============================================================================

class Actions:
    def actionPlayAdd(self, parent, slot):
        return self.action(parent, slot\
                , "media-playback-start"\
                , 'Add and play'\
                , 'Add song to playlist and start playing it.')

    def actionPlayReplace(self, parent, slot):
        return self.action(parent, slot\
                , "media-playback-start"\
                , 'Replace and play'\
                , 'Replace the playlist with the selection and start playing.')

    def actionAddSongs(self, parent, slot):
        return self.action(parent, slot\
        , "list-add"\
        , 'Add to playlist'\
        , 'Add the selection to the playlist.')

    def actionJumpArtist(self, parent, slot):
        return self.action(parent, slot\
        , "go-jump"\
        , 'Jump to artist'\
        , 'Jump to all songs from the selected artist in the library.')

    def actionJumpAlbum(self, parent, slot):
        return self.action(parent, slot\
        , "go-jump"\
        , 'Jump to album'\
        , 'Jump to all songs from the selected album in the library.')

    def actionLoad(self, parent, slot):
        return self.action(parent, slot\
        , "document-send"\
        , 'Load playlist'\
        , 'Replace the current playlist.')

    def actionRemove(self, parent, slot):
        return self.action(parent, slot\
        , "list-remove"\
        , 'Remove'\
        , 'Remove selected.')

    def actionLibReload(self, parent, slot):
        return self.action(parent, slot\
        , 'view-refresh'\
        , 'Reload library'\
        , 'Reload the music library from the server.')

    def actionLibUpdate(self, parent, slot):
        return self.action(parent, slot\
        , 'folder-sync'\
        , 'Update library'\
        , 'Update the music database with new and changed files')

    def actionLibRescan(self, parent, slot):
        return self.action(parent, slot\
        , 'folder-sync'\
        , 'Rescan library'\
        , 'Rescan all files in the music directory.')

    def actionBookmark(self, parent, slot):
        return self.action(parent, slot\
        , 'document-save-as'\
        , 'Bookmark Station'\
        , 'Add the station to the bookmarks list.')

    def actionPreview(self, parent, slot):
        return self.action(parent, slot\
        , 'media-playback-start'\
        , 'Preview'\
        , 'Start listening to the station right away.')

    def actionPlayBM(self, parent, slot):
        return self.action(parent, slot\
        , 'media-playback-start'\
        , 'Play'\
        , 'Start listening to the station.')

    def actionScReload(self, parent, slot):
        return self.action(parent, slot\
        , 'view-refresh'\
        , 'Reload'\
        , 'Reload the genre list.')

    #def action(self, parent, slot):
    #    return self.action(parent, slot\
    #    , ''\
    #    , ''\
    #    , '')

    def action(self, parent, slot, icon=None, text='', tooltip=None):
        action = QAction(text, parent)
        if type(icon) == str:
            action.setIcon(PIcon(icon))
        if type(tooltip) == str:
            action.setToolTip(tooltip)
        self.__addAction(action, parent, slot)
        return action

    def __addAction(self, action, parent, slot):
        parent.addAction(action)
        self.connect(action, SIGNAL('triggered()'), slot)

def PIcon(icon):
    if KDE:
        return KIcon(icon)
    else:
        return QIcon('icons/%s.png' % icon)

class StatusTabBar(QTabBar):
    def __init__(self):
        QTabBar.__init__(self)
        self.tabTimer = QTimer()
        self.connect(self.tabTimer, SIGNAL('timeout()'), self.__selectTab)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        '''Starts timer on enter and sets first position.'''
        self.tabPos = event.pos()
        event.accept()
        self.tabTimer.start(500)

    def dragLeaveEvent(self, event):
        '''If the mouse leaves the tabWidget stop the timer.'''
        self.tabTimer.stop()

    def dragMoveEvent(self, event):
        '''Keep track of the mouse and change the position, restarts the timer when moved.'''
        tabPos = event.pos()
        moved = tabPos.manhattanLength() - self.tabPos.manhattanLength()
        if moved > 7 or moved < -7:
            self.tabTimer.start(500)
        self.tabPos = tabPos

    def __selectTab(self):
        '''Changes the view to the tab where the mouse was hovering above.'''
        index = self.tabAt(self.tabPos)
        self.setCurrentIndex(index)
        self.tabTimer.stop()

