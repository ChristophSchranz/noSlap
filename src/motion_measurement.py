#!/usr/bin/env python3
##wecker_io by Christoph Schranz & Peter Jeremias
##Motion detection for the alarm
##Taking photos with the rpi camera and write pixel changes to a log csv file

##-----------------------------------------------------------------
import os, time, json, inspect
from PIL import Image
from datetime import datetime
import pytz

    # print(type(content))

##main class and definitions
##initially setting images to compare to None
##creating a csv file with with the cration time as name
class App:
    def __init__(self):
        ## defining image dimensions, directory, movement threshold
        with open("config/config.json") as f:
            content = json.loads(f.read())
        ##variables are not called yet, they should replace the ones, assigned in the check.Motion method
        self.VOLUME = content.get("VOLUME", 0)
        self.START_TIME = content.get("START_TIME", "07:00:00")
        self.END_TIME = content.get("END_TIME", "08:00:00")
        self.THRESHOLD = content.get("MAGNITUDE_THRESHOLD", 50)
        self.MIN_CHANGE = content.get("MIN_CHANGE", 30)
        self.MAX_CHANGE = content.get("MAX_CHANGE", 20000)
        self.RECENT_VALUES = content.get("RECENT_VALUES", 10)
        self.AWAKE = content.get("AWAKE", 5)
        self.DAYS = [1,2,3,4,5]  # TODO read config json
        self.PORT = content.get("PORT", 1810)
        self.WIDTH = 400
        self.HEIGHT = 300
        self.BBOX= (50, 100, 350, 200)
        self.FILENAME = inspect.getframeinfo(inspect.currentframe()).filename
        self.BASEDIR = os.path.dirname(os.path.abspath(self.FILENAME))
        ##BASEDIR = os.path.dirname(os.path.abspath(__file__))
        self.PATH = self.BASEDIR + '/images/image.jpg'
        self.THRESHOLD = 50
        self.changelist = []
        self.alarm = False
        
        self.image=None                          
        self.pImage=None                          
        self.oldImage=None                      
        self.movingObject = False
        
        ##changing the start and end time to utc format
        local = pytz.timezone ("Europe/Vienna")
        start_datetime = datetime.strptime (" ".join([datetime.now().date().isoformat(), self.START_TIME]), "%Y-%m-%d %H:%M")
        local_dt = local.localize(start_datetime, is_dst=None)
        self.START_TIME = local_dt.astimezone(pytz.utc).time().isoformat()
        print(self.START_TIME)
        
        end_datetime = datetime.strptime (" ".join([datetime.now().date().isoformat(), self.END_TIME]), "%Y-%m-%d %H:%M")
        local_dt = local.localize(end_datetime, is_dst=None)
        self.END_TIME = local_dt.astimezone(pytz.utc).time().isoformat()
        print(self.END_TIME)
        
        ##looping through the datafiles and remove files older than a week
        self.datafile = self.BASEDIR + '/data/data_' + datetime.utcnow().replace(tzinfo=pytz.UTC) \
                        .replace(microsecond=0).isoformat().replace(":", "_").replace("-", "_") \
                        .split("+")[0] + ".csv"
        self.realseconds = (datetime.utcnow() - datetime(1979, 1, 1)).total_seconds()
        self.datadir = self.BASEDIR + '/data'
        for file in os.listdir(self.datadir):
            self.filepath = os.path.join(self.datadir, file)
            if os.path.getctime(self.filepath) < (self.realseconds-(3600*24*7)):
                os.remove(self.filepath)
        
        
        self.curtime = datetime.utcnow()
        while (self.curtime.isoweekday() not in self.DAYS) or (self.curtime.time().isoformat() < self.START_TIME):
            ##print(curtime)
#           currenttime = timecounter()
            self.curtime = datetime.now()
            time.sleep(0.1)
            
        ##if curtime == START_TIME:
        print("start")
        self.run()
        ##print("start run")
        
    ##command to the rpi camera to take a photo and save it as image in the directory
    ##opening the image to compare
    def takePhoto (self):
        self.oldImage = self.image                # altes Bild 
        command = 'raspistill -t 300 -w %i -h %i -o %s -n '
        os.system(command % (self.WIDTH, self.HEIGHT, self.PATH))
        self.image = Image.open(self.PATH) 

    ##method to write change values to a csv
    ##crop the two images to a bbox
    def checkMotion (self):                     
        if self.image and self.oldImage:
            old = self.oldImage.crop(self.BBOX)
            new = self.image.crop(self.BBOX)
            
            ##assigning the difference to the changed variable
            ##get the time of the change detection and write it with the number of changed pixels to csv
            ##append the change value to a list
            changed = self.getDifference(old, new)
            timestamp = datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat()
            print("{}, {}".format(timestamp, changed))
            with open(self.datafile, 'a') as file:
                file.write("\n{}, {}".format(timestamp, changed))
            self.changelist.append(changed)
            
            ##iterating through the last 10 values of the list
            ##filtering all change values between 30 and 20000
            ##returning alarm as True, if at least 5 of the last 10 values are in the filter
            global alarm
            motiondetect = 0
            backwards = -1
            if len(self.changelist) >= self.RECENT_VALUES:
                while backwards >= -10:
                    value = self.changelist[backwards]
                    if value >= self.MIN_CHANGE:
                        if value < self.MAX_CHANGE:
                            motiondetect += 1
                            print(motiondetect)
                    backwards -= 1
                if motiondetect >= self.AWAKE:
                    print("Alarm")
                    self.alarm = True
                    ##return alarm
                    ##self.playsound()
                    
    
    def killplayer (self):
        os.popen("pkill omxplayer")
        
    def playsound (self):
        os.popen("omxplayer music/Arctic\ Monkeys\ -\ Do\ I\ Wanna\ Know.mp3 --vol -500 &")
        print("pass")
                    
                
    ##method to detect changes in pixels of the two photos
    ##set a change counter to initially 0 and iterate through all pixel rows and columns
    ##append the change value by 1 if the difference exceeds the threshold, return the value to the main method
    def getDifference(self, old, new):            
        changed = 0
        o, n = old.load(), new.load()
        width, height = old.size
        for x in range(width):
            for y in range(height):
                diff = abs(o[x, y][1] - n[x, y][1])
                if diff > self.THRESHOLD:
                    changed += 1
        return changed      

    ##write a header to the csv file
    ## loop and call the methods every 0.5 seconds, until alarm is reutrned as True
    def run(self):
        self.killplayer()
        print(self.datafile)
        with open(self.datafile, "w") as file:
            file.write("Timestamp, DifferentPixels")
        curtime = datetime.utcnow()
        print(curtime.time().isoformat())
        self.alarm = False
        while (self.alarm == False) and (curtime.time().isoformat() < self.END_TIME):##change from alarm == False:
            curtime = datetime.utcnow()
            self.takePhoto()
            self.checkMotion()
            print("alarm")    
            time.sleep(0.2)##changed from 0.5
        print("pass")
        self.playsound()
        print("pass")

##calling the main method
App()           
        
        
