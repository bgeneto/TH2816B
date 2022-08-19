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

import sys
import threading
import time
import traceback
from enum import Enum

import serial
from pymata4 import pymata4
from serial.threaded import LineReader, ReaderThread

__author__ = "Bernhard Enders"
__maintainer__ = "Bernhard Enders"
__email__ = "b g e n e t o @ g m a i l d o t c o m"
__copyright__ = "Copyright 2022, Bernhard Enders"
__license__ = "GPL"
__version__ = "1.0.2"
__date__ = "20220818"
__status__ = "Development"


class ColorPrint:
    '''print terminal messages in colors '''
    @staticmethod
    def print_fail(message, end='\n'):
        sys.stderr.write('\x1b[1;31m' + str(message) + '\x1b[0m' + end)

    @staticmethod
    def print_pass(message, end='\n'):
        sys.stdout.write('\x1b[1;32m' + str(message) + '\x1b[0m' + end)

    @staticmethod
    def print_warn(message, end='\n'):
        sys.stderr.write('\x1b[1;33m' + str(message) + '\x1b[0m' + end)

    @staticmethod
    def print_info(message, end='\n'):
        sys.stdout.write('\x1b[1;34m' + str(message) + '\x1b[0m' + end)

    @staticmethod
    def print_bold(message, end='\n'):
        sys.stdout.write('\x1b[1;37m' + str(message) + '\x1b[0m' + end)


class Board(Enum):
    UNO = 14
    MEGA = 54


class ArduinoConnection:
    '''Remember to set/change the ARDUINO_INSTANCE_ID in the
       FirmataExpress before uploading the Arduino firmware
       Instructions to set the instance-id here:
       https://mryslab.github.io/pymata-express/firmata_express/#setting-the-firmataexpress-instance-id
    '''

    def __init__(self, name, model, id=1):
        ColorPrint.print_info(f"Searching '{name}' device...")
        self.name = name
        self.model = model
        self.id = id
        self.sensors = []
        self.conn = self.connection()

    def connection(self):
        '''instantiate pymata4'''
        conn = pymata4.Pymata4(arduino_instance_id=self.id)
        ColorPrint.print_pass(f"Device '{self.name}' connected successfully")

        return conn

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

    def set_sensor_pin(self, sensor_pos, pin):
        '''set pin number at sensor position'''
        pin = self.convert_pin_number(pin)
        # set the right pin number
        self.sensors.insert(sensor_pos, {'pin': pin})

    def convert_pin_number(self, pin):
        '''convert/normalize pin numbering if required'''
        if isinstance(pin, int):
            return pin
        elif isinstance(pin, str):
            if pin[0].lower() == 'a':
                return self.analog_to_digital(int(pin[1:]))
            elif pin[0].lower() == 'd':
                return int(pin[1:])
            else:  # supposing string of only numbers
                return int(pin)
        else:  # unexpected type
            raise TypeError


def blink(device, pins):
    """
    This function will to toggle a digital pin.
    :param my_board: an Pymata4 instance
    :param pin: pin to be controlled
    """

    # set the pin mode as digital output
    for pin in pins:
        device.set_pin_mode_digital_output(pin)

    # toggle the pin 4 times and exit
    for x in range(4):
        for pin in pins:
            device.digital_write(pin, 1)
        time.sleep(1)
        for pin in pins:
            device.digital_write(pin, 0)
        time.sleep(1)


class SerialConnection:
    def __init__(self, name, port,
                 baudrate=9600,
                 parity=serial.PARITY_NONE,
                 stopbits=serial.STOPBITS_ONE,
                 bytesize=serial.EIGHTBITS,
                 timeout=1):
        ColorPrint.print_info(f"Searching '{name}' device...")
        # generic device parameters
        self.name = name
        self.conn = None
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
        self.conn_parameters = {'url': self.url,
                                'baudrate': self.baudrate,
                                'stopbits': self.stopbits,
                                'bytesize': self.bytesize,
                                'timeout': self.timeout
                                }

    def set_conn_parameters(self, port, baudrate, parity, stopbits, bytesize, timeout):
        self.__init__(self, port, baudrate, parity,
                      stopbits, bytesize, timeout)

    def connect(self, wait=None):
        # make the serial connection
        self.conn = serial.serial_for_url(
            **self.conn_parameters, do_not_open=False)

        # start the serial monitoring thread
        self.thread = ReaderThread(self.conn, SerialReaderProtocolLine)
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

        ColorPrint.print_pass(f"Device '{self.name}' connected successfully")

    def close(self):
        '''Stop and close serial monintoring thread'''
        self.thread.close()
        self.conn.close()


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
        self.received_lines.append(line)

    def connection_lost(self, exc):
        if exc:
            traceback.print_exc(exc)
        ColorPrint.print_fail('Serial port closed\n')


if __name__ == '__main__':

    # LCR TH2816B connection...
    try:
        lcr_meter = SerialConnection('LCR', "/dev/serial0", timeout=1)
    except:
        ColorPrint.print_fail('LCR meter not found or serial port in use')
        sys.exit(1)

    # arduino connections...
    try:
        sensors_board = ArduinoConnection('sensors', Board.UNO, id=2)
    except:
        ColorPrint.print_fail('Sensors board not found or in use')
        pass #sys.exit(1)
    try:
        valves_board = ArduinoConnection('valves', Board.MEGA, id=1)
    except:
        ColorPrint.print_fail('Valves board not found or in use')
        pass  # sys.exit(1)

    valves_board.set_sensor_pin(1, 'D2')
    valves_board.set_sensor_pin(2, 'D3')
    print(valves_board.sensors)
    valves_board.conn.digital_write(2, 1)
    #sensors_board.set_sensor_pin(0, 'd50')
    #sensors_board.set_sensor_pin(1, 'D40')
    pins = [s['pin'] for s in valves_board.sensors]

    #device.set_pin_mode_digital_output(pin)
    blink(valves_board.conn, pins)
    lcr_meter.connect()

    num_threads = threading.active_count()
    ColorPrint.print_info(f"Running {num_threads} threads...")

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        ColorPrint.print_fail("\nProgram interrupted")
        print(lcr_meter.protocol.received_lines)
    finally:
        try:
            lcr_meter.close()
            sensors_board.conn.shutdown()
            valves_board.conn.shutdown()
        except:
            pass

    sys.exit(0)
