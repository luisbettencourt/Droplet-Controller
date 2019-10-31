import visa
import threading
import time
import datetime
import math
from tkinter import *
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pandas import DataFrame

from utils.timer import Timer

import random


class InstrumentManager:
    def __init__(self, app):
        self.app = app
        self.selectedPort = StringVar()
        self.selectedInstrument = StringVar()
        self.selectedInstrument.set('No Connected Device')

    def selectPort(self, port):
        self.measure = self.ImpedanceMeasure(
            self.app, port, self.selectedPort, self.selectedInstrument)

    def startMeasure(self):
        # if(not hasattr(self, 'measure')):
        #     self.measure = self.ImpedanceMeasure(
        #         self.app, 1, self.selectedPort, self.selectedInstrument)
        self.measure.openGraph()

    def disconnect(self):
        if(hasattr(self, 'measure')):
            self.measure.disconnectGPIB()
            del self.measure

    def saveGraph(self):
        self.measure.saveFig()

    def exportData(self):
        self.measure.exportData()

    def setupMenu(self):
        subMenu = Menu(self.app.menu, tearoff=0,
                       postcommand=lambda: self.updateMenu(subMenu))
        self.app.menu.add_cascade(label="Measure", menu=subMenu)

        subMenu.add_command()
        subMenu.add_separator()

        instrumentsMenu = Menu(subMenu, tearoff=0)
        for port in [i for i in range(1, 31)]:
            instrumentsMenu.add_radiobutton(
                label=port, value=port, variable=self.selectedPort, command=lambda port=port: self.selectPort(port))
        subMenu.add_cascade(label="Select Port",
                            menu=instrumentsMenu)

        subMenu.add_command(label="Start Measuring",
                            state="disabled",
                            command=self.startMeasure)

        subMenu.add_separator()

        subMenu.add_command(label="Save Measurement",
                            state="disabled",
                            command=self.saveGraph)
        subMenu.add_command(label="Export Data",
                            state="disabled",
                            command=self.exportData)

        subMenu.add_separator()
        subMenu.add_command(label="Disconnect",
                            state="disabled",
                            command=self.disconnect)

    def updateMenu(self, menu):
        menu.entryconfig(0, label=self.selectedInstrument.get())
        if(not self.selectedPort.get() == ''):
            menu.entryconfig("Start Measuring", state="normal")
            menu.entryconfig("Disconnect", state="normal")
            menu.entryconfig("Save Measurement", state="normal")
            menu.entryconfig("Export Data", state="normal")
        else:
            menu.entryconfig("Start Measuring", state="disabled")
            menu.entryconfig("Disconnect", state="disabled")
            menu.entryconfig("Save Measurement", state="disabled")
            menu.entryconfig("Export Data", state="disabled")

    class ImpedanceMeasure(threading.Thread):
        def __init__(self, app, port, selectedPort, selectedInstrument):
            threading.Thread.__init__(self)
            self.daemon = True

            self.app = app
            self.port = port
            self.selectedPort = selectedPort
            self.selectedInstrument = selectedInstrument
            self.timer = Timer()

            self.stopEvent = threading.Event()
            self.openEvent = threading.Event()

            self.connectGPIB(self.port)

        def connectGPIB(self, port):
            self.rm = visa.ResourceManager()
            self.my_instrument = self.rm.open_resource(
                'GPIB0::%d::INSTR' % port)
            self.selectedPort.set(port)
            self.selectedInstrument.set(self.my_instrument.query('*IDN?'))
            # print('x: ' + my_instrument.query('OUTP? 1'))
            # print('Y: ' + my_instrument.query('OUTP? 2'))
            # print('R: ' + my_instrument.query('OUTP? 3'))
            # print('theta: ' + my_instrument.query('OUTP? 4'))
            # print('Reference phase shift: ' + my_instrument.query('PHAS? 1'))
            # print('SNAP: ' + my_instrument.query('SNAP ? 1, 2, 3, 4, 5, 9'))

        def disconnectGPIB(self):
            self.selectedPort.set('')
            self.selectedInstrument.set('No Instrument Connected')
            self.stopEvent.set()
            self.measurementWindow.destroy()
            if(hasattr(self, 'rm')):
                self.rm.close()

        def openGraph(self):
            self.setupGraph()
            self.openEvent.set()
            self.start()

        def close(self):
            self.openEvent.clear()
            self.measurementWindow.destroy()

        def setupGraph(self):
            self.xs = []
            self.ys = []
            self.timer.reset()
            self.y = random.randint(0, 200)

            self.measurementWindow = Toplevel(self.app.root)
            self.measurementWindow.protocol(
                "WM_DELETE_WINDOW", self.close)
            self.fig = plt.figure(figsize=(12, 6), dpi=100)
            self.ax = self.fig.add_subplot(1, 1, 1)
            self.ax.set_title('Impedance over Time')
            self.ax.set_ylabel('Impedance (Ω)')
            self.ax.set_xlabel('Time (s)')
            self.ax.xaxis.set_major_locator(plticker.MultipleLocator(5))
            self.ax.xaxis.set_minor_locator(plticker.MultipleLocator(1))
            self.xs = []
            self.ys = []
            self.line, = self.ax.plot(self.xs, self.ys)
            self.canvas = FigureCanvasTkAgg(
                self.fig, master=self.measurementWindow)
            self.canvas.get_tk_widget().grid(columnspan=2)

            self.measurementWindow.cameraPhoto = PhotoImage(
                file="assets/camera.png")
            Button(self.measurementWindow, text='Save Graph', command=self.saveFig,
                   image=self.measurementWindow.cameraPhoto).grid(row=1, column=0, sticky="E")
            self.measurementWindow.savePhoto = PhotoImage(
                file="assets/save.png")
            Button(self.measurementWindow, text='Export Data', command=self.exportData,
                   image=self.measurementWindow.savePhoto).grid(row=1, column=1, sticky="W")

        def run(self):
            while not self.stopEvent.isSet():
                while(self.openEvent.isSet()):
                    # Get x and y values
                    x = self.timer.elapsedTime
                    y = self.queryGPIB()

                    if(y):

                        # Add x and y to lists
                        self.xs.append(x)
                        self.ys.append(y)

                        # Limit x and y lists to 200 items
                        if(x - self.xs[0] > 30.0):
                            self.xs.pop(0)
                            self.ys.pop(0)

                        self.line.set_data(self.xs, self.ys)
                        self.canvas.draw_idle()

                        plt.xlim([max(0.0, self.xs[0]), max(30.0, x)])
                        # plt.ylim([min(0.0, min(self.ys)*0.8, min(self.ys)
                        #               * 1.2), max(1, max(self.ys)*1.2)])
                        # plt.ylim([min(min(self.ys)*0.8, min(self.ys)
                        #               * 1.2), max(self.ys)*1.2])

                        plt.ylim([min(self.ys), max(self.ys)])
            time.sleep(0.05)

        def queryGPIB(self):
            rString = self.my_instrument.query('OUTP? 3')
            thetaString = self.my_instrument.query('OUTP? 3')
            try:
                r = float(rString)
                theta = float(thetaString)
                # impedance = r * (math.cos(theta) + math.sin(theta))
                if not r == 0:
                    impedance = 0.2/r * 1000
                else:
                    impedance = 0
                return impedance
            except ValueError:
                print("Not a float")

            # return float(self.my_instrument.query('OUTP? 1'))
            # number = random.randint(0, 3)
            # if(random.randint(0, 1) == 1):
            #     self.y += number
            # else:
            #     self.y -= number
            # return self.y

        def saveFig(self):
            ts = datetime.datetime.now()  # grab the current timestamp
            filename = "exports/graphs/{}.png".format(ts.strftime(
                "%Y-%m-%d_%H-%M-%S"))
            plt.savefig(filename, bbox_inches='tight')

        def exportData(self):
            ts = datetime.datetime.now()  # grab the current timestamp
            filename = "exports/data/{}.xlsx".format(ts.strftime(
                "%Y-%m-%d_%H-%M-%S"))
            df = DataFrame({'Time (s)': self.xs, 'Impedance': self.ys})
            df.to_excel(filename, sheet_name='sheet1', index=False)
