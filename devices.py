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

import copy
import sys
import time
import traceback
from datetime import datetime
from enum import Enum
from typing import Dict

import serial
from pymata4 import pymata4
from serial.threaded import LineReader, ReaderThread

from colorprint import ColorPrint

__author__ = "Bernhard Enders"
__maintainer__ = "Bernhard Enders"
__email__ = "b g e n e t o @ g m a i l d o t c o m"
__copyright__ = "Copyright 2022, Bernhard Enders"
__license__ = "GPL"
__version__ = "0.1.13"
__date__ = "20220914"
__status__ = "Development"

# global constants
global_counter = 0
cprint = ColorPrint(__name__ + '.log')


class Board(Enum):
    '''arduino boards digital pins config'''
    UNO = 14  # number of digital pins
    MEGA = 54  # number of digital pins


class ArduinoConnection:
    '''Remember to set/change the ARDUINO_INSTANCE_ID in the
       FirmataExpress before uploading the Arduino firmware
       Instructions to set the instance-id here:
       https://mryslab.github.io/pymata-express/firmata_express/#setting-the-firmataexpress-instance-id
    '''

    def __init__(self, name, model, id=1):
        cprint.info(f" Searching '{name}' device...               ")
        self.name = name
        self.model = model
        self.id = id
        self.ON = 2
        self.OFF = 1
        self.valves_pins = []
        self.sensors_pins = []
        self.connection_attempt()

    def connect(self):
        '''instantiate pymata4'''
        wait = 3  # seconds
        ser = pymata4.Pymata4(arduino_instance_id=self.id,
                              arduino_wait=wait)
        cprint.success(f" Device '{self.name}' connected successfully")

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
                cprint.warn(
                    f"Device '{self.name}' not found or serial port in use!")
                time.sleep(1)  # wait before next connection attempt
        else:
            cprint.fail(
                f"Unable to connect to device named '{self.name}'. Exiting...")
            # shutdown()
            sys.exit(1)

    def switch_all_off(self):
        '''switch all pins off'''
        for pins in self.valves_pins:
            for pin in pins:
                self.ser.digital_write(pin, self.OFF)
                time.sleep(0.1)
        for pins in self.sensors_pins:
            for pin in pins:
                self.ser.digital_write(pin, self.OFF)
                time.sleep(0.1)

    def _analog_to_digital(self, num) -> int:
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
                for p in pin.split(','):
                    # remove empty pin
                    if len(p) < 1:
                        del pins[idx]
                        continue
                    try:
                        # try to convert to int
                        p = int(p)
                        pins[idx] = p
                    except ValueError:
                        if p[0].lower() == 'A'.lower():
                            pins[idx] = self._analog_to_digital(int(p[1:]))
                        elif p[0].lower() == 'D'.lower():
                            pins[idx] = int(p[1:])
        else:  # unexpected type
            raise TypeError

        return pins

    def _init_pins(self, pins: list) -> list:
        '''convert pin name scheme, set output mode and turn off all pins'''

        for idx, pin in enumerate(pins):
            if not isinstance(pin, list):
                pins[idx] = [pin]

        proper_pins = []
        for idx, pin in enumerate(pins):
            # convert pin name scheme, set output mode and turn off pins
            proper_pins.append(self._convert_pin_number(pin))

        # set all pins as digital output
        for pins in proper_pins:
            for pin in pins:
                self.ser.set_pin_mode_digital_output(pin)
                # turn off all pins at initialization
                self.ser.digital_write(pin, self.OFF)
                time.sleep(0.1)  # lets be cautious and wait a little bit

        return proper_pins

    def invert_onoff(self):
        '''invert ON and OFF logic for arduinos relay'''
        cprint.warn('inverting ON and OFF relay logic')
        self.ON, self.OFF = self.OFF, self.ON

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
            time.sleep(0.1)
            if idx in pins_pos:
                for pin in pins:
                    cprint.info(f"Turning ON pin {pin}")
                    self.ser.digital_write(pin, self.ON)
            else:
                for pin in pins:
                    #cprint.info(f"Turning OFF pin {pin}")
                    self.ser.digital_write(pin, self.OFF)
        # global wait (if requested)
        time.sleep(wait)

    def sensors_loop(self, lcr_meter, sensors_pos, sloop, vloop, rtime):
        '''loop through all the selected sensors'''
        global global_counter

        # LCR meter primary and secondary parameters
        params = {'primary': [], 'secondary': []}

        # data structures to store the readings
        sensors_lst = [f'S{idx}' for idx in sensors_pos]
        sensors_dict = {sensor: copy.deepcopy(
            params) for sensor in copy.deepcopy(sensors_lst)}

        nsensors = len(sensors_pos)
        for _ in range(sloop):
            for spos in sensors_pos:
                global_counter += 1
                # first thing is to turn on the sensor and wait for it to settle
                self.switch_onoff(self.sensors_pins, [spos])
                # wait for the sensor to settle before taking a reading
                time.sleep(0.5)
                percent = round(100.0*global_counter/(nsensors*sloop*vloop))
                cprint.normal(f'Measuring... {percent}% completed')
                # now we empty the input buffer list
                lcr_meter.transport.serial.flush()
                lcr_meter.protocol.received_lines = []
                # read duration
                time.sleep(rtime)
                lines = copy.deepcopy(lcr_meter.protocol.received_lines)
                for line in lines:
                    pri, sec = line.split(',')
                    sensors_dict[f'S{spos}']['primary'].append(
                        float(pri))
                    sensors_dict[f'S{spos}']['secondary'].append(
                        float(sec))

        return sensors_dict


class SerialConnection:
    '''threaded serial port connection'''

    def __init__(self, cfg):

        self.name = 'LCR'

        cprint.info(f" Searching '{self.name}' device...        ")

        # generic device parameters
        self.ser = None
        self.transport = None
        self.protocol = None
        self.thread = None

        # serial connection parameters
        self.port = str(cfg.get_setting("serial", "port"))
        self.url = str(cfg.get_setting("serial", "port"))
        self.baudrate = int(cfg.get_setting("serial", "baudrate"))
        self.parity = str(cfg.get_setting("serial", "parity"))
        self.stopbits = int(cfg.get_setting("serial", "stopbits"))
        self.bytesize = int(cfg.get_setting("serial", "bytesize"))
        self.timeout = int(cfg.get_setting("serial", "timeout"))
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
            cprint.warn(
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
                    cprint.fail(
                        f"***ERROR: Serial port ({self.name}) not ready, timed out!")
                    raise TimeoutError

        cprint.success(f" Device '{self.name}' connected successfully")

    def connection_attempt(self):
        '''attempts to connect to the serial port'''
        attempts = 4  # max number of connections attempts
        while attempts > 0:
            attempts -= 1
            try:
                self.connect()
                # set LCR trigger to manual/software controlled mode
                time.sleep(0.2)
                self.protocol.write_line('APER SLOW')
                time.sleep(0.2)
                self.protocol.write_line('TRIG:SOUR INT')
                break
            except Exception as _:
                cprint.warn(
                    f"Device '{self.name}' not found or serial port in use!")
                time.sleep(1)  # wait before next connection attempt
        else:
            cprint.fail(
                f"Unable to connect to device named '{self.name}'. Exiting...")
            # shutdown()
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
        cprint.warn('Serial port closed')


def shutdown(lcr_meter, arduinos):
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
            cprint.warn(f'Arduino {arduino.name} shutdown')
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cprint.bold(f'..:: Experiment ended at {now} ::..')
    except Exception as exc:
        traceback.print_exc(exc)


def run_experiment(lcr_meter, arduinos, vloop, sloop, stime):
    '''run the experiment'''
    global global_counter
    global_counter = 0

    # wait before starting a measurement
    time.sleep(1)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cprint.bold(f'..:: Experiment started at {now}  ::..')

    # find out number of arduinos configured
    if len(arduinos) == 1:
        arduino_sensors = arduinos['all']
        arduino_valves = arduinos['all']
    else:
        arduino_sensors = arduinos['sensors']
        arduino_valves = arduinos['valves']

    # choose which sensors and valves to use (default: all)
    sensors_pos = range(len(arduino_sensors.sensors_pins))
    valves_pos = range(len(arduino_valves.valves_pins))

    # check if arduino is configured
    empty_sensors = all(
        len(elem) == 0 for elem in arduino_sensors.sensors_pins)
    empty_valves = all(len(elem) == 0 for elem in arduino_valves.valves_pins)
    if empty_sensors or empty_valves:
        cprint.fail('Please configure arduino pins first!')
        sys.exit(1)

    # store retrieved data in a list of dictionaries
    data = []
    valves_lst = [f'V{idx}' for idx in valves_pos]

    # main experiment loop
    for _ in range(vloop):
        valves_dict = {key: copy.deepcopy({})
                       for key in copy.deepcopy(valves_lst)}
        for vpos in valves_pos:
            arduino_valves.switch_onoff(arduino_valves.valves_pins, [vpos])
            valves_dict[f'V{vpos}'] = arduino_sensors.sensors_loop(lcr_meter,
                                                                   sensors_pos,
                                                                   sloop,
                                                                   vloop,
                                                                   stime)
        # append to list only after a valve cycle is completed
        data.append(valves_dict)

    return data


def arduinos_connect(cfg) -> Dict[str, ArduinoConnection]:
    '''connect to arduinos'''
    boards = {}
    # check if arduino2 is present/configured
    device = "arduino2"
    device_model = str(cfg.get_setting(device, "model"))
    device_board = Board.MEGA if device_model == 'MEGA' else Board.UNO
    device_sensors = str(cfg.get_setting(device, "sensors")).split(';')
    device_valves = str(cfg.get_setting(device, "valves")).split(';')
    empty_sensors = all(len(elem) == 0 for elem in device_sensors)
    empty_valves = all(len(elem) == 0 for elem in device_valves)

    # one arduino only, but not the choosen previously
    if empty_sensors and empty_valves:
        device = 'arduino1'
        device_model = str(cfg.get_setting(device, "model"))
        device_board = Board.MEGA if device_model == 'MEGA' else Board.UNO
        device_sensors = str(cfg.get_setting(
            device, "sensors")).split(';')
        device_valves = str(cfg.get_setting(device, "valves")).split(';')
        sensors = [val.split(',') for val in device_sensors if len(val) > 0]
        valves = [val.split(',') for val in device_valves if len(val) > 0]
        boards['all'] = ArduinoConnection(
            'valves & sensors', device_board, id=1)
        boards['all'].configure_pins(
            valves_pins=valves, sensors_pins=sensors)
        # check for inverted ON/OFF logic in arduino config
        invert_onoff = int(cfg.get_setting(device, "invert_onoff"))
        if invert_onoff == 1:
            boards['all'].invert_onoff()
    else:  # two arduinos
        if empty_sensors:  # find out which arduino is the sensors one
            boards['valves'] = ArduinoConnection(
                'valves', device_board, id=2)
            # get other arduino configuration
            other_device = "arduino1"
            other_device_model = str(cfg.get_setting(other_device, "model"))
            other_device_board = Board.MEGA if other_device_model == 'MEGA' else Board.UNO
            boards['sensors'] = ArduinoConnection(
                'sensors', other_device_board, id=1)
            device_sensors = str(cfg.get_setting(
                other_device, "sensors")).split(';')
            device_valves = str(cfg.get_setting(
                device, "valves")).split(';')
            sensors = [val.split(',')
                       for val in device_sensors if len(val) > 0]
            valves = [val.split(',') for val in device_valves if len(val) > 0]
            boards['valves'].configure_pins(valves_pins=valves)
            boards['sensors'].configure_pins(sensors_pins=sensors)
            invert_onoff = int(cfg.get_setting(device, "invert_onoff"))
            if invert_onoff == 1:
                boards['valves'].invert_onoff()
            invert_onoff = int(cfg.get_setting(other_device, "invert_onoff"))
            if invert_onoff == 1:
                boards['sensors'].invert_onoff()
        elif empty_valves:
            boards['sensors'] = ArduinoConnection(
                'sensors', device_board, id=2)
            # get other arduino configuration
            other_device = 'arduino1'
            other_device_model = str(cfg.get_setting(other_device, "model"))
            other_device_board = Board.MEGA if other_device_model == 'MEGA' else Board.UNO
            boards['valves'] = ArduinoConnection(
                'valves', other_device_board, id=1)
            device_valves = str(cfg.get_setting(
                other_device, "valves")).split(';')
            device_sensors = str(cfg.get_setting(
                device, "sensors")).split(';')
            valves = [val.split(',') for val in device_valves if len(val) > 0]
            sensors = [val.split(',')
                       for val in device_sensors if len(val) > 0]
            boards['sensors'].configure_pins(sensors_pins=sensors)
            boards['valves'].configure_pins(valves_pins=valves)
            invert_onoff = int(cfg.get_setting(device, "invert_onoff"))
            if invert_onoff == 1:
                boards['sensors'].invert_onoff()
            invert_onoff = int(cfg.get_setting(other_device, "invert_onoff"))
            if invert_onoff == 1:
                boards['valves'].invert_onoff()
    return boards
