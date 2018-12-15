#!/usr/bin/env bash
echo "Setting up noSlap"

echo
echo "***************************************************************"
echo "Checking the camera"
echo
echo Running: vcgencmd get_camera
echo $(vcgencmd get_camera)
result=$(echo $(vcgencmd get_camera) | awk '{print $2}')

if [ "$result" != "detected=0" ]; then
	echo "The camera works."
        echo
        echo "***************************************************************"
        echo "Turning off the lights"
	sudo sh -c "echo 0 > /sys/class/leds/led0/brightness"
	sudo sh -c "echo 0 > /sys/class/leds/led1/brightness"
	sudo sh -c "echo 'disable_camera_led=1' >> /boot/co"
	# Turn off raspberry pi camera light
	cat /boot/config.txt | grep -v 'Added by noSlap to turn off the camera light' | grep -v 'disable_camera_led' > boot_config.txt
	sudo cp boot_config.txt /boot/config.txt.save
	# sudo rm boot_config.txt
	sudo sh -c "echo 'Added by noSlap to turn off the camera light' >> /boot/config.txt"
	sudo sh -c "echo 'disable_camera_led=1' >> /boot/config.txt"

	echo
	echo "***************************************************************"
	echo "Installing requirements"
	echo
	sudo apt-get update
	sudo apt-get dist-upgrade -y
	sudo apt-get -y install python3-pil python3-pil.imagetk
	sudo apt-get -y install python3-openpyxl
	sudo apt-get -y install python3-tk
#	pip3 install Pillow
	pip3 install pytz
	pip3 install redis
	pip3 install flask
	pip3 install python-dateutil

	echo
	echo "***************************************************************"
	echo "Creating NoSlap Services"
	echo
	sudo cp src/config/noslap-logger.service /etc/systemd/system/noslap-logger.service
	sudo cp src/config/noslap-server.service /etc/systemd/system/noslap-server.service

	sudo systemctl daemon-reload
	sudo systemctl restart noslap-logger
	sudo systemctl enable noslap-logger
	sudo systemctl restart noslap-server
	sudo systemctl enable noslap-server
	sleep 5
	systemctl --no-pager status noslap-logger
	systemctl --no-pager status noslap-server
        echo
        echo "***************************************************************"
	echo "Installed NoSlap, the service is avalable on localhost:1811 in the browser."
	echo "You might have to reboot the system to activate the system changes."

else
        echo
        echo "***************************************************************"
        echo "ERROR the camera is may not connected"
        echo "Check 'vcgencmd get_camera' and 'raspistill -v -o test.jpg' to debug the error. Also check the side of the camera cable!"
fi
