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
import sys

import serial
import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

from devices import *
import mycfg

__author__ = "Bernhard Enders"
__maintainer__ = "Bernhard Enders"
__email__ = "b g e n e t o @ g m a i l d o t c o m"
__copyright__ = "Copyright 2022, Bernhard Enders"
__license__ = "GPL"
__status__ = "Development"
__version__ = "1.1.1"
__date__ = "20220905"


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
        params = {}
        params['valves_loop'] = int(cfg.get_setting(
            "experiment", "valves_loop"))
        params['sensors_loop'] = int(cfg.get_setting(
            "experiment", "sensors_loop"))
        params['sensors_duration'] = int(cfg.get_setting(
            "experiment", "sensors_duration"))
        params['a1_sensors'] = ['']*8
        params['a1_valves'] = ['']*8
        params['a2_sensors'] = ['']*8
        params['a2_valves'] = ['']*8
        params['a1_sensors'] = str(cfg.get_setting(
            "arduino1", "sensors")).split(";")
        params['a1_valves'] = str(cfg.get_setting(
            "arduino1", "valves")).split(";")
        params['a2_sensors'] = str(cfg.get_setting(
            "arduino2", "sensors")).split(";")
        params['a2_valves'] = str(cfg.get_setting(
            "arduino2", "valves")).split(";")
        # finally render the page with the parameters
        self.render(f'page{id}.html', **params)


class FormHandler(tornado.web.RequestHandler):

    def post(self):
        page_id = int(self.get_body_arguments("page_id")[0])
        try:
            if page_id == 1:
                self.experiment_config()
            elif page_id == 2:
                self.arduino_config()
        except:
            self.redirect(f'page?id={page_id}&status=2')
            return False

        self.redirect(f'page?id={page_id}&status=1')
        return True

    get = post

    def arduino_config(self):
        config = cfg.get_config()
        config['arduino1'] = {}
        config['arduino2'] = {}
        # write arduino parameters to file
        a1_sensors_lst = []
        a1_valves_lst = []
        a2_sensors_lst = []
        a2_valves_lst = []
        a1_model = str(self.get_body_arguments("A1M")[0])
        a2_model = str(self.get_body_arguments("A2M")[0])
        for idx in range(8):
            a1_sensors_lst.append(
                str(self.get_body_arguments(f"A1S{idx}")[0]))
            a1_valves_lst.append(
                str(self.get_body_arguments(f"A1V{idx}")[0]))
            a2_sensors_lst.append(
                str(self.get_body_arguments(f"A2S{idx}")[0]))
            a2_valves_lst.append(
                str(self.get_body_arguments(f"A2V{idx}")[0]))
        config['arduino1']['model'] = a1_model
        config['arduino2']['model'] = a2_model
        config['arduino1']['sensors'] = ";".join(
            a1_sensors_lst).replace(' ', '')
        config['arduino1']['valves'] = ";".join(a1_valves_lst).replace(' ', '')
        config['arduino2']['sensors'] = ";".join(
            a2_sensors_lst).replace(' ', '')
        config['arduino2']['valves'] = ";".join(a2_valves_lst).replace(' ', '')
        with open(cfg_file, 'w', encoding='UTF-8') as configfile:
            config.write(configfile)

    def experiment_config(self):
        config = cfg.get_config()
        config['experiment'] = {}
        # write experiment parameters to file
        valves_loop = str(self.get_body_arguments('valves_loop')[0])
        sensors_loop = str(self.get_body_arguments('sensors_loop')[0])
        sensors_duration = str(self.get_body_arguments('sensors_duration')[0])
        config['experiment']['valves_loop'] = valves_loop
        config['experiment']['sensors_loop'] = sensors_loop
        config['experiment']['sensors_duration'] = sensors_duration
        with open(cfg_file, 'w', encoding='UTF-8') as configfile:
            config.write(configfile)


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


def check_queue():
    '''check the queue for pending messages, and reply that to all connected clients'''
    if not output_queue.empty():
        message = output_queue.get()
        for c in clients:
            c.write_message(message)


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


if __name__ == '__main__':
    # get user settings
    script_dir = os.path.dirname(sys.argv[0])
    if not len(script_dir):
        script_dir = '.' + os.sep
    cfg_file = os.path.join(script_dir, "config.ini")
    cfg = mycfg.MyConfig(cfg_file)
    ser_params, ws_params = cfg.read_config()

    # setup websockets with ip and port
    setup_ws(**ws_params)

    # global constants
    ON = 1
    OFF = 2

    # # LCR TH2816B connection
    # lcr_meter = SerialConnection('lcr', "/dev/serial0", timeout=1)
    # lcr_meter.daemon = True
    # lcr_meter.start()

    # # arduino connection
    # valves_arduino = ArduinoConnection('valves', Board.MEGA, id=1)
    # sensors_arduino = ArduinoConnection('sensors', Board.UNO, id=2)

    # # run the experiment
    # experiment()

    # tornado.options.parse_command_line()
    handlers = [
        (r"/", IndexHandler),
        (r"/page", PageHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler,
         {'path':  './static'}),
        (r"/ws", WebSocketHandler),
        (r"/form", FormHandler)
    ]
    app = tornado.web.Application(
        handlers=handlers,
        debug=True,
        autoreload=True
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
        lcr_meter.terminate()
        lcr_meter.join()
        scheduler.stop()
        http_server.stop()
        # for handler in handlers:
        #    handler.aclose()
        print('\nINFO: Web server stopped')
