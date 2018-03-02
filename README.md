To install, git clone this repository as follows: 

    sudo git clone https://github.com/chadgates/RaspiCharts /usr/local/bin 
    
Then add service to systemd as follows: 

    sudo nano /lib/systemd/system/climateserver.service

Add following to file: 
    
    [Unit]
    Description=Climate Server
    After=multi-user.target
    
    [Service]
    Type=idle
    ExecStart=/usr/bin/python /usr/local/bin/RaspiCharts/server.py > /var/log/climateserver.log
    
    [Install]
    WantedBy=multi-user.target


Save the file and enable the service: 

    sudo chmod 644 /lib/systemd/system/climateserver.service
    sudo systemctl enable climateserver.service
    


Then do the same for the client: 

    sudo nano /lib/systemd/system/climateserver.service

Add following to the file: 
    
    [Unit]
    Description=Climate Client
    After=multi-user.target
    
    [Service]
    Type=idle
    ExecStart=/usr/bin/python /usr/local/bin/RaspiCharts/client.py > /var/log/climateclient.log
    
    [Install]
    WantedBy=multi-user.target
    
And enable it: 

    sudo chmod 644 /lib/systemd/system/climateclient.service
    sudo systemctl enable climateclient.service


Then reboot the RaspberryPi
    
    sudo reboot
