import os
from tkinter import *

from utils.videoManager import VideoManager
from utils.profileManager import ProfileManager
from utils.boardManager import BoardManager
from utils.instrumentManager import InstrumentManager


class App():
    def __init__(self):
        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind('<Configure>', self.size)   # Hook window size changes
        self.root.title("Droplet Controller")
        self.setupInterface()

    def close(self):
        videoManager.disconnectVideoStream()
        boardManager.disconnectBoard()
        InstrumentManager.disconnect()
        self.root.quit()

    def size(self, event):
        self.xCanvas, self.yCanvas = self.canvas.winfo_width(), self.canvas.winfo_height()
        if(hasattr(profileManager, 'profile')):
            profileManager.drawProfile()
        if(hasattr(videoManager, 'videoStream')):
            videoManager.videoStream.recenterImage()

    def setupInterface(self):
        self.xCanvas = 1280
        self.yCanvas = 720
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.canvas = Canvas(self.root, width=self.xCanvas,
                             height=self.yCanvas, bg='black', highlightthickness=0)
        self.canvas.grid(sticky='nesw')

    def setupMenus(self):
        self.menu = Menu(self.root)
        self.root.config(menu=self.menu)
        profileManager.setupMenu()
        boardManager.setupMenu()
        videoManager.setupMenu()
        InstrumentManager.setupMenu()


def createDirectories(directories):
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)


if __name__ == "__main__":
    app = App()
    createDirectories(['profiles', 'exports/snapshots', 'exports/videos', 'exports/graphs', 'exports/data'])
    videoManager = VideoManager(app)
    boardManager = BoardManager(app)
    profileManager = ProfileManager(boardManager, videoManager, app)
    InstrumentManager = InstrumentManager(app)
    app.setupMenus()
    app.root.iconbitmap('assets/favicon.ico')
    app.root.mainloop()
