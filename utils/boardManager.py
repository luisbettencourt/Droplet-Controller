import threading
from tkinter import *
import serial
import serial.tools.list_ports
from pyfirmata2 import ArduinoMega


class BoardManager(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.daemon = True

        self.selectedPort = StringVar()
        self.app = app

        self.start()

    def run(self):
        self.board = self.Board(self.selectedPort)

    def setupMenu(self):
        subMenu = Menu(self.app.menu, tearoff=0,
                       postcommand=lambda: self.updateMenu(subMenu))
        self.app.menu.add_cascade(label="Board", menu=subMenu)
        subMenu.add_command(label="Auto Detect",
                            command=lambda: self.loadBoard(None))
        portsMenu = Menu(
            subMenu, postcommand=lambda: self.updatePortsList(portsMenu), tearoff=0)
        portsMenu.commands = []
        subMenu.add_cascade(label="Select Port", menu=portsMenu)

        subMenu.add_separator()
        subMenu.add_command(label="Disconnect",
                            command=self.disconnectBoard, state="disabled")

    def updateMenu(self, menu):
        if(not self.selectedPort.get() == ''):
            menu.entryconfig("Disconnect", state="normal")
        else:
            menu.entryconfig("Disconnect", state="disabled")

    def listPorts(self):
        arduinoPorts = [
            p.device
            for p in serial.tools.list_ports.comports()
            if 'Arduino' in p.description  # may need tweaking to match new arduinos
        ]
        return arduinoPorts

    def updatePortsList(self, menu):
        portsList = self.listPorts()

        for i, command in enumerate(menu.commands):
            if(command not in portsList):
                menu.delete(i)
                menu.commands.remove(command)

        if(len(portsList) > 0):
            for port in portsList:
                if(port not in menu.commands):
                    menu.add_radiobutton(label=port, value=port, variable=self.selectedPort,
                                         command=lambda port=port: self.loadBoard(port))
                    menu.commands.append(port)
        else:
            menu.add_command(label="No Boards Available")
            menu.commands.append("No Boards Available")

    def loadBoard(self, port):
        if(not self.selectedPort.get() == port):
            self.board = self.Board(self.selectedPort, port)

    def disconnectBoard(self):
        if(hasattr(self, 'board')):
            self.selectedPort.set('')
            self.board.connection.exit()

    class Board:
        def __init__(self, selectedPort, port=None):
            if(port):
                self.connection = ArduinoMega(port)
            else:
                self.connection = ArduinoMega(ArduinoMega.AUTODETECT)
            selectedPort.set(self.connection.name)
