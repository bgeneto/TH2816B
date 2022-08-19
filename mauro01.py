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
__version__ = "1.0.3"
__date__ = "20220824"
__status__ = "Development"


class ColorPrint:
    '''print terminal messages in colors '''
    @staticmethod
    def print_fail(message, end='\n'):
        sys.stderr.write('\x1b[1;31m' + message.rstrip() + '\x1b[0m' + end)

    @staticmethod
    def print_pass(message, end='\n'):
        sys.stdout.write('\x1b[1;32m' + message.rstrip() + '\x1b[0m' + end)

    @staticmethod
    def print_warn(message, end='\n'):
        sys.stderr.write('\x1b[1;33m' + message.rstrip() + '\x1b[0m' + end)

    @staticmethod
    def print_info(message, end='\n'):
        sys.stdout.write('\x1b[1;34m' + message.rstrip() + '\x1b[0m' + end)

    @staticmethod
    def print_bold(message, end='\n'):
        sys.stdout.write('\x1b[1;37m' + message.rstrip() + '\x1b[0m' + end)


class Board(Enum):
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
        self.ser = self.connection()

    def connection(self):
        '''instantiate pymata4'''
        ser = pymata4.Pymata4(arduino_instance_id=self.id,
                              arduino_wait=5)
        ColorPrint.print_pass("---------------------------------------------")
        ColorPrint.print_pass(f" Device '{self.name}' connected successfully ")
        ColorPrint.print_pass("---------------------------------------------")

        return ser

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

    def get_pin_number(self, pin):
        '''set the correct pin number according to the board pin name'''
        return self.convert_pin_number(pin)

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

    def configure_pins(self, physical_pins):
        '''set proper pin number and configure required pins as digital output'''
        # convert physical pin name scheme with proper pin number
        for p in range(len(physical_pins)):
            pin_number = self.get_pin_number(physical_pins[p])
            self.pins.insert(p, pin_number)
            # set all pins as digital output
            self.ser.set_pin_mode_digital_output(pin_number)
            self.ser.digital_write(pin_number, OFF)

    def turn(self, onoff, selected_pins, wait=0):
        '''turn on selected pins and turn off all others.
           turn off selected pins and turn on all other pins.
        '''
        status = {0: 'OFF', 1: 'ON'}
        for pin in range(len(self.pins)):
            if pin in selected_pins:
                ColorPrint.print_info("Turning {} {} {}\n".format(
                    status[onoff], self.name, pin))
                self.ser.digital_write(self.pins[pin], onoff)
            else:
                self.ser.digital_write(self.pins[pin], ~onoff)
            time.sleep(0.2)
        time.sleep(wait)
        return


class SerialConnection:
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

    def set_ser_parameters(self, port, baudrate, parity, stopbits, bytesize, timeout):
        self.__init__(self, port, baudrate, parity,
                      stopbits, bytesize, timeout)

    def connect(self, wait=None):
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
        line = str(int(round(time.time() * 1000))) + ',' + line
        self.received_lines.append(line)

    def connection_lost(self, exc):
        if exc:
            traceback.print_exc(exc)
        ColorPrint.print_fail('Serial port closed\n')


def shutdown():
    '''ends serial connections and close active threads'''
    try:
        device['lcr'].protocol.write_line('TRIG:SOUR MAN')
        device['lcr'].close()
        for d in ['valves', 'sensors']:
            # turn off pin energy
            for pin in device[d].pins:
                device[d].ser.digital_write(pin, 0)
                pass
            device[d].ser.shutdown()
    except Exception as e:
        # traceback.print_exc(e)
        pass


if __name__ == '__main__':

    ON = 1
    OFF = 2
    ATTEMPTS = 3
    device = {}
    errmsg = "{} device not found or serial port in use!"

    # LCR TH2816B connection attempts
    dname = 'lcr'
    for _ in range(ATTEMPTS):
        try:
            device[dname] = SerialConnection(dname, "/dev/serial0", timeout=1)
            device[dname].connect()
            # set LCR trigger to manual/software controlled mode
            time.sleep(0.25)
            device[dname].protocol.write_line('TRIG:SOUR INT')
            time.sleep(0.25)
            device[dname].protocol.write_line('APER FAST')
            break
        except:
            ColorPrint.print_warn(errmsg.format(dname))
            time.sleep(1)
    else:
        ColorPrint.print_fail(errmsg.format(dname))
        shutdown()
        sys.exit(1)

    time.sleep(1)

    # arduino connection attempts
    dname = 'sensors'
    for _ in range(ATTEMPTS):
        try:
            device[dname] = ArduinoConnection(dname, Board.UNO, id=2)
            break
        except:
            ColorPrint.print_warn(errmsg.format(dname))
            time.sleep(1)
    else:
        ColorPrint.print_fail(errmsg.format(dname))
        shutdown()
        sys.exit(1)

    time.sleep(1)

    # arduino connection attempts
    dname = 'valves'
    for t in range(ATTEMPTS):
        try:
            device[dname] = ArduinoConnection(dname, Board.MEGA, id=1)
            break
        except:
            ColorPrint.print_warn(errmsg.format(dname))
            time.sleep(1)
    else:
        ColorPrint.print_fail(errmsg.format(dname))
        shutdown()
        sys.exit(1)

    # configure board used pins
    sensors_board_pins = ['A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'D2', 'D3']
    device['sensors'].configure_pins(sensors_board_pins)

    valves_board_pins = ['D2', 'D3', 'D4', 'D5', 'D6']
    device['valves'].configure_pins(valves_board_pins)

    time.sleep(1)

    # loop parameters
    dt = 1/10.
    swtime = 2
    
    # turn on/off valves
    dev = device['valves']
    for valve in range(len(dev.pins[0:1])):
        print("Alternating valves...")
        dev.turn(ON, [valve])

        # number of sensor reading cycles
        NUM_CYCLES = 4

        # turn on/off sensors
        print("Alternating sensors...")
        dev = device['sensors']
        try:
            for __ in range(NUM_CYCLES):
                for sensor in range(len(dev.pins)):
                    fname = f"v{valve}s{sensor}.csv"
                    dev.turn(ON, [sensor])
                    device['lcr'].protocol.received_lines = []
                    for _ in range(int(swtime/dt)):
                        time.sleep(dt)
                    else:
                        with open(fname, 'a', encoding='utf-8') as f:
                            f.write('\n'.join(device['lcr'].protocol.received_lines))
        except KeyboardInterrupt:
            ColorPrint.print_fail("\nProgram interrupted")
        finally:
            shutdown()

    sys.exit(0)
