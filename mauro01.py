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

import os
import sys
import time
import traceback
from enum import Enum
from io import StringIO

import pandas as pd
import serial
from pymata4 import pymata4
from serial.threaded import LineReader, ReaderThread

__author__ = "Bernhard Enders"
__maintainer__ = "Bernhard Enders"
__email__ = "b g e n e t o @ g m a i l d o t c o m"
__copyright__ = "Copyright 2022, Bernhard Enders"
__license__ = "GPL"
__version__ = "1.1.0"
__date__ = "20220825"
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
        ColorPrint.print_info(f" Searching '{name}' device...                ")
        ColorPrint.print_info("---------------------------------------------")
        self.name = name
        self.model = model
        self.id = id
        self.pins = []
        self.connection_attempt()

    def connect(self):
        '''instantiate pymata4'''
        wait = 3  # seconds
        ser = pymata4.Pymata4(arduino_instance_id=self.id,
                              arduino_wait=wait)
        ColorPrint.print_pass("---------------------------------------------")
        ColorPrint.print_pass(f" Device '{self.name}' connected successfully ")
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

    def analog_to_digital(self, num):
        '''When configuring an analog input pin as a digital input/output,
        you must use the pin's digital pin number equivalent. For example,
        on an Arduino Uno, if you wish to use pin A0 as a digital pin,
        the digital pin number equivalent is 14. In general,
        to find the digital equivalent of pin A0 for your specific
        Arduino board type, the algorithm is:

            digital_pin_number = analog_pin_number + number of digital pins
        '''
        return int(num + self.model.value)

    def convert_pin_number(self, pin):
        '''convert analog pin to digital if required and
           use the correct pin numbering instead of board numbering/naming'''
        if isinstance(pin, int):
            return pin
        elif isinstance(pin, str):
            if pin[0].lower() == 'A'.lower():
                return self.analog_to_digital(int(pin[1:]))
            elif pin[0].lower() == 'D'.lower():
                return int(pin[1:])
            else:  # supposing string of only numbers
                return int(pin)
        else:  # unexpected type
            raise TypeError

    def configure_pins(self, physical_pins):
        '''set proper pin number and configure required pins as digital output'''
        # convert physical pin name scheme with proper pin number
        for i, pin in enumerate(physical_pins):
            pin_number = self.convert_pin_number(pin)
            self.pins.insert(i, pin_number)
            # set all pins as digital output
            self.ser.set_pin_mode_digital_output(pin_number)
            time.sleep(0.1)  # lets be cautious and wait a little bit
            self.ser.digital_write(pin_number, OFF)
            time.sleep(0.1)  # lets be cautious and wait a little bit

    def switch_onoff(self, pin_pos, wait=0):
        '''turn on selected pins at pin_pos and turn off all others'''
        for i, pin in enumerate(self.pins):
            if i in pin_pos:
                ColorPrint.print_info(f"Turning ON {self.name} {pin}\n")
                self.ser.digital_write(pin, ON)
            else:
                self.ser.digital_write(pin, OFF)
            time.sleep(0.1)  # wait before turning off/on another GPIO pin
        time.sleep(wait)
        return

    def loop(self, sensors, count):
        '''loop through all the selected sensors'''

        # LCR meter sampling rate
        reading_rate = 1/10.0

        # LCR meter sampling duration (in seconds) per sensor
        reading_time = 3

        # LCR meter primary and secondary parameters
        cols = ['primary', 'secondary']

        # received data lists
        rx_lst = lcr_meter.protocol.received_lines
        str_lst = ['']*len(sensors)

        try:
            while count > 0:
                count = count - 1
                for sensor in sensors:
                    # first thing is to turn on the sensor and wait for it to settle
                    self.switch_onoff([sensor])
                    time.sleep(1)
                    # now we empty the input buffer list
                    rx_lst = []
                    # wait 'reading_time' seconds
                    for __ in range(int(reading_time/reading_rate)):
                        time.sleep(reading_rate)
                    rx_str = '\n'.join(rx_lst) + '\n'
                    str_lst[sensor] += rx_str
        except KeyboardInterrupt:
            ColorPrint.print_fail("\nProgram interrupted")
        finally:
            shutdown()

        # format the data into a list of dataframes
        lst_df = []
        for pos, data in enumerate(str_lst):
            lst_df.insert(pos, pd.read_csv(
                StringIO(data), sep=",", header=None, names=cols))

        return lst_df


class SerialConnection:
    '''threaded serial port connection'''

    def __init__(self, name, port,
                 baudrate=9600,
                 parity=serial.PARITY_NONE,
                 stopbits=serial.STOPBITS_ONE,
                 bytesize=serial.EIGHTBITS,
                 timeout=1):

        ColorPrint.print_info("---------------------------------------------")
        ColorPrint.print_info(f" Searching '{name}' device...                ")
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
        ColorPrint.print_pass(f" Device '{self.name}' connected successfully ")
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
    '''ends serial connections and close active threads'''
    try:
        # return lcr meter to manual trigger mode (stops auto measurement)
        lcr_meter.protocol.write_line('TRIG:SOUR MAN')
        time.sleep(0.1)
        lcr_meter.close()
        for device in [valves_arduino, sensors_arduino]:
            # turn off pin energy
            for pin in device.pins:
                device.ser.digital_write(pin, OFF)
                time.sleep(0.1)
            device.ser.shutdown()
    except Exception as exc:
        traceback.print_exc(exc)
    return


def create_output_dir():
    # base output directory
    base_dir = 'experiments'

    # date and time as subdirectory
    timestr = time.strftime("%Y-%m-%d %H%M%S")

    # create output directory if not exists
    output_dir = os.path.abspath(os.path.join(base_dir, timestr))
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except Exception as _:
            ColorPrint.print_fail(f"Unable to create output directory!")
            shutdown()
            sys.exit(1)

    return output_dir


def experiment():
    '''make requried connections and start the experiment'''

    # store retrieved data in a list of dataframes
    data = []

    # configure board pins
    sensors_board_pins = ['A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'D2', 'D3']
    sensors_arduino.configure_pins(sensors_board_pins)

    valves_board_pins = ['D2', 'D3', 'D4', 'D5', 'D6']
    valves_arduino.configure_pins(valves_board_pins)

    # wait before starting a measurement
    time.sleep(1)

    # choose sensors to use
    sensors = range(0, 7)

    # experiment cycle
    cycles = 4  # number of sensor reading cycles

    valve = 0
    valves_arduino.switch_onoff([valve])
    data[valve] = sensors_arduino.loop(sensors, cycles)

    valve = 1
    valves_arduino.switch_onoff([valve])
    data[valve] = sensors_arduino.loop(sensors, cycles)

    # create output directory if not exists
    output_dir = create_output_dir()

    # save data to several csv files
    for valve in data:
        for param in ['primary', 'secondary']:
            # write two files with all sensors data
            sensors_df = pd.concat(
                [df_sensors[param] for df_sensors in data[valve]], ignore_index=True, axis=1)
            fname = os.path.join(
                output_dir, f'v{valve}_{param}_all_sensors.csv')
            sensors_df.to_csv(fname, index=False)
        for sensor in data[valve]:
            # write one
            fname = os.path.join(output_dir, f'v{valve}_s{sensor}.csv')
            data[valve][sensor].to_csv(fname, index=False)

    return


if __name__ == '__main__':

    # global constants
    ON = 1
    OFF = 2

    # LCR TH2816B connection
    lcr_meter = SerialConnection('lcr', "/dev/serial0", timeout=1)

    # arduino connection
    valves_arduino = ArduinoConnection('valves', Board.MEGA, id=1)
    sensors_arduino = ArduinoConnection('sensors', Board.UNO, id=2)

    # run the experiment
    experiment()

    sys.exit(0)
