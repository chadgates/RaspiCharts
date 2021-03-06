# Climate Monitor

## Description
This is a monitor for a server room using a RaspberryPi Zero with a GrovePi Temperatur Sensor.
A websocket webserver serves webbrowsers via port 9000. A client process polls the temperatur and
humidity every 5 seconds and pushes them to server. 


Some alarm settings in the client allow e-mail to be sent based on environment variables. 


![Browser Front End](/img/webfrontend.png)


## Installation

To install, git clone this repository as follows: 

    sudo git clone https://github.com/chadgates/RaspiCharts /usr/local/bin/RaspiCharts
    sudo pip install -r /usr/local/bin/requirements.txt

    
Then add service to systemd as follows: 

    sudo nano /lib/systemd/system/climateserver.service

Add following to file: 
    
    [Unit]
    Description=Climate Server
    After=multi-user.target
    
    [Service]
    Type=idle
    ExecStart=/usr/bin/python /usr/local/bin/RaspiCharts/server.py
    
    [Install]
    WantedBy=multi-user.target


Save the file and enable the service: 

    sudo chmod 644 /lib/systemd/system/climateserver.service
    sudo systemctl enable climateserver.service
    


Then do the same for the client: 

    sudo nano /lib/systemd/system/climateserver.service

Add following to the file and fill in the environment variables: 
    
    [Unit]
    Description=Climate Client
    After=multi-user.target
    
    [Service]
    Type=idle
    Environment="EMAIL_SENDER="
    Environment="EMAIL_RECEIVER="
    Environment="EMAIL_SERVER="
    Environment="RUN_MODE=PRODUCTION"
    
    ExecStart=/usr/bin/python /usr/local/bin/RaspiCharts/client.py
    
    [Install]
    WantedBy=multi-user.target
    
And enable it: 

    sudo chmod 644 /lib/systemd/system/climateclient.service
    sudo systemctl enable climateclient.service


Then reboot the RaspberryPi
    
    sudo reboot


To check the output of the logs: 

    sudo journalctl -u climateserver.service
    sudo journalctl -u climateclient.service
    

## Add cronjob to reset the GrovePi at midnight

This may be required as after a while (usually after about 1 week), no more 
valid results are received. 
Issue discussed also here: https://forum.dexterindustries.com/t/grove-pi-rst/743/6

Therefore decided to add a cron job to reset once every day: 

Run crontab with -e flag to edit the cron table: 

    crontab -e
 
Select and editor (if this is the first time).
 
Add a scheduled task

     0 0 * * * /usr/bin/avrdude -c gpio -p m328p


## E-Mail Server Test

To run an email server test, run
    
    python testmail.py
   