#!/usr/bin/python3
#----------------------------------------------------------------
# Dateiname: motion_detect.pyw
# Das RPi-Kameramodul ist angeschlossen.
# Anzeige des Livebilds der Kamera mit aktueller Uhrzeit.
# Bewegungen (z.B. vorbeifahrende Autos) werden erkannt.
# 
# Michael Weigend
# Raspberry Pi programmieren mit Python, 3. Auflage, mitp 2016
# Kap. 10.4
# Michael Weigend 20. April 2016
#-----------------------------------------------------------------
import os, time 
from tkinter import Tk, Label,N,LEFT
from PIL import Image, ImageTk
WIDTH = 400
HEIGHT = 300
BBOX= (50, 100, 350, 200)
BASEDIR = '/home/pi/photos/'
PATH = BASEDIR + 'image.jpg'
THRESHOLD = 50
MIN_SIZE = 400

class App:
    def __init__(self):
        self.window = Tk()
        self.label = Label(master=self.window)
        self.label.pack()
        self.labelTime = Label(master=self.window)
        self.labelTime.pack()
        self.image=None                          
        self.pImage=None                          
        self.oldImage=None                      
        self.movingObject = False
        self.run()
        self.window.mainloop() 

    def takePhoto (self):
        self.oldImage = self.image                # altes Bild 
        command = 'raspistill -t 300 -w %i -h %i -o %s -n '
        os.system(command % (WIDTH, HEIGHT, PATH))
        self.image = Image.open(PATH)
        self.pImage=ImageTk.PhotoImage(self.image)    
        self.label.config(image=self.pImage)   

    def checkMotion (self):                       
        if self.image and self.oldImage:
            old = self.oldImage.crop(BBOX)
            new = self.image.crop(BBOX)
            if self.checkDifference(old, new):
                if not self.movingObject:
                   self.image.save(BASEDIR + time.asctime() +'.jpg')
                self.labelTime.config(text=time.asctime() + " Objekt erkannt")
                self.movingObject=True
            else:
                self.movingObject = False
                self.labelTime.config(text=time.asctime() + " Keine Bewegung")
            
    def checkDifference(self, old, new):            
        changed = 0
        o, n = old.load(), new.load()
        width, height = old.size
        for x in range(width):
            for y in range(height):
                diff = abs(o[x, y][1] - n[x, y][1])
                if diff > THRESHOLD:
                    changed += 1
        return changed > MIN_SIZE      

    def run(self):
        self.takePhoto()
        self.checkMotion()
        self.window.after(100, self.run)

App()           
        
        
