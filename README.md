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
 3. Install noSlap Setup:

```bash
git clone https://github.com/ChristophSchranz/noSlap.git
cd noSlap
sudo ./install_noSlap.sh
```

In install_noSlap.sh, we:

*   Check if the Camera works

        vcgencmd get_camera
        -> supported=1 detected=1
        raspistill -v -o test.jpg

*   Install required packages

*   Create and preconfigure `noslap-server.service` and `noslap-alarm.service` in `/etc/systemd/system`.

*   Start `noslap-server.service`

Check if the user `pi` has permissions to write the data:

    sudo chown -R pi.pi *

Make sure that the Raspberry Pi connects to your hotspot, e.g. with the following `/etc/dhcpcd.conf` addendum:

The Server will be available from your smartphone on [192.168.43.40:1811](192.168.43.40:1811)
    
    interface wlan0
    static ip_address=192.168.43.40/24
    static routers=192.168.43.1
    static domain_name_servers=192.168.43.1
    
    interface wlan1
    static ip_address=192.168.48.171/24
    static routers=192.168.48.1
    static domain_name_servers=192.168.48.2,192.168.48.3
 
Reboot the Raspberry Pi to make the settings run correctly.

## Usage

```bash
sudo service noslap-server restart
sudo service noslap-server status
sudo service noslap-server stop
```

Open [localhost:1811](0.0.0.0:1811) and Use the service


## Configuration

Open [localhost:1811/settings](0.0.0.0:1811/settings)

Configure the settings in 0.0.0.0:1811/settings
TIME_THRESHOLD, MAGNITUDE_THRESHOLD, DEFAULT_SONG, RADIO
Click on Save, which triggers a service restart.
