import threading
import cv2
import os
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from utils.timer import Timer
import datetime

import time


class VideoManager:
    def __init__(self, app):
        self.app = app
        self.selectedCamera = StringVar()
        self.invertVideo = BooleanVar(False)

    def startVideoStream(self, cameraId):
        if(hasattr(self, 'videoStream')):
            self.videoStream.disconnect()
        self.selectedCamera.set(cameraId)
        self.videoStream = self.VideoStream(
            self.app, cameraId, self.invertVideo)

    def disconnectVideoStream(self):
        self.selectedCamera.set('')
        if(hasattr(self, 'videoStream')):
            self.videoStream.disconnect()
            del self.videoStream

    def takeSnapshot(self):
        self.videoStream.snapshot()

    def startRecording(self):
        self.videoStream.startRecording()

    def stopRecording(self):
        self.videoStream.stopRecording()

    def toggleInvertVideo(self):
        if(hasattr(self, 'videoStream')):
            self.invertVideo.set(not self.invertVideo.get())

    def setupMenu(self):
        subMenu = Menu(self.app.menu, tearoff=0,
                       postcommand=lambda: self.updateMenu(subMenu))
        self.app.menu.add_cascade(label="Camera", menu=subMenu)

        camerasMenu = Menu(subMenu, tearoff=0)
        for cameraId in self.listCameras():
            camerasMenu.add_radiobutton(label=cameraId, value=cameraId, variable=self.selectedCamera,
                                        command=lambda cameraId=cameraId: self.startVideoStream(cameraId))
        subMenu.add_cascade(label="Select Capture Device", menu=camerasMenu)

        subMenu.add_separator()
        subMenu.add_command(label="Take Snapshot",
                            command=self.takeSnapshot, state="disabled")
        subMenu.add_command(label="Record Video",
                            command=self.startRecording, state="disabled")

        subMenu.add_separator()
        self.inverVideoButton = subMenu.add_checkbutton(label="Invert Video", variable=self.invertVideo,
                                                        command=self.toggleInvertVideo, state="disabled")
        subMenu.add_command(label="Disconnect",
                            command=self.disconnectVideoStream, state="disabled")

    def listCameras(self):
        index = 0
        arr = []

        while True:
            cap = cv2.VideoCapture(index)
            if not cap.read()[0]:
                break
            else:
                arr.append(index)
            cap.release()
            index += 1

        return arr

    def updateMenu(self, menu):
        if(hasattr(self, 'videoStream')):
            menu.entryconfig("Disconnect", state="normal")
            menu.entryconfig("Invert Video", state="normal")
            menu.entryconfig("Take Snapshot", state="normal")

            # if(self.videoStream.invertVideo):
            #     menu.entryconfig("Invert Video", state="disabled",
            #                      variable=self.videoStream.invertVideo)

            if(hasattr(self.videoStream, 'recording')):
                menu.entryconfig(3, label="Stop Recording",
                                 command=self.stopRecording, state="normal")
            else:
                menu.entryconfig(3, label="Record Video",
                                 command=self.startRecording, state="normal")
        else:
            false = False
            menu.entryconfig("Disconnect", state="disabled")
            # menu.entryconfig("Invert Video", variable=false)
            # menu.entryconfig("Invert Video", state="disabled")
            menu.entryconfig("Take Snapshot", state="disabled")
            menu.entryconfig(3, label="Record Video", state="disabled")

    class VideoStream(threading.Thread):
        def __init__(self, app, cameraId, invertVideo):
            threading.Thread.__init__(self)
            self.app = app
            self.cameraId = cameraId
            self.invertVideo = invertVideo

            self.daemon = True
            self.stopEvent = threading.Event()

            self.start()

        def run(self):
            self.cap = cv2.VideoCapture(self.cameraId)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 10000)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 10000)

            # keep looping over frames until we are instructed to stop
            while not self.stopEvent.isSet():
                start_time = time.time()

                ok, self.frame = self.cap.read()

                if ok:
                    if(hasattr(self, 'recording') and not self.recording.isPaused):
                        self.recording.fileWrite.write(self.frame)

                    xMultiplier = self.app.xCanvas / \
                        self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    yMultiplier = self.app.yCanvas / \
                        self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    minMultiplier = min(xMultiplier, yMultiplier)
                    width = int(minMultiplier *
                                self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(minMultiplier *
                                 self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                    image = cv2.resize(self.frame, (width, height))
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    if(self.invertVideo.get()):
                        image = cv2.flip(image, 1)
                    image = Image.fromarray(image)
                    image = ImageTk.PhotoImage(image)

                    if (not self.stopEvent.isSet() and (not hasattr(self, 'backgroundImage') or self.backgroundImage not in self.app.canvas.find_all())):
                        self.backgroundImage = self.app.canvas.create_image(
                            self.app.xCanvas/2, self.app.yCanvas/2)
                        self.app.canvas.tag_lower(self.backgroundImage)
                        self.setupRecordingInterface()

                    self.app.canvas.itemconfig(
                        self.backgroundImage, image=image)
                    self.app.canvas.image = image

                    self.fps = 1.0 / (time.time() - start_time)

        def recenterImage(self):
            self.app.canvas.delete(self.backgroundImage)

        # def toggleInvertVideo(self):
        #     self.invertVideo = not self.invertVideo

        def disconnect(self):
            if(hasattr(self, 'recording')):
                self.recording.end()

            self.stopEvent.set()
            self.cameraId = ''
            self.cap.release()

            if(hasattr(self, 'backgroundImage')):
                self.app.canvas.delete(self.backgroundImage)
                self.app.canvas.delete(self.recButton['button'])
                self.app.canvas.delete(self.pauseButton['button'])

        def snapshot(self):
            """ Take snapshot and save it to the file """
            ts = datetime.datetime.now()  # grab the current timestamp
            filename = "{}.png".format(ts.strftime(
                "%Y-%m-%d_%H-%M-%S"))  # construct filename

            ok, frame = self.cap.read()
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)

            # save image as jpeg file
            image.save('exports/snapshots/' + filename, "PNG")
            print("[INFO] saved {}".format(filename))

        class VideoCapture:
            def __init__(self, app, resolution, fps):
                self.app = app

                ts = datetime.datetime.now()  # grab the current timestamp
                filename = "exports/videos/{}.mp4".format(ts.strftime(
                    "%Y-%m-%d_%H-%M-%S"))
                codec = cv2.VideoWriter_fourcc(*'mp4v')
                self.fileWrite = cv2.VideoWriter(
                    filename, codec, fps, resolution)

                self.isPaused = False
                self.timer = Timer()

                self.timeCounter = self.app.canvas.create_text(
                    150, self.app.yCanvas - 40, fill="white", font="Times 15", text=self.timer.stringVar.get())
                self.timer.stringVar.trace_variable('w', self.onTimerUpdate)

            def onTimerUpdate(self, varname, index, mode):
                if(self.timeCounter in self.app.canvas.find_all()):
                    self.app.canvas.itemconfigure(
                        self.timeCounter, text=self.timer.stringVar.get())

            def end(self):
                self.timer.stop()
                self.app.canvas.delete(self.timeCounter)
                self.fileWrite.release()

            def pause(self):
                self.isPaused = True
                self.timer.pause()

            def resume(self):
                self.isPaused = False
                self.timer.resume()

        def setupRecordingInterface(self):
            if(hasattr(self, 'recButton') and self.recButton not in self.app.canvas.find_all()):
                self.app.canvas.delete(self.recButton)
            self.recButton = self.loadButton(
                'assets/rec.png', 'assets/stop.png', self.startRecording, self.stopRecording, 40, self.app.yCanvas - 40)
            self.switchButtonState(self.recButton, hasattr(self, 'recording'))

            if(hasattr(self, 'pauseButton') and self.pauseButton not in self.app.canvas.find_all()):
                self.app.canvas.delete(self.pauseButton)
            self.pauseButton = self.loadButton(
                'assets/play.png', 'assets/pause.png', self.resumeRecording, self.pauseRecording, 85, self.app.yCanvas - 40)
            self.switchButtonState(self.pauseButton, hasattr(
                self, 'recording') and not self.recording.isPaused)

            if(hasattr(self, 'recording') and hasattr(self.recording, 'timeCounter') and self.recording.timeCounter not in self.app.canvas.find_all()):
                self.app.canvas.delete(self.recording.timeCounter)
                self.recording.timeCounter = self.app.canvas.create_text(
                    150, self.app.yCanvas - 40, fill="white", font="Times 15", text=self.recording.timer.stringVar.get())

        def loadButton(self, image0, image1, command0, command1, x, y):
            buttonObject = {
                'state': '',
                'image0': ImageTk.PhotoImage(file=image0),
                'image1': ImageTk.PhotoImage(file=image1),
                'command0': command0,
                'command1': command1,
                'button': self.app.canvas.create_image(x, y)
            }
            self.app.canvas.itemconfig(
                buttonObject['button'], image=buttonObject['image0'])
            self.app.canvas.tag_bind(
                buttonObject['button'], '<Button-1>', lambda event: buttonObject['command0']())

            return buttonObject

        def switchButtonState(self, buttonObject, condition):
            if(condition):
                self.app.canvas.itemconfig(
                    buttonObject['button'], image=buttonObject['image1'])
                self.app.canvas.tag_bind(
                    buttonObject['button'], '<Button-1>', lambda event: buttonObject['command1']())
            else:
                self.app.canvas.itemconfig(
                    buttonObject['button'], image=buttonObject['image0'])
                self.app.canvas.tag_bind(
                    buttonObject['button'], '<Button-1>', lambda event: buttonObject['command0']())

        def startRecording(self):
            if(not hasattr(self, 'recording')):
                self.recording = self.VideoCapture(self.app, (int(self.cap.get(
                    cv2.CAP_PROP_FRAME_WIDTH)), int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))), self.fps)
                self.switchButtonState(
                    self.recButton, hasattr(self, 'recording'))
                self.switchButtonState(self.pauseButton, hasattr(
                    self, 'recording') and not self.recording.isPaused)

        def stopRecording(self):
            if(hasattr(self, 'recording')):
                self.recording.end()
                del self.recording
                self.switchButtonState(
                    self.recButton, hasattr(self, 'recording'))
                self.switchButtonState(self.pauseButton, hasattr(
                    self, 'recording') and not self.recording.isPaused)

        def pauseRecording(self):
            if(hasattr(self, 'recording')):
                self.recording.pause()
                self.switchButtonState(self.pauseButton, hasattr(
                    self, 'recording') and not self.recording.isPaused)

        def resumeRecording(self):
            if(hasattr(self, 'recording')):
                self.recording.resume()
                self.switchButtonState(self.pauseButton, hasattr(
                    self, 'recording') and not self.recording.isPaused)
