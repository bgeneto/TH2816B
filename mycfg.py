import os
import socket
from configparser import ConfigParser

import serial


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

    def ini_config(self):
        '''
        Creates an initial config file with default values
        '''
        self.config = ConfigParser()
        self.config.add_section("config")
        self.config.set("config", "port", "/dev/serial0")
        self.config.set("config", "baudrate", "9600")
        self.config.set("config", "parity", str(serial.PARITY_NONE))
        self.config.set("config", "stopbits", str(serial.STOPBITS_ONE))
        self.config.set("config", "bytesize", str(serial.EIGHTBITS))
        self.config.set("config", "timeout", "1")
        self.config.set("config", "web_port", "8080")
        self.config.set("config", "web_ip", get_ip())
        self.config.add_section("experiment")
        self.config.set("experiment", "valves_loop", "4")
        self.config.set("experiment", "sensors_loop", "10")
        self.config.set("experiment", "sensors_duration", "2")
        self.config.add_section("arduino1")
        self.config.set("arduino1", "model", "MEGA")
        self.config.set("arduino1", "sensors", ";;;;;;;")
        self.config.set("arduino1", "valves", ";;;;;;;")
        self.config.add_section("arduino2")
        self.config.set("arduino2", "model", "MEGA")
        self.config.set("arduino2", "sensors", ";;;;;;;")
        self.config.set("arduino2", "valves", ";;;;;;;")
        with open(self.cfg_file, "w", encoding='UTF-8') as config_file:
            try:
                self.config.write(config_file)
            except Exception as _:
                print("Error creating initial config file. Check permissions.")
                os._exit(os.EX_CONFIG)

    def get_config(self):
        '''
        Returns the config object
        '''
        if not os.path.isfile(self.cfg_file):
            self.ini_config()

        self.config = ConfigParser()

        try:
            self.config.read(self.cfg_file)
        except Exception as exp:
            print(str(exp))
            os._exit(os.EX_CONFIG)

        return self.config

    def get_setting(self, section, setting):
        '''
        Return a setting value
        '''
        self.config = self.get_config()
        try:
            value = self.config.get(section, setting)
        except Exception as exp:
            print(str(exp))
            os._exit(os.EX_CONFIG)

        return value

    def read_config(self):
        ser_params = {
            'port': self.get_setting("config", "port"),
            'baudrate': int(self.get_setting("config", "baudrate")),
            'parity': str(self.get_setting("config", "parity")),
            'stopbits': int(self.get_setting("config", "stopbits")),
            'bytesize': int(self.get_setting("config", "bytesize")),
            'timeout': int(self.get_setting("config", "timeout"))
        }
        ws_params = {
            'web_port': int(self.get_setting("config", "web_port")),
            'web_ip': self.get_setting("config", "web_ip")
        }

        return ser_params, ws_params