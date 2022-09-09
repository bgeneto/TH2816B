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
from datetime import date

import serial
import tornado.concurrent
import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

import mycfg
from colorprint import ColorPrint
from devices import *

__author__ = "Bernhard Enders"
__maintainer__ = "Bernhard Enders"
__email__ = "b g e n e t o @ g m a i l d o t c o m"
__copyright__ = "Copyright 2022, Bernhard Enders"
__license__ = "GPL"
__status__ = "Development"
__version__ = "1.1.2"
__date__ = "20220909"
__year__ = date.today().year

clients = []

input_queue = multiprocessing.Queue()
output_queue = multiprocessing.Queue()

sensors_input_queue = multiprocessing.Queue()
sensors_output_queue = multiprocessing.Queue()

valves_input_queue = multiprocessing.Queue()
valves_output_queue = multiprocessing.Queue()


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        params = {}
        params['__version__'] = __version__
        params['__year__'] = __year__
        self.render('index.html', **params)


class PageHandler(tornado.web.RequestHandler):
    def get(self):
        id = str(self.get_arguments("id")[0])
        params = {}
        params['__version__'] = __version__
        params['__year__'] = __year__
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
        params['a1_model'] = str(cfg.get_setting(
            "arduino1", "model")).split(";")
        params['a2_sensors'] = str(cfg.get_setting(
            "arduino2", "sensors")).split(";")
        params['a2_valves'] = str(cfg.get_setting(
            "arduino2", "valves")).split(";")
        params['a2_model'] = str(cfg.get_setting(
            "arduino2", "model")).split(";")
        # finally render the page with the parameters
        self.render(f'page{id}.html', **params)


class FormHandler(tornado.web.RequestHandler):

    _thread_pool = tornado.concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def post(self):
        # every form most have a unique page_id
        try:
            page_id = int(self.get_body_arguments("page_id")[0])
        except:
            self.redirect(f'page?id=0&status=unknown')
            return
        # treat each form differently
        try:
            if page_id == 0:
                self.start_experiment()
            elif page_id == 1:
                self.experiment_config()
            elif page_id == 2:
                self.arduino_config()
        except Exception as exp:
            ColorPrint.print_fail(str(exp))
            self.redirect(f'page?id={page_id}&status=2')
            return

        self.redirect(f'page?id={page_id}&status=1')
        return

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
        with open(cfg.cfg_file, 'w', encoding='UTF-8') as configfile:
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
        with open(cfg.cfg_file, 'w', encoding='UTF-8') as configfile:
            config.write(configfile)

    @tornado.concurrent.run_on_executor(executor='_thread_pool')
    def start_experiment(self):
        '''start a new experiment'''

        # ensures that this variable is accessible in the other thread
        cfg = mycfg.MyConfig(CFGFN)

        # experiment parameters
        params = dict(
            vloop=int(cfg.get_setting("experiment", "valves_loop")),
            sloop=int(cfg.get_setting("experiment", "sensors_loop")),
            stime=int(cfg.get_setting("experiment", "sensors_duration"))
        )

        # configure and connect all required arduinos
        arduinos = arduinos_connect(cfg)

        # LCR TH2816B serial connection
        lcr = SerialConnection(cfg)

        # run the experiment
        try:
            run_experiment(lcr, arduinos, **params)
        except Exception as exp:
            print(str(exp))
        finally:
            shutdown(lcr, arduinos)


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
        SCRIPT_DIR, "static", "js", "websocket.template.js")
    ws_file = os.path.join(SCRIPT_DIR, "static", "js", "websocket.js")

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
    # find out this script's directory
    SCRIPT_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))
    if len(SCRIPT_DIR) < 1:
        SCRIPT_DIR = '.' + os.sep

    # user defined ini file
    CFGFN = os.path.join(SCRIPT_DIR, "config.ini")

    cfg = mycfg.MyConfig(CFGFN)
    ser_params, web_params = cfg.read_config()

    # setup ip and port
    setup_ws(**web_params)

    # start the serial worker in background (as a deamon)
    #sp = serialworker.SerialProcess(
    #    input_queue, output_queue, serial_port, baud_rate, timeout)
    #sp.daemon = True
    #sp.start()

    # tornado setup
    handlers = [
        (r"/", IndexHandler),
        (r"/page", PageHandler),
        (r"/ws", WebSocketHandler),
        (r"/form", FormHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler,
         {'path':  './static'}),
    ]
    settings = dict(
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        autoreload=True,
        debug=True
    )
    app = tornado.web.Application(
        handlers=handlers,
        settings=settings
    )
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(web_params['web_port'])
    ColorPrint.print_bold("Web server listening on http://{web_ip}:{web_port}".format(
        **web_params))

    main_loop = tornado.ioloop.IOLoop().current()

    # adjust the scheduler_interval according to the frames sent by the serial port
    SCHEDULER_INTERVAL = 100
    scheduler = tornado.ioloop.PeriodicCallback(
        check_queue, SCHEDULER_INTERVAL)

    # tornado main loop
    try:
        scheduler.start()
        main_loop.start()
    except Exception as exp:
        print(str(exp))
        pass
    finally:
        input_queue.close()
        output_queue.close()
        scheduler.stop()
        http_server.stop()
        ColorPrint.print_bold('\nWeb server stopped!')
