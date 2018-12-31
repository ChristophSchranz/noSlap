#!/usr/bin/env python3
##wecker_io by Christoph Schranz & Peter Jeremias
##Motion detection for the alarm
##Taking photos with the rpi camera and write pixel changes to a log csv file

##-----------------------------------------------------------------
import os, sys, time, json, inspect
from PIL import Image
import logging
from datetime import datetime
import pytz


##main class and definitions
##initially setting images to compare to None
##creating a csv file with with the cration time as name
class NoSlap:
    def __init__(self, start_time, end_time, days, volume=0, testing=False):
        logging.basicConfig()
        self.logger = logging.getLogger("NoSlap")
        self.logger.setLevel(logging.DEBUG)
        self.logger.info("Started NoSlap Logger")

        self.VOLUME = volume  # content.get("VOLUME", 0)
        self.START_TIME = start_time  # content.get("START_TIME", "07:00:00")
        self.END_TIME = end_time  # content.get("END_TIME", "08:00:00")
        self.DAYS = days  # [1,2,3,4,5]  # TODO read config json
        self.testing = testing
        self.logger.info("Next Slap: {}".format(self.START_TIME))
        if testing:
            self.logger.info("Started NoSlap instance in demo mode")

        ## defining image dimensions, directory, movement threshold
        with open("config/config.json") as f:
            content = json.loads(f.read())
        ##variables are not called yet, they should replace the ones, assigned in the check.Motion method
        self.THRESHOLD = content.get("MAGNITUDE_THRESHOLD", 50)
        self.MIN_CHANGE = content.get("MIN_CHANGE", 30)
        self.MAX_CHANGE = content.get("MAX_CHANGE", 20000)
        self.RECENT_VALUES = content.get("RECENT_VALUES", 10)
        self.AWAKE = content.get("AWAKE", 5)
        self.PORT = content.get("PORT", 1810)
        self.WIDTH = 400
        self.HEIGHT = 300
        self.BBOX= (50, 100, 350, 200)
        self.FILENAME = inspect.getframeinfo(inspect.currentframe()).filename
        self.BASEDIR = os.path.dirname(os.path.realpath(self.FILENAME))
        self.logger.debug("basedir: {}".format(self.BASEDIR))
        ##BASEDIR = os.path.dirname(os.path.abspath(__file__))
        self.PATH = self.BASEDIR + '/images/image.jpg'
        self.THRESHOLD = 50
        self.changelist = []
        self.alarm = False
        self.motiondetect = 0
        
        self.image=None                          
        self.pImage=None                          
        self.oldImage=None                      
        self.movingObject = False

        ##changing the start and end time to utc format
        # local = pytz.timezone ("Europe/Vienna")
        try:
            start_datetime = datetime.strptime(" ".join([datetime.now().date().isoformat(), self.START_TIME]), "%Y-%m-%d %H:%M")
        except ValueError:
            start_datetime = datetime.strptime(" ".join([datetime.now().date().isoformat(), self.START_TIME]), "%Y-%m-%d %H:%M:%S")
        self.logger.info(start_datetime)
        # local_dt = local.localize(start_datetime, is_dst=None)
        # self.START_TIME = local_dt.astimezone(pytz.utc).time().isoformat()
        self.START_TIME = start_datetime.time().isoformat()
        self.logger.info("From {}".format(self.START_TIME))

        try:
            end_datetime = datetime.strptime (" ".join([datetime.now().date().isoformat(), self.END_TIME]), "%Y-%m-%d %H:%M")
        except ValueError:
            end_datetime = datetime.strptime (" ".join([datetime.now().date().isoformat(), self.END_TIME]), "%Y-%m-%d %H:%M:%S")
        # local_dt = local.localize(end_datetime, is_dst=None)
        # self.END_TIME = local_dt.astimezone(pytz.utc).time().isoformat()
        self.START_TIME = start_datetime.time().isoformat()
        self.logger.info("To {}".format(self.END_TIME))
        
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

    ##command to the rpi camera to take a photo and save it as image in the directory
    ##opening the image to compare
    def takePhoto (self):
        if not self.testing:
            self.oldImage = self.image                # altes Bild
            command = 'raspistill -t 300 -w %i -h %i -o %s -n '
            os.system(command % (self.WIDTH, self.HEIGHT, self.PATH))
            self.image = Image.open(self.PATH)

    ##method to write change values to a csv
    ##crop the two images to a bbox
    def checkMotion (self):                     
        if self.image and self.oldImage and not self.testing:
            old = self.oldImage.crop(self.BBOX)
            new = self.image.crop(self.BBOX)
            
            ##assigning the difference to the changed variable
            ##get the time of the change detection and write it with the number of changed pixels to csv
            ##append the change value to a list
            changed = self.getDifference(old, new)
            timestamp = datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat()
            self.logger.debug("{}, {}".format(timestamp, changed))
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
                    self.logger.info("Alarm")
                    self.alarm = True
                    ##return alarm
                    ##self.playsound()
        elif self.testing:
            timestamp = datetime.now().replace(microsecond=0).replace(tzinfo=pytz.UTC).time().isoformat()
            self.logger.info("debug: time: {}, start_time: {}, motiondetect: {}".format(timestamp, self.START_TIME,
                                                                             self.motiondetect))
            if timestamp < self.START_TIME:
                return
            self.motiondetect += 1
            if self.motiondetect >= 25:
                print("Test alarm")

    def killplayer (self):
        try:
            os.popen("pkill omxplayer")
        except:
            self.logger.info("omxplayer not found")

    def playsound (self):
        os.popen("omxplayer music/Arctic\ Monkeys\ -\ Do\ I\ Wanna\ Know.mp3 --vol -500 &")
                    
                
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

    ## write a header to the csv file
    ## loop and call the methods every 0.5 seconds, until alarm is reutrned as True
    def run(self):
        self.logger.info("Run run(), Starttime: {}, DayofWeeks: {}".format(self.START_TIME, self.DAYS))
        if not self.testing:
            self.killplayer()

        # Wait until a the alarm time span
        self.curtime = datetime.now()
        c = 0
        while not (self.curtime.isoweekday() in self.DAYS and self.curtime.time().isoformat() > self.START_TIME and self.curtime.time().isoformat() < self.END_TIME ):
            self.curtime = datetime.now()
            if (c % 10 == 0):
                self.logger.debug("Current time: {}, day: {}".format(self.curtime, self.curtime.isoweekday()))
            time.sleep(1)  # Set back to 0.1
            c += 1

        self.logger.debug("The time has come: {}".format(self.datafile))
        with open(self.datafile, "w") as file:
            file.write("Timestamp, DifferentPixels")
        curtime = datetime.now()
        self.logger.debug(curtime.time().isoformat())
        self.alarm = False
        while (self.alarm == False) and (curtime.time().isoformat() < self.END_TIME):##change from alarm == False:
            curtime = datetime.now()
            self.takePhoto()
            self.checkMotion()
            time.sleep(0.2)  # changed from 0.5

        self.logger.debug("Play that sound")
        self.playsound()

        # Wait until the button is pressed or the service restartet
        while True:  # TODO not button_pressed
            time.sleep(0.2)
        self.logger.info("Button was pressed, terminating program now")


if __name__ == '__main__':
    print("\nNext noSlap:")
    dayofweek = datetime.now().isoweekday()
    hourofday = ":".join(datetime.now().time().isoformat().split(":")[:2])

    with open(os.sep.join([os.getcwd(), "noSlapServer/no-slaps.json"])) as slaps:
        noslaps = json.loads(slaps.read())

    # Check for the next Slap on the same day:
    next_slap = None
    next_start = "24:00"
    for slap in noslaps["NOSLAPS"]:
        if dayofweek in slap["DAYS"] and hourofday < slap["START_TIME"] and slap["START_TIME"] < next_start and slap["ACTIVATED"]:
            next_start = slap["START_TIME"]
            next_slap = slap

    # If there are no slaps on the same day, check the next day
    if next_slap is None:
        for slap in noslaps["NOSLAPS"]:
            if ((dayofweek - 1) % 7) + 1 in slap["DAYS"] and slap["START_TIME"] < next_start and slap["ACTIVATED"]:
                next_start = slap["START_TIME"]
                next_slap = slap

    print("The next slap is on {} slap: {}".format(next_start, next_slap))

    # next_slap = no_slaps["NOSLAPS"][-1]  # remove
    # calling the main method with standard parameter in UTC time
    if next_slap is not None:
        testing = False
        no_slap = NoSlap(next_slap["START_TIME"], next_slap["END_TIME"],
                         next_slap["DAYS"], next_slap["VOLUME"], testing)
        no_slap.run()

