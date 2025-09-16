#!/bin/bash

# Permissions /var/www/html
cd /var/www
sudo chown francis:www-data /var/www/html
sudo chmod 0775 -R /var/www/html

# Files RPI-Heudicourt
cd html
ln -s /home/francis/Pc/Raspberry/RPI-Heudicourt/webserver/main.html index.html
ln -s /home/francis/Pc/Raspberry/RPI-Heudicourt/database/logdata.db
ln -s /home/francis/Pc/Raspberry/RPI-Heudicourt/heudicourt-solaire/pythonplot.py
ln -s /home/francis/Pc/Raspberry/RPI-Heudicourt/webserver/solaire.php
ln -s /home/francis/Pc/Raspberry/RPI-Heudicourt/heudicourt-solaire/webserver_plot.sh

