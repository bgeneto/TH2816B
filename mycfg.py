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


__doc__ = """
Create, read and write to config file (.ini file).

Classes:

    MyConfig

Functions:

    get_config()
    get_setting(section, end)
    read_config()

Misc variables:

    __version__
    __author__
"""

import os
import socket
from configparser import ConfigParser

import serial

__author__ = "bgeneto"
__copyright__ = "Copyright 2022, bgeneto"
__credits__ = ["bgeneto"]
__license__ = "GPL"
__maintainer__ = "Bernhard Enders"
__email__ = "b g e n e t o @ d u c k . c o m"
__version__ = "1.0.0"
__modified__ = "20220916"


def get_ip():
    '''get the ip address of the machine'''
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


class MyConfig:
    def __init__(self, cfg_file='config.ini'):
        self.cfg_file = cfg_file
        self.config = None

    def __ini_config(self):
        '''
        Creates an initial config file with default values
        '''
        self.config = ConfigParser()
        self.config.add_section("serial")
        self.config.set("serial", "port", "/dev/serial0")
        self.config.set("serial", "baudrate", "9600")
        self.config.set("serial", "parity", str(serial.PARITY_NONE))
        self.config.set("serial", "stopbits", str(serial.STOPBITS_ONE))
        self.config.set("serial", "bytesize", str(serial.EIGHTBITS))
        self.config.set("serial", "timeout", "1")
        self.config.add_section("web")
        self.config.set("web", "port", "8080")
        self.config.set("web", "ip", get_ip())
        self.config.add_section("experiment")
        self.config.set("experiment", "valves_loop", "4")
        self.config.set("experiment", "sensors_loop", "8")
        self.config.set("experiment", "sensors_duration", "3")
        self.config.add_section("arduino1")
        self.config.set("arduino1", "model", "MEGA")
        self.config.set("arduino1", "sensors", ";;;;;;;")
        self.config.set("arduino1", "valves", ";;;;;;;")
        self.config.set("arduino1", "invert_onoff", "0")
        self.config.add_section("arduino2")
        self.config.set("arduino2", "model", "MEGA")
        self.config.set("arduino2", "sensors", ";;;;;;;")
        self.config.set("arduino2", "valves", ";;;;;;;")
        self.config.set("arduino2", "invert_onoff", "0")
        self.__write_config_file()

    def __write_config_file(self):
        '''
        Write the config file
        '''
        with open(self.cfg_file, "w", encoding='UTF-8') as config_file:
            try:
                self.config.write(config_file)
            except Exception as _:
                print("ERROR: Failed creating initial config file. Check permissions.")
                os._exit(os.EX_CONFIG)

    def get_config(self):
        '''
        Returns the config object
        '''
        if not os.path.isfile(self.cfg_file):
            self.__ini_config()

        self.config = ConfigParser()

        try:
            self.config.read(self.cfg_file)
            # update the ip address
            ip = self.config.get('web', 'ip')
            if ip != get_ip():
                self.config.set('web', 'ip', get_ip())
                self.__write_config_file()
        except Exception as exp:
            print(str(exp))
            # auto (re)create config file in the next run
            self.__ini_config()
            os._exit(os.EX_CONFIG)

        return self.config

    def get_setting(self, section, setting):
        '''
        Return a setting value
        '''
        self.config = self.get_config()
        value = None
        try:
            value = self.config.get(section, setting)
        except Exception as exp:
            print(str(exp))
            pass

        return value

    def read_config(self):
        ser_params = {
            'port': self.get_setting("serial", "port"),
            'baudrate': int(self.get_setting("serial", "baudrate")),
            'parity': str(self.get_setting("serial", "parity")),
            'stopbits': int(self.get_setting("serial", "stopbits")),
            'bytesize': int(self.get_setting("serial", "bytesize")),
            'timeout': int(self.get_setting("serial", "timeout"))
        }
        web_params = {
            'web_port': int(self.get_setting("web", "port")),
            'web_ip': self.get_setting("web", "ip")
        }

        return ser_params, web_params
