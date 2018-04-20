#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tornado.ioloop import IOLoop, PeriodicCallback
from tornado import gen
from tornado.websocket import websocket_connect

from random import randint  # Random generator

try:
    import grovepi
except:
    pass

import math
import logging
import os
import time
import datetime
import sys

DHT_SENSOR_TYPE = 0
DHT_SENSOR_PORT = 3
MILLISECONDS_BETWEEN_READS = 5000

RUN_MODE = os.getenv('RUN_MODE', 'PRODUCTION')
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_RECEIVER = os.getenv('EMAIL_RECEIVER')
EMAIL_SERVER = os.getenv('EMAIL_SERVER')

ALERTSTATE = 'Green'
REPORTTIME = None
TEMP_THRESHOLD = 28
HUMI_THRESHOLD = 80
ALERTWAIT = 300
ALERTRESEND = 3600
ALERTCOUNT = 0
RESENDCOUNT = 0


READERSTATE = 'Green'
READERTIME = None
READERRESENDCOUNT = 0


logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def isFloat(string):
    try:
        float(string)
        if math.isnan(float(string)):
            return False
        return True
    except ValueError:
        return False


class Client(object):
    def __init__(self, url, timeout):
        self.url = url
        self.timeout = timeout
        self.ioloop = IOLoop.instance()
        self.ws = None
        self.connect()
        PeriodicCallback(self.keep_alive, MILLISECONDS_BETWEEN_READS, io_loop=self.ioloop).start()
        try:
            self.ioloop.start()
        except KeyboardInterrupt:
            print("Client stopped -> CTRL+C pressed")

    @gen.coroutine
    def connect(self):
        logging.info("trying to connect")
        try:
            self.ws = yield websocket_connect(self.url)
        except Exception as e:
            logging.info("connection error")
        else:
            logging.info("connected")
            self.run()

    @gen.coroutine
    def run(self):
        while True:
            msg = yield self.ws.read_message()
            if msg is None:
                logging.info("connection closed")
                self.ws = None
                break

    def keep_alive(self):
        global ALERTSTATE
        global REPORTTIME
        global ALERTWAIT
        global ALERTRESEND
        global ALERTCOUNT
        global READERTIME
        global READERSTATE
        global RESENDCOUNT
        global READERRESENDCOUNT

        if self.ws is None:
            self.connect()
        else:
            try:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if RUN_MODE == 'PRODUCTION':
                    [temp_c, hum] = grovepi.dht(DHT_SENSOR_PORT, DHT_SENSOR_TYPE)
                    if isFloat(temp_c):
                        logging.debug("Temperature (C) = " + str(temp_c))

                        if READERSTATE != 'Green':
                            READERSTATE = 'Green'
                            READERTIME = None
                            logging.info("Reader state alert removed - Status back normal")
                    else:
                        if READERSTATE == 'Green':
                            READERSTATE = 'Yellow'
                            logging.info("Reader state changed to Yello")
                        if not READERTIME:
                            READERTIME = time.time()

                    if ((isFloat(hum)) and (hum > 0)):
                        logging.debug("Humidity (%) = " + str(hum))
                        self.ws.write_message(str(temp_c) + ";" + str(hum) + ";" + timestamp)
                elif RUN_MODE == 'DEVELOPMENT':
                    temp_c = randint(15,30)
                    hum = randint(25,80)
                    self.ws.write_message(str(temp_c) + ";" + str(hum) + ";" + timestamp)
                elif RUN_MODE == 'ALERT':
                    ALERTWAIT = 10
                    ALERTRESEND = 30
                    if ALERTCOUNT <= 6:
                        temp_c = 30
                        hum = 80
                        ALERTCOUNT += 1
                    else:
                        temp_c = 25
                        hum = 40
                    self.ws.write_message(str(temp_c) + ";" + str(hum) + ";" + timestamp)
                elif RUN_MODE == 'READERALERT':
                    [temp_c, hum] = float('nan'), float('nan')
                    if isFloat(temp_c):
                        logging.debug("Temperature (C) = " + str(temp_c))

                        if READERSTATE != 'Green':
                            READERSTATE = 'Green'
                            READERTIME = None
                            logging.info("Reader state alert removed - Status back normal")
                    else:
                        if READERSTATE == 'Green':
                            READERSTATE = 'Yellow'
                            logging.info("Reader state changed to Yello")
                        if not READERTIME:
                            READERTIME = time.time()

                    if ((isFloat(hum)) and (hum > 0)):
                        logging.debug("Humidity (%) = " + str(hum))
                        self.ws.write_message(str(temp_c) + ";" + str(hum) + ";" + timestamp)


                else:
                    logging.error("Unknown RUN_MODE:" + RUN_MODE)

                # check for alert

                if temp_c >= TEMP_THRESHOLD or hum >= HUMI_THRESHOLD:
                    if REPORTTIME == None:
                        REPORTTIME = time.time()

                    if ALERTSTATE == 'Green' and (time.time() - REPORTTIME) >= ALERTWAIT:
                        logging.info("Alert raised")
                        ALERTSTATE = 'Red'
                        send_alert_by_mail(temp_c, hum, 'ALARM')

                    if ALERTSTATE == 'Red' and (time.time() - REPORTTIME) >= (ALERTRESEND * (RESENDCOUNT+1)):
                        logging.info("Alert resend")
                        send_alert_by_mail(temp_c, hum, 'ALARM')
                        RESENDCOUNT += 1

                if temp_c < TEMP_THRESHOLD and hum < HUMI_THRESHOLD:
                    if ALERTSTATE == 'Red':
                        logging.info("Alert removed - Status back normal")
                        send_alert_by_mail(temp_c, hum, 'Normal')
                        ALERTSTATE = 'Green'
                        REPORTTIME = None
                        RESENDCOUNT = 0
                    else:
                        REPORTTIME = None

                if READERTIME:
                    if (time.time() - READERTIME) >= ALERTWAIT and READERSTATE == 'Yellow':
                        logging.info("Reader Alert raised")
                        send_alert_by_mail(0, 0, 'READER ALARM')
                        READERSTATE = 'Red'
                        logging.info("Reader state changed to Red")

                    if (time.time() - READERTIME) >= (ALERTRESEND * (READERRESENDCOUNT+1)) and READERSTATE == 'Red':
                        logging.info("Reader Alert resend")
                        send_alert_by_mail(0, 0, 'READER ALARM RESEND')
                        logging.info("Reader state changed to Red")
                        READERRESENDCOUNT += 1

            except IOError:
                logging.error("IO Error when trying to keep alive")


def send_alert_by_mail(temperature, humidity, alerttype):
    # Import smtplib for the actual sending function
    import smtplib

    # Import the email modules we'll need
    from email.mime.text import MIMEText

    # Open a plain text file for reading.  For this example, assume that
    # the text file contains only ASCII characters.

    msg = MIMEText("Temperature in Server Room: " + str(temperature) + "\r\n" +
                   "Humidity in Server Room: " + str(humidity)
                   )


    msg['Subject'] = 'Server Room Climate ' + alerttype
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP(EMAIL_SERVER)
    s.sendmail(EMAIL_SENDER, [EMAIL_RECEIVER], msg.as_string())
    s.quit()


if __name__ == "__main__":
    logging.info("Starting Climate Client")
    logging.info("Mode is:" + RUN_MODE)
    logging.info("EMail Sender:" + EMAIL_SENDER)
    logging.info("EMail Receiver:" + EMAIL_RECEIVER)
    logging.info("EMail Server:" + EMAIL_SERVER)
    client = Client("ws://127.0.0.1:9000/ws", 5)
