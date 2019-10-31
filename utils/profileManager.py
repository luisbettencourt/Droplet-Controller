import os
import copy
import pickle
from tkinter import *
from tkinter import ttk, filedialog
from svg.path import parse_path
from xml.dom import minidom
from utils.dialog import CustomDialog


class ProfileManager:
    def __init__(self, boardManager, videoManager, app):
        self.selectedProfileName = StringVar()
        self.boardManager = boardManager
        self.videoManager = videoManager
        self.app = app
        self.readProfileCache()

        self.showChannels = False

    def setupMenu(self):
        subMenu = Menu(self.app.menu, tearoff=0)
        self.app.menu.add_cascade(label="File", menu=subMenu)
        subMenu.add_command(label="New Profile", command=self.newProfile)
        subMenu.add_command(label="Import Layout", command=self.openFile)
        subMenu.add_separator()
        loadMenu = Menu(
            subMenu, postcommand=lambda: self.updateProfileList(loadMenu), tearoff=0)
        loadMenu.commands = []
        subMenu.add_cascade(label="Load Profile", menu=loadMenu)
        subMenu.add_command(label="Save Profile",
                            command=lambda: self.saveProfile(False))
        subMenu.add_command(label="Save Profile as...",
                            command=lambda: self.saveProfile(True))
        subMenu.add_command(label="Delete Profile",
                            command=self.deleteProfile)
        subMenu.add_separator()
        subMenu.add_checkbutton(label='Show Channels',
                                command=self.toggleChannels)
        subMenu.add_command(label="Exit",
                            command=self.app.close)

    def newProfile(self):
        self.app.canvas.delete("all")
        self.selectedProfileName.set('')
        self.profile = {}
        self.updateProfileCache('')

    def openFile(self):
        filePath = filedialog.askopenfilename(
            initialdir="/", title="Select file", filetypes=(("svg files", "*.svg"),))

        if(filePath):
            doc = minidom.parse(filePath)
            self.profile = self.Profile(doc)
            self.drawProfile()

    def drawProfile(self):
        if(hasattr(self, 'profile')):
            self.app.canvas.delete("all")

            xMultiplier = self.app.xCanvas/self.profile.svg.xLength * 0.8
            yMultiplier = self.app.yCanvas/self.profile.svg.yLength * 0.8
            minMultiplier = min(xMultiplier, yMultiplier)
            xPadding = max(0, (xMultiplier - minMultiplier))/2
            yPadding = max(0, (yMultiplier - minMultiplier))/2

            for pathObject in self.profile.svg.pathObjects:
                self.app.canvas.delete(pathObject.obj)
                polygonCoordinates = []
                for pathCommand in pathObject.pathCommands:
                    polygonCoordinates.append([pathCommand.x0 * self.profile.svg.xLength * minMultiplier + self.profile.svg.xLength * xPadding + self.app.xCanvas *
                                               0.1, pathCommand.y0 * self.profile.svg.yLength * minMultiplier + self.profile.svg.yLength * yPadding + self.app.yCanvas * 0.1])

                pathObject.obj = self.app.canvas.create_polygon(
                    polygonCoordinates, fill="", outline='', width=2)
                self.setObjectColor(pathObject)

                self.app.canvas.tag_bind(pathObject.obj, '<Button-1>', lambda event,
                                         pathObject=pathObject: self.onObjectClick(pathObject))
                self.app.canvas.tag_bind(pathObject.obj, '<Button-3>', lambda event,
                                         pathObject=pathObject: self.setChannel(pathObject))

            if(hasattr(self, 'showChannels') and self.showChannels):
                self.drawObjectChannels()

    def setObjectColor(self, pathObject):
        if(hasattr(self.boardManager, 'board') and hasattr(self.boardManager.board, 'connection') and isinstance(pathObject.channel, int) and self.boardManager.board.connection.digital[pathObject.channel].read()):
            self.app.canvas.itemconfig(pathObject.obj, outline='red')
            self.app.canvas.tag_raise(pathObject.obj)
        else:
            self.app.canvas.itemconfig(pathObject.obj, outline='blue')
            self.app.canvas.tag_lower(pathObject.obj)
            if(hasattr(self.videoManager, 'videoStream') and hasattr(self.videoManager.videoStream, 'backgroundImage')):
                self.app.canvas.tag_lower(
                    self.videoManager.videoStream.backgroundImage)

    def drawObjectChannels(self):
        if(self.showChannels):
            self.app.xCanvas = self.app.canvas.winfo_width()
            self.app.yCanvas = self.app.canvas.winfo_height()

            xMultiplier = self.app.xCanvas/self.profile.svg.xLength * 0.8
            yMultiplier = self.app.yCanvas/self.profile.svg.yLength * 0.8
            minMultiplier = min(xMultiplier, yMultiplier)
            xPadding = max(0, (xMultiplier - minMultiplier))/2
            yPadding = max(0, (yMultiplier - minMultiplier))/2

            for pathObject in self.profile.svg.pathObjects:
                polygonCoordinates = self.app.canvas.coords(pathObject.obj)
                xCoordinates = []
                yCoordinates = []
                for x, y in zip(polygonCoordinates[0::2], polygonCoordinates[1::2]):
                    xCoordinates.append(x)
                    yCoordinates.append(y)

                xPosition = (max(xCoordinates) - min(xCoordinates)) / \
                    2 + min(xCoordinates)
                yPosition = (max(yCoordinates) - min(yCoordinates)) / \
                    2 + min(yCoordinates)

                obj = self.app.canvas.create_text((
                    xPosition, yPosition), fill="white", text=pathObject.channel)
                pathObject.channelText = obj

        else:
            for pathObject in self.profile.svg.pathObjects:
                self.app.canvas.delete(pathObject.channelText)

    def toggleChannels(self):
        self.showChannels = not self.showChannels
        print(self.showChannels)
        self.drawObjectChannels()

    def saveProfile(self, askName):
        if(self.profile.name == "" or askName):
            self.profile.name = CustomDialog(
                self.app.root, "Profile Name:", "If a profile with the same name exists, it will be overwritten.", self.profile.name).show()
        if(self.profile.name):
            self.selectedProfileName.set(self.profile.name)
            with open('profiles/' + self.profile.name + '.pkl', 'wb') as output:
                pickle.dump(self.profile, output)
                self.updateProfileCache(self.profile.name)

    def listProfiles(self):
        profileList = [
            file.split('.')[0]
            for file in os.listdir("profiles")
            if file.endswith(".pkl")
        ]
        return profileList

    def updateProfileList(self, menu):
        profilesList = self.listProfiles()

        for i, command in enumerate(menu.commands):
            if(command not in profilesList):
                menu.delete(i)
                menu.commands.remove(command)

        if(len(profilesList) > 0):
            for profile in profilesList:
                if(profile not in menu.commands):
                    menu.add_radiobutton(label=profile, value=profile, variable=self.selectedProfileName,
                                         command=lambda profile=profile: self.loadProfile(profile))
                    menu.commands.append(profile)
        else:
            menu.add_command(label="No Profiles Available")
            menu.commands.append("No Profiles Available")

    def loadProfile(self, fileName):
        if fileName and os.path.isfile('profiles/' + fileName + '.pkl') and os.path.getsize('profiles/' + fileName + '.pkl') > 0:
            with open('profiles/' + fileName + '.pkl', 'rb') as output:
                profile = pickle.load(output)
                self.profile = profile
            if(self.profile):
                self.selectedProfileName.set(self.profile.name)
                self.drawProfile()
                self.updateProfileCache(self.profile.name)

    def updateProfileCache(self, profileName):
        with open('profiles/cache.txt', 'w') as file:
            file.write(profileName)

    def readProfileCache(self):
        if os.path.isfile('profiles/cache.txt'):
            with open('profiles/cache.txt') as file:
                profileList = self.listProfiles()
                cachedProfile = file.read()
                if cachedProfile in profileList:
                    self.loadProfile(cachedProfile)

    def deleteProfile(self):
        if self.profile.name and os.path.isfile('profiles/' + self.profile.name + '.pkl'):
            os.remove('profiles/' + self.profile.name + '.pkl')
            self.newProfile()

    def setChannel(self, pathObject):
        channel = CustomDialog(self.app.root, "Channel:", "Available Pins: " + str(
            self.availablePins(self.boardManager.board.connection._layout)), pathObject.channel).show()
        if(channel):
            pathObject.channel = int(channel)

    def availablePins(self, layout):
        return list(filter(lambda x: x not in layout['disabled'], layout['digital']))

    def onObjectClick(self, pathObject):
        if(pathObject.channel is None):
            self.setChannel(pathObject)
        elif(hasattr(self.boardManager.board, 'connection')):
            if(self.boardManager.board.connection.digital[pathObject.channel].read()):
                self.boardManager.board.connection.digital[pathObject.channel].write(
                    0)
                self.setObjectColor(pathObject)
            else:
                self.boardManager.board.connection.digital[pathObject.channel].write(
                    1)
                self.setObjectColor(pathObject)
        else:
            print('no board!')

    class Profile:
        def __init__(self, doc):
            if(not hasattr(self, 'name')):
                self.name = ''
            self.svg = self.Svg(doc)

        class Svg:
            def __init__(self, doc):
                self.processDocument(doc)

            def processDocument(self, doc):
                path_strings = [path.getAttribute('d') for path
                                in doc.getElementsByTagName('path')]
                doc.unlink()

                self.pathObjects = []
                for path_string in path_strings:
                    pathString = parse_path(path_string)

                    pathCommands = []
                    for path in pathString:
                        if type(path).__name__ == 'Line':
                            x0 = path.start.real
                            y0 = path.start.imag
                            x1 = path.end.real
                            y1 = path.end.imag
                            pathCommands.append(
                                self.PathObject.PathCommand(x0, y0, x1, y1))

                    self.pathObjects.append(
                        self.PathObject(pathString, pathCommands))

                allPathCommands = list(
                    self.flatten([pathObject.pathCommands for pathObject in self.pathObjects]))
                self.x00 = min(allPathCommands, key=lambda x: x.x0).x0
                self.y00 = min(allPathCommands, key=lambda x: x.y0).y0
                self.x11 = max(allPathCommands, key=lambda x: x.x1).x1
                self.y11 = max(allPathCommands, key=lambda x: x.y1).y1

                self.xLength = self.x11 - self.x00
                self.yLength = self.y11 - self.y00

                for pathObject in self.pathObjects:
                    for pathCommand in pathObject.pathCommands:
                        pathCommand.x0 = (pathCommand.x0 - self.x00) / \
                            (self.x11 - self.x00)
                        pathCommand.y0 = (pathCommand.y0 - self.y00) / \
                            (self.y11 - self.y00)
                        pathCommand.x1 = (pathCommand.x1 - self.x00) / \
                            (self.x11 - self.x00)
                        pathCommand.y1 = (pathCommand.y1 - self.y00) / \
                            (self.y11 - self.y00)

            def flatten(self, list):
                for i in list:
                    for j in i:
                        yield j

            class PathObject:
                def __init__(self, pathString, pathCommands, obj=None, channel=None):
                    self.pathString = pathString
                    self.pathCommands = pathCommands
                    self.obj = obj
                    self.channel = channel

                class PathCommand:
                    def __init__(self, x0, y0, x1, y1):
                        self.x0 = x0
                        self.y0 = y0
                        self.x1 = x1
                        self.y1 = y1
