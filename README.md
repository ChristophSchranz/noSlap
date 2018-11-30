# noSlap

### An alarm clock based on optical feedback and a Raspberry Pi.

#### The weckIO module measures the your sleep intensity and wakes 
you in the sleep phase you are ready to get up.

## Contents

1. [Requirements](#requirements)
2. [Usage](#usage)
3. [Configuration](#configuration)
4. [Trouble-Shooting](#trouble-shooting)


## Requirements:
 1. Raspberry Pi with running debian
 2. Raspberry Pi Camera
Check if the Camera works
```bash
vcgencmd get_camera
-> supported=1 detected=1
raspistill -v -o test.jpg
```

 3. Install noSlap Setup:

```bash
git clone https://github.com/...
cd wakeIO
sudo ./install_noSlap.sh
```

In install_noSlap.sh, we:

* check if cam works

* install required packages

* create noSlap.service

* enable autostart

* Start the Service


## Usage

```bash
sudo service noslap restart
sudo service noslap status
sudo service noslap stop
```

Open [localhost:1811](0.0.0.0:1811) and Use the service


## Configuration

Open [localhost:1811](0.0.0.0:1811), click on on/off, edit wake intevall

Configure the settings in 0.0.0.0:1811/settings
TIME_THRESHOLD, MAGNITUDE_THRESHOLD, DEFAULT_SONG, RADIO
Click on Save, which triggers a service restart.
