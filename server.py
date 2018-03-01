#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.httpserver
import tornado.websocket
import tornado.ioloop
# from tornado.ioloop import PeriodicCallback
import tornado.web
# from random import randint  # Random generator
import os
import time
import logging


# Config
port = 9000  # Websocket Port
timeInterval = 2000  # Milliseconds


class IndexHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("index.html", history=WSHandler.cache)


class WSHandler(tornado.websocket.WebSocketHandler):
    waiters = set()
    cache = []
    cache_size = 288
    last_cache = time.time()

    # check_origin fixes an error 403 with Tornado
    # http://stackoverflow.com/questions/24851207/tornado-403-get-warning-when-opening-websocket
    def check_origin(self, origin):
        return True

    def open(self):
        WSHandler.waiters.add(self)
        logging.info("A connection opened")

    def on_message(self, message):
        WSHandler.update_cache(message)
        WSHandler.send_updates(message)
        logging.info(message)

    def on_close(self):
        WSHandler.waiters.remove(self)
        logging.info("A connection closed")

    @classmethod
    def send_updates(cls, message):
        for waiter in cls.waiters:
            try:
                waiter.write_message(message)
            except:
                logging.error("Could not send message to everyone")

    @classmethod
    def update_cache(cls, message):
        rightnow = time.time()
        if (rightnow - cls.last_cache) > 15 or cls.cache.__len__() == 0:
            cls.last_cache = rightnow
            cls.cache.append(message)
            if len(cls.cache) > cls.cache_size:
                cls.cache = cls.cache[-cls.cache_size:]


application = tornado.web.Application(
    [
        (r'/', IndexHandler),
        (r'/ws', WSHandler),
    ],
    static_path=os.path.join(os.path.dirname(__file__), "static"), )

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print("Server stopped -> CTRL+C was pressed")