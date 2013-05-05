#!/usr/bin/env python2
# coding: UTF-8

#
# Douban FM GUI
#
import os
import sys
import urllib
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QPixmap, QIcon, QLabel, QWidgetAction
from PyQt4.QtCore import QSize
from PyQt4.phonon import Phonon
from ui.player import Ui_MainWindow, _fromUtf8
from lib.doubanfm import DoubanFM
from util import ms_to_hms

index_dir = os.path.dirname(os.path.abspath(__file__))
favicon = os.path.join(index_dir, 'ui/resources/doubanfm-0.xpm')

class GUIState:
    (Playing, Paused, Heart, Hearted) = range(4)

class DoubanFMGUI(QtGui.QMainWindow):
    def __init__(self, start_url=None, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow() 
        self.ui.setupUi(self)
        self.setup_player_ui()
        self.ui.seekSlider.setIconVisible(False)
        self.ui.volumeSlider.setMuteVisible(False)
        self.doubanfm = DoubanFM(start_url, debug=False)
        print self.doubanfm.username
        self.connect(self.ui.pushButtonHeart, QtCore.SIGNAL('clicked()'), self.heart_song)
        self.connect(self.ui.pushButtonTrash, QtCore.SIGNAL('clicked()'), self.trash_song)
        self.connect(self.ui.pushButtonSkip, QtCore.SIGNAL('clicked()'), self.skip_song)
        self.connect(self.ui.pushButtonToggle, QtCore.SIGNAL('clicked()'), self.play_toggle)

        self.next_song()

    def setup_player_ui(self):
        # Setup phonon player
        self.mediaObject = Phonon.MediaObject(self)
        self.mediaObject.setTickInterval(100)
        self.mediaObject.tick.connect(self.tick)
        #self.mediaObject.finished.connect(self.finished)
        self.mediaObject.stateChanged.connect(self.catchStateChanged)
        #self.mediaObject.totalTimeChanged.connect(self.totalTime)

        # bind AudioOutput with MediaObject
        self.audioOutput = Phonon.AudioOutput(Phonon.MusicCategory, self)
        Phonon.createPath(self.mediaObject, self.audioOutput)

        # Setup the seek slider
        self.ui.seekSlider.setMediaObject(self.mediaObject)

        # Setup the volume slider
        self.ui.volumeSlider.setAudioOutput(self.audioOutput)

    def set_ui_state(self, state):
        #TODO: refactor
        if state == GUIState.Playing:
            self.ui.pushButtonToggle.setStyleSheet(_fromUtf8("background: url(:/player/pause.png) no-repeat center;\nborder: none;\n outline: none;\n background-color: '#9dd6c5';"))
        elif state == GUIState.Paused:
            self.ui.pushButtonToggle.setStyleSheet(_fromUtf8("background: url(:/player/play.png) no-repeat center;\nborder: none;\n outline: none;\n background-color: '#9dd6c5';"))
        elif state == GUIState.Heart:
            self.ui.pushButtonHeart.setStyleSheet('border-image: url(:/player/heart.png);\nborder: none;\noutline: none;')
        elif state == GUIState.Hearted:
            self.ui.pushButtonHeart.setStyleSheet('border-image: url(:/player/hearted.png);\nborder: none;\noutline: none;')

    def tick(self, time):
        h, m, s = ms_to_hms(time)
        self.ui.timeLabel.setText('%02d:%02d:%02d' %(h, m, s))

    def catchStateChanged(self, new_state, old_state):
        #http://harmattan-dev.nokia.com/docs/library/html/qt4/phonon.html
        if new_state == Phonon.PlayingState:
            self.set_ui_state(GUIState.Playing)
        elif new_state == Phonon.PausedState:
            self.set_ui_state(GUIState.Paused)
        elif new_state == Phonon.StoppedState:
            print 'stopped state!!!!!!!!! old_state', old_state
            self.next_song()
        elif new_state == Phonon.ErrorState:
            print('Error playing back file')
            #self.quit()
        print 'new_state:', new_state

    def play_song(self):
        song = self.doubanfm.current_song
        url = song.get('url')
        self.ui.labelAlbum.setText(u'<{0}> {1}'.format(song.get('albumtitle'), song.get('public_time')))
        self.ui.labelTitle.setText(song.get('title'))
        self.ui.labelTitle.setToolTip(song.get('title'))
        self.ui.labelArtist.setText(song.get('artist'))
        if int(song.get('like')) != 0:
            self.set_ui_state(GUIState.Hearted)
        else:
            self.set_ui_state(GUIState.Heart)

        self.ui.debug.setText(str(song))
        self.mediaObject.setCurrentSource(Phonon.MediaSource(url))
        self.mediaObject.play()
        urllib.urlretrieve(song.get('picture').replace('mpic', 'lpic'),'/tmp/cover.jpg')
        cover = QIcon('/tmp/cover.jpg')# TODO refactor
        self.ui.pushButtonCover.setIcon(cover)
        self.ui.pushButtonCover.setIconSize(QSize(200,200))

        
    def play_toggle(self):
        ns = self.mediaObject.state()
        if ns == Phonon.PlayingState:
            self.mediaObject.pause()
        elif ns == Phonon.PausedState:
            self.mediaObject.play()

    def heart_song(self):
        song = self.doubanfm.current_song
        if int(song.get('like')) != 0:
            self.set_ui_state(GUIState.Heart)
            self.doubanfm.unheart_song()
        else:
            self.set_ui_state(GUIState.Hearted)
            self.doubanfm.heart_song()
    
    def trash_song(self):
        self.doubanfm.trash_song()
        self.mediaObject.stop()

    def skip_song(self):
        song = self.doubanfm.skip_song()
        self.mediaObject.stop()

    def next_song(self):
        self.doubanfm.next_song()
        self.play_song()

    def __del__(self):
        self.mediaObject.stop()
        

class SystemTrayIcon(QtGui.QSystemTrayIcon):
    def __init__(self, parent=None):
        QtGui.QSystemTrayIcon.__init__(self, parent)

        self.setIcon(QtGui.QIcon(favicon))

        start_url = None
        if len(sys.argv) >= 2:
            start_url = sys.argv[1]
        self.doubanfm_gui = DoubanFMGUI(start_url)

        self.leftMenu = QtGui.QMenu(parent)
        lqa=QWidgetAction(self.leftMenu)
        lqa.setDefaultWidget(self.doubanfm_gui)
        action=self.leftMenu.addAction(lqa)


        self.rightMenu = QtGui.QMenu(parent)
        username = self.doubanfm_gui.doubanfm.username
        print 'username:', username
        rqa = QWidgetAction(self.rightMenu)
        about = QLabel("{0} {1}".format('Douban FM GUI', '', 'by mckelvin'))

        rqa.setDefaultWidget(about);
        self.rightMenu.addAction(rqa)
        self.rightMenu.addAction(u'@{0}'.format((username or u'未登录')))
        appexit = self.rightMenu.addAction("Exit")
        self.connect(appexit,QtCore.SIGNAL('triggered()'),self.app_exit)

                
        self.setContextMenu(self.rightMenu)
        self.activated.connect(self.click_trap)

    def click_trap(self, value):
        if value == self.Trigger: #left click!
            self.leftMenu.exec_(QtGui.QCursor.pos())

    def app_exit(self):
        del self.doubanfm_gui
        app.quit()



if __name__ == "__main__":
    ''' 
    #start as a normal app
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName("Douban FM")
    doubanfm = DoubanFMGUI()
    doubanfm.show()
    sys.exit(app.exec_())
    '''
    # start as a tray bar app
    app = QtGui.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    w = QtGui.QWidget()
    trayIcon = SystemTrayIcon(w)
    trayIcon.show()
    sys.exit(app.exec_())
