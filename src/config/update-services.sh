echo "Updating noSlap services"
sudo systemctl daemon-reload
sudo systemctl start noslap-logger
sudo systemctl enable noslap-logger
sudo systemctl start noslap-server
sudo systemctl enable noslap-server
sleep 5
systemctl --no-pager status noslap-logger
systemctl --no-pager status noslap-server

