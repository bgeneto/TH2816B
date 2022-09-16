#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by bgeneto <b g e n e t o @ g m a i l . c o m>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""TH2816B LCR Meter WebGUI.
Web interface for TH2816B LCR Meter data processing.
Author:   b g e n e t o @ g m a i l . c o m

"""

import json
import multiprocessing
import os
import sys
from datetime import date

import pandas as pd
import plotly
import plotly.express as px
import tornado.autoreload
import tornado.concurrent
import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

import indexer
import mycfg
from devices import *

__author__ = "Bernhard Enders"
__maintainer__ = "Bernhard Enders"
__email__ = "b g e n e t o @ g m a i l d o t c o m"
__copyright__ = "Copyright 2022, Bernhard Enders"
__license__ = "GPL"
__status__ = "Development"
__version__ = "0.1.8"
__date__ = "20220914"
__year__ = date.today().year

# global variables
BASE_EXP_DIR = 'experiments'


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
        params['page_id'] = int(id)
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
            "arduino1", "model"))
        params['a1_onoff'] = str(cfg.get_setting(
            "arduino1", "invert_onoff"))
        params['a2_sensors'] = str(cfg.get_setting(
            "arduino2", "sensors")).split(";")
        params['a2_valves'] = str(cfg.get_setting(
            "arduino2", "valves")).split(";")
        params['a2_model'] = str(cfg.get_setting(
            "arduino2", "model"))
        params['a2_onoff'] = str(cfg.get_setting(
            "arduino2", "invert_onoff"))
        # finally render the page with the parameters
        self.render(f'page{id}.html', **params)


class AjaxHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            data = json.loads(self.request.body)
        except:
            self.write(json.dumps({'status': 'ok'}))
            self.finish()
            return

        # check if log file exists
        log = ''
        if os.path.isfile(data['fname']):
            with open(data['fname'], 'r', encoding='UTF-8') as f:
                log = f.read()

        # json response
        response_to_send = {}
        response_to_send['status'] = 'ok'
        response_to_send['contents'] = log
        self.write(json.dumps(response_to_send))
        self.finish()
        return

    get = post


class FormHandler(tornado.web.RequestHandler):

    _thread_pool = tornado.concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def post(self):
        # every form most have a unique page_id
        status = 1
        form_action = "ok"
        try:
            page_id = int(self.get_body_arguments("page_id")[0])
        except Exception as exp:
            self.redirect(f'page?id=0&status=unknown')
            return
        # treat each form differently
        try:
            if page_id == 0:
                form_action = str(self.get_body_arguments("form_action")[0])
                if form_action == "cancel":
                    # stop tornado server
                    status = 3
                    # change reload watched file
                    try:
                        with open('reload', 'w') as f:
                            f.write(
                                'Change this file in order to force a tornado reload!')
                    except:
                        pass
                else:
                    # start a new experiment
                    self.start_experiment()
            elif page_id == 1:
                self.experiment_config()
            elif page_id == 2:
                self.arduino_config()
        except Exception as exp:
            print(str(exp))
            self.redirect(f'page?id={page_id}&status=2')
            return

        self.redirect(f'page?id={page_id}&status={status}')
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
        try:
            a1_onoff = str(self.get_body_arguments("A1onoff")[0])
        except:
            a1_onoff = '0'
        try:
            a2_onoff = str(self.get_body_arguments("A2onoff")[0])
        except:
            a2_onoff = '0'
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
        config['arduino1']['invert_onoff'] = a1_onoff
        config['arduino2']['invert_onoff'] = a2_onoff
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

    def update_output_dir(self):
        """Update the output directory generating correspoding 'index.html' files"""
        parser = indexer.add_args()
        args = parser.parse_args([BASE_EXP_DIR, '--recursive'])
        indexer.process_dir(args.top_dir, args)

    def write_each_sensor(self, data, output_dir):
        # convert data to dataframe
        data_df = pd.json_normalize(data)
        # write individual csv files for each sensor
        for valve in data[0].keys():
            for sensor in data[0][valve].keys():
                for param in ['primary', 'secondary']:
                    cname = f'{valve}.{sensor}.{param}'
                    df_tmp = data_df[cname].explode(cname)
                    fn = os.path.join(output_dir, param, f'{valve}-{sensor}')
                    # write to csv file
                    df_tmp.to_csv(fn+'.csv')
                    # produce plots
                    fig = px.scatter(df_tmp)
                    fig.update_traces(mode='lines+markers')
                    plotly.offline.plot(fig,
                                        include_plotlyjs='cdn',
                                        filename=fn+'.html')

    def write_all_sensors(self, data, output_dir):
        # convert data to dataframe
        data_df = pd.json_normalize(data)
        # write all sensors to csv file
        for valve in data[0].keys():
            for param in ['primary', 'secondary']:
                valve_df = data_df.filter(regex=f'{valve}.*{param}').copy()
                min_rows = sys.maxsize
                for col in valve_df.columns:
                    rows = valve_df[col].map(len).min()
                    min_rows = rows if rows < min_rows else min_rows
                for idx in valve_df.index:
                    for col in valve_df.columns:
                        valve_df.loc[idx, col] = valve_df[col][idx][0:min_rows]
                valve_df = valve_df.explode(
                    list(valve_df.columns), ignore_index=True)
                fn = os.path.join(output_dir, param, f'{valve}')
                # write to csv file
                valve_df.to_csv(fn+'.csv')
                # produce plots
                fig = px.scatter(valve_df)
                fig.update_traces(mode='lines+markers')
                plotly.offline.plot(fig,
                                    include_plotlyjs='cdn',
                                    filename=fn+'.html')

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
        data = []
        try:
            data = run_experiment(lcr, arduinos, **params)
        except Exception as exp:
            print(str(exp))
        finally:
            shutdown(lcr, arduinos)

        # subdirectories to create
        topdir = None
        subdirs = ['primary', 'secondary']

        # get experiment name from form and write to file
        exp_name = str(self.get_body_arguments('exp_name')[0])
        username = str(self.get_body_arguments('username')[0])
        if len(exp_name) < 1:
            exp_name = 'No desc'
        if len(username) < 1:
            username = ''
        else:
            topdir = username

        # create output directory and subdirectories
        output_dir = create_output_dir(topdir, subdirs)
        try:
            with open(os.path.join(output_dir, 'desc.txt'), 'w', encoding='UTF-8') as fp:
                fp.write(exp_name)
        except Exception as exp:
            print("ERROR: Unable to write experiment description to file")
            os._exit(os.EX_CONFIG)

        # save all collected data to a single json file
        with open(os.path.join(output_dir, 'results.json'), 'w', encoding='ISO-8859-1') as outfile:
            json.dump(data, outfile, indent=2, ensure_ascii=True)

        # save each sensor data to a separate csv file
        self.write_each_sensor(data, output_dir)

        # save all sensor data to a single csv file
        self.write_all_sensors(data, output_dir)

        # finally update index files with new contents
        self.update_output_dir()


def create_output_dir(topdir=None, subdirs=None):
    '''create data output directory'''
    # base output directory
    base_dir = BASE_EXP_DIR if topdir is None else os.path.join(
        BASE_EXP_DIR, topdir)

    # date and time as subdirectory
    timestr = time.strftime("%Y-%m-%d %Hh%Mm%Ss")
    output_dir = os.path.abspath(os.path.join(SCRIPT_DIR, base_dir, timestr))

    # create output directory if not exists
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except Exception as _:
            print("ERROR: Unable to create output directory! Check permissions...")
            # shutdown()
            os._exit(os.EX_CONFIG)

    if subdirs is not None:
        for subdir in subdirs:
            if not os.path.exists(os.path.join(output_dir, subdir)):
                try:
                    os.makedirs(os.path.join(output_dir, subdir))
                except Exception as _:
                    print(
                        "ERROR: Unable to create output subdirectory! Check permissions...")
                    os._exit(os.EX_CONFIG)

    return output_dir


def autoreload_wait(secs=3):
    '''sleep for a given number of seconds'''
    time.sleep(secs)


if __name__ == '__main__':
    # find out this script's directory
    SCRIPT_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))
    if len(SCRIPT_DIR) < 1:
        SCRIPT_DIR = '.' + os.sep

    # user defined ini file
    CFGFN = os.path.join(SCRIPT_DIR, "config.ini")

    cfg = mycfg.MyConfig(CFGFN)
    ser_params, web_params = cfg.read_config()

    # tornado setup
    handlers = [
        (r"/", IndexHandler),
        (r"/page", PageHandler),
        (r"/form", FormHandler),
        (r"/ajax", AjaxHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler,
         {'path': './static'}),
        (fr"/{BASE_EXP_DIR}/(.*)", tornado.web.StaticFileHandler,
         {'path': f'./{BASE_EXP_DIR}', "default_filename": "index.html"}),
    ]
    settings = dict(
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        debug=False,
        autoreload=True,
    )
    app = tornado.web.Application(
        handlers=handlers,
        settings=settings
    )
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(web_params['web_port'])
    print("Web server listening on http://{web_ip}:{web_port}".format(
        **web_params))

    if settings['autoreload']:
        # auto reload tornado server after file changed
        watched_files = (os.path.abspath(os.path.join(BASE_EXP_DIR, 'index.html')),
                         os.path.abspath('reload'),)
        # enable tornado autoreload
        tornado.autoreload.start()
        # add watched file to tornado autoreload feature
        for watched_file in watched_files:
            tornado.autoreload.watch(watched_file)
        # wait a little bit before reloading tornado server
        tornado.autoreload.add_reload_hook(autoreload_wait)

    # tornado main loop
    main_loop = tornado.ioloop.IOLoop().current()

    # start tornado main loop
    try:
        main_loop.start()
    except Exception as exp:
        pass
    finally:
        http_server.stop()
        print('\nWeb server stopped!')
