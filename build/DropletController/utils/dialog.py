from tkinter import *


class CustomDialog(Toplevel):
    def __init__(self, parent, prompt, label=None, value=None):
        Toplevel.__init__(self, parent)

        self.var = None
        self.string = StringVar()
        if(value):
            self.string.set(value)

        self.prompt = Label(self, text=prompt)
        self.entry = Entry(self, textvariable=self.string)
        self.label = Label(self, text=label)
        self.ok_button = Button(self, text="OK", command=self.on_ok)

        self.prompt.pack(side="top", fill="x")
        self.entry.pack(side="top", fill="x")
        self.label.pack(side="top", fill="x")
        self.ok_button.pack(side="right")

        self.entry.bind("<Return>", self.on_ok)

    def on_ok(self, event=None):
        self.var = self.string.get()
        self.destroy()

    def show(self):
        self.wm_deiconify()
        self.entry.focus_force()
        self.wait_window()
        return self.var


if __name__ == "__main__":
    root = Tk()
    root.wm_geometry("400x200")
    root.mainloop()
