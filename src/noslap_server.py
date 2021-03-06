#!/usr/bin/env python3

import os
import sys
import json
import time
import pytz
import logging
from datetime import datetime
from dateutil.parser import parse
from flask import Flask, jsonify, request, render_template, redirect, abort
from redis import Redis

__date__ = "31 Dezember 2018"
__version__ = "0.1"
__email__ = "christoph.schranz@salzburgresearch.at"
__status__ = "Development"
__desc__ = """This is the NoSlap Server Dashboard."""

PORT = int(os.getenv("PORT", "1811"))

# Creating dashboard
path = os.path.dirname(os.path.abspath(__file__))
slap_file = os.path.join(path, "noSlapServer", "no-slaps.json")
config_file = os.path.join(path, "config", "config.json")

# webservice setup
app = Flask(__name__, template_folder=path)
redis = Redis(host='redis', port=PORT)

dir_path = os.path.dirname(os.path.realpath(__file__))


class NoSlapTools:
    """
    Toolset for handling with the noslap alarm service.
    """
    def __init__(self):
        self.config = json.loads(open(config_file).read())
        self.noslaps = json.loads(open(slap_file).read())
        self.noslaplist = list()

    def get_dt(self, request):
        # dt_default = datetime.now().isoformat()
        dt = request.form.get('datetime', "")
        try:
            validstring = parse(dt).replace(tzinfo=pytz.UTC).isoformat()
            return validstring
        except:
            return "invalid datetime"

    def run_tests(self):
        if len(self.config) == 0:
            print("Invalid config.json")
            sys.exit()
        if len(self.noslaps) == 0:
            print("Invalid no-slaps.json")
            sys.exit()
        print("Tests were successful")

    def start_timers(self):
        os.popen("sudo systemctl daemon-reload")
        os.popen("sudo service noslap-alarm restart")
        time.sleep(2)
        return os.popen("sudo service noslap-alarm status").read()

    def stop_timers(self):
        os.popen("sudo service noslap-alarm stop")
        os.popen("pkill omxplayer")
        print("Stopped noslap-alarm service")


# http://0.0.0.0:1811/
@app.route('/status')
def print_status():
    """
    This function returns the status.
    :return:
    """
    status = {"date": __date__,
              "email": __email__,
              "version": __version__,
              "dev status": __status__,
              "description": __desc__,
              "status": "ok"}
    # print(noslaptools.noslaplist)
    return jsonify(status)


@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
def home():
    """
    Finds the next slap and renders it in the template
    :return:
    """
    print("\nNext noSlap:")
    dayofweek = datetime.now().isoweekday()
    hourofday = ":".join(datetime.now().time().isoformat().split(":")[:2])

    noslaps = json.loads(open(slap_file).read())

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
            if ((dayofweek-1) % 7)+1 in slap["DAYS"] and slap["START_TIME"] < next_start and slap["ACTIVATED"]:
                next_start = slap["START_TIME"]
                next_slap = slap

    print("The next slap is on {} slap: {}".format(next_start, next_slap))

    return render_template('noSlapServer/app/home.html', noslap=next_slap,
                           noslap_string=["There are no outstanding NoSlaps." if next_slap is None else ""][0])
    # return render_template('noSlapServer/app/home.html')


@app.route('/delete-noslap/<int:slapid>')
def delete_noslap(slapid):
    """
    Delete the slap and reorder remaining slaps
    :param slapid:
    :return: redirect to /noslaps
    """
    noslaps = json.loads(open(slap_file).read())
    noslaps["NOSLAPS"] = noslaps["NOSLAPS"][:slapid] + noslaps["NOSLAPS"][slapid+1:]
    for i in range(len(noslaps["NOSLAPS"])):
        noslaps["NOSLAPS"][i]["ID"] = i
    logger.info("Deleted no slap with id: {}".format(slapid))

    noslaptools.start_timers()
    with open(slap_file, "w") as f:
        f.write(json.dumps(noslaps, indent=2))
    return redirect("/noslaps")


@app.route('/edit-noslap/<int:slapid>', methods=['GET', 'POST'])
def edit_noslap(slapid):
    if (request.method == 'POST') and ("day" in request.form):
        new_slap = dict(request.form)
        slap = dict({"ID": slapid,
                     "START_TIME": new_slap["starttime"][0],
                     "END_TIME": new_slap["endtime"][0],
                     "DAYS": [int(i) for i in new_slap["day"]],
                     "VOLUME": int(new_slap["Volume"][0]),
                     "ACTIVATED": "activated" in new_slap
                     })
        logger.info(slap)

        noslaps = json.loads(open(slap_file).read())
        if slapid < len(noslaps["NOSLAPS"]):  # in this case, a no slap is edited
            noslaps["NOSLAPS"][slapid] = slap
        else:  # A new no slap is added
            noslaps["NOSLAPS"].append(slap)

        with open(slap_file, "w") as f:
            f.write(json.dumps(noslaps, indent=2))

#        noslaptools.stop_timers()
        noslaptools.start_timers()
        logger.info("Updated noslaps.")
        return redirect("/noslaps")

    else:  # Show a specific no slap
        select_day = ""
        if request.method == 'POST':
            select_day = "Please select at least one day or deactivate no slap."
        noslaps = json.loads(open(slap_file).read())
        if slapid < len(noslaps["NOSLAPS"]):  # in this case, a no slap is edited
            starttime = noslaps["NOSLAPS"][slapid]["START_TIME"]
            endtime = noslaps["NOSLAPS"][slapid]["END_TIME"]
            def_volume = noslaps["NOSLAPS"][slapid]["VOLUME"]
            days = noslaps["NOSLAPS"][slapid]["DAYS"]
        else:  # in this case, we add a no slap
            starttime = "07:00"
            endtime = "08:00"
            def_volume = "36"
            days = [1, 2, 3, 4, 5]
        return render_template('noSlapServer/app/edit-noslap.html', select_day=select_day,
                               starttime=starttime, endtime=endtime, def_volume=def_volume, days=days)


@app.route('/edit-noslap/', methods=['GET', 'POST'])
def add_no_slap():
    """
    This function is called if a new slap is added,
    therefore it is redirected to the subsequent id.
    :return:
    """
    noslaps = json.loads(open(slap_file).read())
    slapid = len(noslaps["NOSLAPS"])
    return redirect("/edit-noslap/{}".format(slapid))


@app.route('/noslaps', methods=['GET', 'POST'])
def my_no_slaps():
    """
    List all slaps
    :return:
    """
    noslaps = json.loads(open(slap_file).read())
    if noslaps["NOSLAPS"] is list():
        noslaps_string = "There are no NoSlaps in the next 20 hours."
    else:
        noslaps_string = ""
    return render_template('noSlapServer/app/no-slaps.html', noslaps=noslaps["NOSLAPS"],
                           noslaps_string=noslaps_string)


@app.route('/settings', methods=['GET', 'POST'])
def edit_settings():
    """
    Set the internal configs and threshold.
    Writes back into file pretty after reading.
    :return:
    """
    if request.method == 'POST':
        try:
            settings = json.loads(request.form["textbox"])
            with open(config_file, "w") as f:
                f.write(json.dumps(settings, indent=2))
            logger.info("updated settings")
            settings = open(config_file).read()
            return render_template('noSlapServer/app/settings.html', status="settings were saved", settings=settings)
        except json.decoder.JSONDecodeError:
            logger.warning("Invalid filaments.json")
            return jsonify("Invalid json")

    else:
        settings = open(config_file).read()
        return render_template('noSlapServer/app/settings.html', settings=settings)


if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger("NoSlapServer")
    logger.setLevel(logging.INFO)

    while True:
        noslaptools = NoSlapTools()
        noslaptools.run_tests()

        res = noslaptools.start_timers()
        print(res)

        logger.info("Starting NoSlap Server on port: {}".format(PORT))
        try:
            app.run(host="0.0.0.0", debug=True, port=PORT)
        except KeyboardInterrupt:
            pass
        finally:
            print("terminate all noslap services")
            noslaptools.stop_timers()
