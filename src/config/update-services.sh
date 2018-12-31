#!/usr/bin/env bash
echo "Updating noSlap services"
sudo systemctl daemon-reload

sudo systemctl start noslap-server
sudo systemctl enable noslap-server
sleep 5
systemctl --no-pager status noslap-alarm
systemctl --no-pager status noslap-server

