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

import json
import os
import sys
import time
import traceback
from enum import Enum

import serial
from pymata4 import pymata4
from serial.threaded import LineReader, ReaderThread
import mycfg

__author__ = "Bernhard Enders"
__maintainer__ = "Bernhard Enders"
__email__ = "b g e n e t o @ g m a i l d o t c o m"
__copyright__ = "Copyright 2022, Bernhard Enders"
__license__ = "GPL"
__version__ = "1.1.4"
__date__ = "20220902"
__status__ = "Development"


class ColorPrint:
    '''print terminal messages in colors '''
    @staticmethod
    def print_fail(message, end='\n'):
        sys.stderr.write('\x1b[1;31m' + 'ERROR: ' + message + '\x1b[0m' + end)

    @staticmethod
    def print_pass(message, end='\n'):
        sys.stdout.write('\x1b[1;32m' + message + '\x1b[0m' + end)

    @staticmethod
    def print_warn(message, end='\n'):
        sys.stderr.write('\x1b[1;33m' + 'WARNING: ' +
                         message + '\x1b[0m' + end)

    @staticmethod
    def print_info(message, end='\n'):
        sys.stdout.write('\x1b[1;34m' + message + '\x1b[0m' + end)

    @staticmethod
    def print_bold(message, end='\n'):
        sys.stdout.write('\x1b[1;37m' + message + '\x1b[0m' + end)


class Board(Enum):
    '''arduino boards digital pins config'''
    UNO = 14  # number of digital pins
    MEGA = 54  # number of digital pins
    ON = 1    # digital pin on
    OFF = 0   # digital pin off


class ArduinoConnection:
    '''Remember to set/change the ARDUINO_INSTANCE_ID in the
       FirmataExpress before uploading the Arduino firmware
       Instructions to set the instance-id here:
       https://mryslab.github.io/pymata-express/firmata_express/#setting-the-firmataexpress-instance-id
    '''

    def __init__(self, name, model, id=1):
        ColorPrint.print_info("---------------------------------------------")
        ColorPrint.print_info(f" Searching '{name}' device...               ")
        ColorPrint.print_info("---------------------------------------------")
        self.name = name
        self.model = model
        self.id = id
        self.valves_pins = []
        self.sensors_pins = []
        self.connection_attempt()

    def connect(self):
        '''instantiate pymata4'''
        wait = 3  # seconds
        ser = pymata4.Pymata4(arduino_instance_id=self.id,
                              arduino_wait=wait)
        ColorPrint.print_pass("---------------------------------------------")
        ColorPrint.print_pass(f" Device '{self.name}' connected successfully")
        ColorPrint.print_pass("---------------------------------------------")

        return ser

    def connection_attempt(self):
        '''attempts to connect to the serial port'''
        attempts = 4  # max number of connections attempts
        while attempts > 0:
            attempts -= 1
            try:
                self.ser = self.connect()
                break
            except Exception as _:
                ColorPrint.print_warn(
                    f"Device '{self.name}' not found or serial port in use!")
                time.sleep(1)  # wait before next connection attempt
        else:
            ColorPrint.print_fail(
                f"Unable to connect to device named '{self.name}'. Exiting...")
            shutdown()
            sys.exit(1)

    def switch_all_off(self):
        '''switch all pins off'''
        for pins in self.valves_pins:
            for pin in pins:
                self.ser.digital_write(pin, OFF)
                time.sleep(0.1)
        for pins in self.sensors_pins:
            for pin in pins:
                self.ser.digital_write(pin, OFF)
                time.sleep(0.1)

    def _analog_to_digital(self, num):
        '''When configuring an analog input pin as a digital input/output,
        you must use the pin's digital pin number equivalent. For example,
        on an Arduino Uno, if you wish to use pin A0 as a digital pin,
        the digital pin number equivalent is 14. In general,
        to find the digital equivalent of pin A0 for your specific
        Arduino board type, the algorithm is:

            digital_pin_number = analog_pin_number + number of digital pins
        '''
        return int(num + self.model.value)

    def _convert_pin_number(self, pins: list):
        '''convert analog pin to digital if required and
           use the correct pin numbering instead of board numbering/naming'''
        if isinstance(pins, list):
            for idx, pin in enumerate(pins):
                if pin[0].lower() == 'A'.lower():
                    pins[idx] = self._analog_to_digital(int(pin[1:]))
                elif pin[0].lower() == 'D'.lower():
                    pins[idx] = int(pins[1:])
        else:  # unexpected type
            raise TypeError

        return pins

    def _init_pins(self, pins: list) -> list:
        '''convert pin name scheme, set output mode and turn off all pins'''

        # unexpected type
        if not isinstance(pins, list):
            raise TypeError

        proper_pins = []
        for idx, pin in enumerate(pins):
            if not isinstance(pin, list):
                pins[idx] = [pin]
            # convert pin name scheme, set output mode and turn off pins
            proper_pins.append(self._convert_pin_number(pin))
            # set all pins as digital output
            for pin in proper_pins:
                self.ser.set_pin_mode_digital_output(pin)
                # turn off all pins at initialization
                self.ser.digital_write(pin, OFF)
                time.sleep(0.1)  # lets be cautious and wait a little bit

        return proper_pins

    def configure_pins(self, valves_pins=None, sensors_pins=None):
        '''set proper pin number and configure required pins as digital output'''

        if valves_pins is not None:
            self.valves_pins = self._init_pins(valves_pins)

        if sensors_pins is not None:
            self.sensors_pins = self._init_pins(sensors_pins)

    def switch_onoff(self, pins_lst: list, pins_pos: list, wait: float = 0.0) -> None:
        '''turn on selected pins at pins_pos and turn off all others'''
        # check if pins_pos is a list
        if not isinstance(pins_pos, list):
            raise TypeError
        # turn on select positions and turn off all others
        for idx, pins in enumerate(pins_lst):
            if idx in pins_pos:
                ColorPrint.print_info(f"Turning ON pin {pins}")
                for pin in pins:
                    self.ser.digital_write(pin, ON)
                    time.sleep(0.1)
            else:
                for pin in pins:
                    self.ser.digital_write(pin, OFF)
                    time.sleep(0.1)
        # global wait (if requested)
        time.sleep(wait)

    def sensors_loop(self, sensors, count):
        '''loop through all the selected sensors'''

        # LCR meter sampling rate
        #reading_rate = 1/10.0

        # LCR meter sampling duration (in seconds) per sensor
        reading_time = 2

        # LCR meter primary and secondary parameters
        cols = {'primary': [], 'secondary': []}

        # data structures to store the readings
        sensors_lst = [f'S{idx}' for idx in sensors]
        sensors_dict = {key: cols for key in sensors_lst}

        # received data lists
        #str_lst = ['']*len(sensors)

        while count > 0:
            count = count - 1
            for sensor in sensors:
                # first thing is to turn on the sensor and wait for it to settle
                self.switch_onoff(self.sensors_pins, [sensor])
                time.sleep(1)
                # now we empty the input buffer list
                lcr_meter.protocol.received_lines = []
                # wait 'reading_time' seconds
                # for __ in range(int(reading_time/reading_rate)):
                #    time.sleep(reading_rate)
                time.sleep(reading_time)
                lines = lcr_meter.protocol.received_lines
                for line in lines:
                    pri, sec = line.split(',')
                    sensors_dict[f'S{sensor}']['primary'].append(
                        float(pri))
                    sensors_dict[f'S{sensor}']['secondary'].append(
                        float(sec))
                # rx_str = '\n'.join(
                #    lcr_meter.protocol.received_lines) + '\n'
                #str_lst[sensor] += rx_str

        # format the data into a list of dataframes
        #lst_df = []
        # for pos, data in enumerate(str_lst):
        #    lst_df.insert(pos, pd.read_csv(
        #        StringIO(data), sep=",", header=None, names=cols))

        return sensors_dict


class SerialConnection:
    '''threaded serial port connection'''

    def __init__(self, name, port,
                 baudrate=9600,
                 parity=serial.PARITY_NONE,
                 stopbits=serial.STOPBITS_ONE,
                 bytesize=serial.EIGHTBITS,
                 timeout=1):

        ColorPrint.print_info("---------------------------------------------")
        ColorPrint.print_info(f" Searching '{name}' device...               ")
        ColorPrint.print_info("---------------------------------------------")

        # generic device parameters
        self.name = name
        self.ser = None
        self.transport = None
        self.protocol = None
        self.thread = None

        # serial connection parameters
        self.port = port
        self.url = port
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.timeout = timeout
        self.ser_parameters = {'url': self.url,
                               'baudrate': self.baudrate,
                               'stopbits': self.stopbits,
                               'bytesize': self.bytesize,
                               'timeout': self.timeout
                               }
        # perform connection attempt
        self.connection_attempt()

    def connect(self, wait=None):
        '''make a connection waiting device to get ready if asked'''
        # make the serial connection
        self.ser = serial.serial_for_url(
            **self.ser_parameters, do_not_open=False)

        # start the serial monitoring thread
        self.thread = ReaderThread(self.ser, SerialReaderProtocolLine)
        self.thread.start()
        self.transport, self.protocol = self.thread.connect()

        # wait device to became ready
        if wait is not None:
            ColorPrint.print_warn(
                f"Waiting serial port ({self.name}) to became ready...")
            if isinstance(wait, int) and wait > 0:
                time.sleep(wait)
            elif isinstance(wait, str):
                # 30s wait timeout
                t_end = time.time() + 30
                while time.time() < t_end:
                    if str(wait.lower()) in self.protocol.received_lines:
                        break
                else:
                    ColorPrint.print_fail(
                        f"***ERROR: Serial port ({self.name}) not ready, timed out!")
                    raise TimeoutError

        ColorPrint.print_pass("---------------------------------------------")
        ColorPrint.print_pass(f" Device '{self.name}' connected successfully")
        ColorPrint.print_pass("---------------------------------------------")

    def connection_attempt(self):
        '''attempts to connect to the serial port'''
        attempts = 4  # max number of connections attempts
        while attempts > 0:
            attempts -= 1
            try:
                self.connect()
                # set LCR trigger to manual/software controlled mode
                time.sleep(0.2)
                self.protocol.write_line('APER MED,5')
                time.sleep(0.2)
                self.protocol.write_line('TRIG:SOUR INT')
                break
            except Exception as _:
                ColorPrint.print_warn(
                    f"Device '{self.name}' not found or serial port in use!")
                time.sleep(1)  # wait before next connection attempt
        else:
            ColorPrint.print_fail(
                f"Unable to connect to device named '{self.name}'. Exiting...")
            shutdown()
            sys.exit(1)

    def close(self):
        '''Stop and close serial monintoring thread'''
        self.thread.close()
        self.ser.close()


class SerialReaderProtocolLine(LineReader):
    '''read lines of data'''
    TERMINATOR = b'\n'
    ENCODING = 'utf-8'

    def __init__(self):
        super(SerialReaderProtocolLine, self).__init__()
        self.received_lines = []

    def connection_made(self, transport):
        """Called when reader thread is started"""
        super(SerialReaderProtocolLine, self).connection_made(transport)
        self.transport.serial.reset_input_buffer()

    def handle_line(self, line):
        """New line waiting to be processed"""
        #sys.stdout.write(f'Line received: {repr(line)}')
        # line = str(int(round(time.time() * 1000))) + ',' + line # add timestamp
        self.received_lines.append(line)

    def connection_lost(self, exc):
        if exc:
            traceback.print_exc(exc)
        ColorPrint.print_fail('Serial port closed\n')


def shutdown():
    '''ends serial connections, closes active threads and turn off all valves and sensors'''
    try:
        # return lcr meter to manual trigger mode (stops auto measurement)
        lcr_meter.protocol.write_line('TRIG:SOUR MAN')
        time.sleep(0.1)
        lcr_meter.close()
        for arduino in arduinos.values():
            # turn off all pin energy
            arduino.switch_all_off()
            time.sleep(0.1)
            arduino.ser.shutdown()
    except Exception as exc:
        traceback.print_exc(exc)


def create_output_dir():
    '''create data output directory'''
    # base output directory
    base_dir = 'experiments'

    # date and time as subdirectory
    timestr = time.strftime("%Y-%m-%d %Hh%Mm%Ss")

    # create output directory if not exists
    output_dir = os.path.abspath(os.path.join(base_dir, timestr))
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except Exception as _:
            ColorPrint.print_fail("Unable to create output directory!")
            shutdown()
            sys.exit(1)

    return output_dir


def run_experiment(scycles, vcycles):
    '''run the experiment'''

    # wait before starting a measurement
    time.sleep(1)

    # choose valves to use (default: all)
    num_arduinos = len(arduinos)

    if num_arduinos == 1:
        arduino_sensors = arduinos['all']
        arduino_valves = arduinos['all']
        valves_pos = range(len(arduinos['all'].valves_pins))
        sensors_pos = range(len(arduinos['all'].sensors_pins))
    else:
        arduino_sensors = arduinos['sensors']
        arduino_valves = arduinos['valves']
        sensors_pos = range(len(arduinos['sensors'].sensors_pins))
        valves_pos = range(len(arduinos['valves'].valves_pins))

    # store retrieved data in a list of dictionaries
    data = []
    valves_lst = [f'V{idx}' for idx in valves_pos]
    valves_dict = {key: {} for key in valves_lst}
    print(valves_dict)

    # main experiment loop
    for _ in range(vcycles):
        for vpos in valves_pos:
            arduino_valves.switch_onoff(arduino_valves.valves_pins, [vpos])
            valves_dict[f'V{vpos}'] = arduino_sensors.sensors_loop(
                sensors_pos, scycles)
        # append to list only after a valve cycle is completed
        data.append(valves_dict)

    # create output directory if not exists
    output_dir = create_output_dir()

    # save all collected data to a single json file
    with open(os.path.join(output_dir, 'results.json'), 'w', encoding='UTF-8') as outfile:
        json.dump(data, outfile, ensure_ascii=False)

    # convert to dataframe
    #data_df = pd.json_normalize(data)

    # save data to several csv files
    # for valve in valves:
    # for param in ['primary', 'secondary']:
    # print(data[valve][0][param])
    # write two files with all sensors data
    # sensors_df = pd.concat(
    #    [x[param] for x in data[valve][:]], ignore_index=True, axis=1)
    # fname = os.path.join(
    #    output_dir, f'v{valve}_{param}_all_sensors.csv')
    #sensors_df.to_csv(fname, index=False)
    #    for sensor in sensors:
    #        # write one
    #        fname = os.path.join(output_dir, f'v{valve}s{sensor}.csv')
    #        data[valve][sensor].to_csv(fname, index=False)


def arduinos_connect():
    '''connect to arduinos'''
    arduino_model = str(cfg.get_setting("arduino2", "model"))
    arduino_board = Board.MEGA if arduino_model == 'MEGA' else Board.UNO
    arduino_sensors = str(cfg.get_setting("arduino2", "sensors")).split(';')
    arduino_valves = str(cfg.get_setting("arduino2", "valves")).split(';')
    empty_sensors = all(len(elem) == 0 for elem in arduino_sensors)
    empty_valves = all(len(elem) == 0 for elem in arduino_valves)
    if empty_sensors and empty_valves:
        arduino_model = str(cfg.get_setting("arduino1", "model"))
        arduino_board = Board.MEGA if arduino_model == 'MEGA' else Board.UNO
        arduino_sensors = str(cfg.get_setting(
            "arduino1", "sensors")).split(';')
        arduino_valves = str(cfg.get_setting("arduino1", "valves")).split(';')
        arduinos['all'] = ArduinoConnection(
            'valves and sensors', arduino_board, id=1)
        arduinos['all'].configure_pins(
            valves_pins=arduino_valves, sensors_pins=arduino_sensors)
    else:  # two arduinos
        if empty_sensors:
            arduinos['valves'] = ArduinoConnection(
                'valves', arduino_board, id=2)
            arduinos['valves'].configure_pins(valves_pins=arduino_valves)
            # get other arduino configuration
            arduino_model = str(cfg.get_setting("arduino1", "model"))
            arduino_board = Board.MEGA if arduino_model == 'MEGA' else Board.UNO
            arduino_sensors = str(cfg.get_setting(
                "arduino1", "sensors")).split(';')
            arduinos['sensors'] = ArduinoConnection(
                'sensors', arduino_board, id=1)
            arduinos['sensors'].configure_pins(sensors_pins=arduino_sensors)
        elif empty_valves:
            arduinos['sensors'] = ArduinoConnection(
                'sensors', arduino_board, id=2)
            arduinos['sensors'].configure_pins(sensors_pins=arduino_sensors)
            # get other arduino configuration
            arduino_model = str(cfg.get_setting("arduino1", "model"))
            arduino_board = Board.MEGA if arduino_model == 'MEGA' else Board.UNO
            arduino_valves = str(cfg.get_setting(
                "arduino1", "valves")).split(';')
            arduinos['valves'] = ArduinoConnection(
                'valves', arduino_board, id=1)
            arduinos['valves'].configure_pins(valves_pins=arduino_valves)

    return arduinos


if __name__ == '__main__':

    # global constants
    ON = 1
    OFF = 2

    # this script directory path
    script_dir = os.path.dirname(sys.argv[0])

    # config file path and name
    cfg_file = os.path.join(script_dir, "config.ini")
    cfg = mycfg.MyConfig(cfg_file)

    # serial port configuration
    serial_port = str(cfg.get_setting("config", "port"))
    serial_baudrate = int(cfg.get_setting("config", "baudrate"))

    # experiment configuration
    valves_loop = int(cfg.get_setting("experiment", "valves_loop"))
    sensors_loop = int(cfg.get_setting("experiment", "sensors_loop"))
    sensors_duration = int(cfg.get_setting("experiment", "sensors_duration"))

    # configure and connect all required arduinos
    arduinos = arduinos_connect()

    # LCR TH2816B serial connection
    lcr_meter = SerialConnection('lcr', serial_port, baudrate=serial_baudrate)

    # run the experiment
    try:
        run_experiment(scycles=sensors_loop, vcycles=valves_loop)
    except KeyboardInterrupt:
        ColorPrint.print_fail("\nProgram interrupted!")
    finally:
        shutdown()

    sys.exit(0)
