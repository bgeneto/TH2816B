#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""TH2816B LCR Meter WebGUI.
Web interface for TH2816B LCR Meter data processing.
Author:   b g e n e t o @ g m a i l . c o m
History:  v1.0.0  Initial release
          v1.0.1  Configure options via config (ini) file
"""

import json
import multiprocessing
import os
import socket
import sys
import time
from connections import *
from colorprint import ColorPrint
from configparser import ConfigParser

import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

import serial
import serialworker

__author__ = "Bernhard Enders"
__maintainer__ = "Bernhard Enders"
__email__ = "b g e n e t o @ g m a i l d o t c o m"
__copyright__ = "Copyright 2022, Bernhard Enders"
__license__ = "GPL"
__status__ = "Development"
__version__ = "1.0.1"
__date__ = "20220815"


clients = []

input_queue = multiprocessing.Queue()
output_queue = multiprocessing.Queue()

sensors_input_queue = multiprocessing.Queue()
sensors_output_queue = multiprocessing.Queue()

valves_input_queue = multiprocessing.Queue()
valves_output_queue = multiprocessing.Queue()


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class PageHandler(tornado.web.RequestHandler):
    def get(self):
        id = str(self.get_arguments("id")[0])
        self.render(f'page{id}.html')

# class StaticFileHandler(tornado.web.RequestHandler):
#    def get(self):
#        self.render('websocket.js')


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print('DEBUG: new ws connection request')
        clients.append(self)
        self.write_message(" Serial device connected! ")

    def on_message(self, message):
        print('DEBUG: tornado received from client: {}'.format(json.dumps(message)))
        # self.write_message('ack')
        input_queue.put(message)

    def on_close(self):
        print('DEBUG: ws connection closed')
        clients.remove(self)

    async def aclose(self):
        self.close()
        await self._closed.wait()
        return self.close_code, self.close_reason


# check the queue for pending messages, and reply that to all connected clients
def check_queue():
    if not output_queue.empty():
        message = output_queue.get()
        for c in clients:
            c.write_message(message)


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()

    return ip


def ini_config():
    '''
    Creates an initial config file with default values
    '''
    config = ConfigParser()
    config.add_section("config")
    config.set("config", "port", "/dev/serial0")
    config.set("config", "baudrate", "9600")
    config.set("config", "parity", str(serial.PARITY_NONE))
    config.set("config", "stopbits", str(serial.STOPBITS_ONE))
    config.set("config", "bytesize", str(serial.EIGHTBITS))
    config.set("config", "timeout", "1")
    config.set("config", "web_port", "8080")
    config.set("config", "web_ip", get_ip())

    with open(cfg_file, "w") as config_file:
        try:
            config.write(config_file)
        except Exception as e:
            print("Error creating initial config file. Check permissions.")


def get_config():
    '''
    Returns the config object
    '''
    if not os.path.isfile(cfg_file):
        ini_config()

    config = ConfigParser()

    try:
        config.read(cfg_file)
    except Exception as e:
        print(str(e))
        os._exit(os.EX_CONFIG)

    return config


def get_setting(section, setting):
    '''
    Return a setting value
    '''
    config = get_config()
    try:
        value = config.get(section, setting)
    except Exception as e:
        print(str(e))
        os._exit(os.EX_CONFIG)

    return value


def setup_ws(web_ip, web_port):
    # template and js files
    ws_template = os.path.join(
        script_dir, "static", "js", "websocket.template.js")
    ws_file = os.path.join(script_dir, "static", "js", "websocket.js")

    # check if websocket template file (provided) exists
    if not os.path.isfile(ws_template):
        print('FATAL: template file not found')
        os._exit(os.EX_CONFIG)

    # always write a new websocket javascript file based on ini settings
    with open(ws_template, 'r') as tf:
        data = tf.read()

    # user defined ip and port
    data = data.replace('<web_ip>', web_ip).replace(
        '<web_port>', str(web_port))

    # write up-to-date js file
    with open(ws_file, 'w') as js:
        js.write(data)


def read_config(cfg_file):
    ser_params = {
        'port': get_setting("config", "port"),
        'baudrate': int(get_setting("config", "baudrate")),
        'parity': str(get_setting("config", "parity")),
        'stopbits': int(get_setting("config", "stopbits")),
        'bytesize': int(get_setting("config", "bytesize")),
        'timeout': int(get_setting("config", "timeout"))
    }
    ws_params = {
        'web_port': int(get_setting("config", "web_port")),
        'web_ip': get_setting("config", "web_ip")
    }

    return ser_params, ws_params


if __name__ == '__main__':
    # get user settings
    script_dir = os.path.dirname(sys.argv[0])
    if not len(script_dir):
        script_dir = '.' + os.sep
    cfg_file = os.path.join(script_dir, "config.ini")
    ser_params, ws_params = read_config(cfg_file)

    # setup websockets with ip and port
    setup_ws(**ws_params)

    # start the serial workers in background (as a deamon)
    try:
        ser = serial.Serial(**ser_params)
    except:
        ColorPrint.print_fail('LCR meter not found or serial port in use')
        sys.exit(1)
    sp = serialworker.SerialProcess(input_queue, output_queue, ser)
    sp.daemon = True
    sp.start()

    # arduino firmata connections...
    try:
        sensors_board = ArduinoConnection('sensors', Board.MEGA, id=1)
    except:
        ColorPrint.print_fail('Sensors board not found or in use')
        sys.exit(1)
    try:
        valves_board = ArduinoConnection('valves', Board.UNO, id=2)
    except:
        ColorPrint.print_fail('Valves board not found or in use')
        pass  # sys.exit(1)

    # tornado.options.parse_command_line()
    handlers = [
        (r"/", IndexHandler),
        (r"/page", PageHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler,
         {'path':  './static'}),
        (r"/ws", WebSocketHandler)
    ]
    app = tornado.web.Application(
        handlers=handlers
    )
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(ws_params['web_port'])
    print("INFO: Web server listening on {web_ip}:{web_port}".format(
        **ws_params))

    main_loop = tornado.ioloop.IOLoop().current()
    # adjust the scheduler_interval according to the frames sent by the serial port
    scheduler_interval = 100
    scheduler = tornado.ioloop.PeriodicCallback(
        check_queue, scheduler_interval)
    try:
        scheduler.start()
        main_loop.start()
    except:
        pass
    finally:
        input_queue.close()
        output_queue.close()
        sp.terminate()
        sp.join()
        scheduler.stop()
        http_server.stop()
        # for handler in handlers:
        #    handler.aclose()
        print('\nINFO: Web server stopped')
