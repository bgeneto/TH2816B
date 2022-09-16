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
Write message to standard output (stdout) or standard error (stderr).

Message is outputted in color according to the message flavor/method requested.
Can also write to a file in html format.

Classes:

    ColorPrint

Functions:

    fail(message, end)
    error(message, end)
    warn(message, end)
    info(message, end)
    success(message, end)
    bold(message, end)
    norm(message, end)
    light(message, end)

Misc variables:

    __version__
    __author__
"""

import os
import sys

__author__ = "bgeneto"
__copyright__ = "Copyright 2022, bgeneto"
__credits__ = ["bgeneto"]
__license__ = "GPL"
__maintainer__ = "Bernhard Enders"
__email__ = "b g e n e t o @ d u c k . c o m"
__version__ = "1.0.1"
__modified__ = "20220915"


class ColorPrint:
    '''Print terminal messages in colors.
       Alternatively, print html with colors to file
    '''

    def __init__(self, filename=None):
        # filename to log to
        self.filename = filename
        # remove file at start
        if self.filename is not None:
            if os.path.isfile(self.filename):
                os.remove(self.filename)
        # terminal colors to use
        self.term_postfix = '\x1b[0m'
        self.term_color = {'fail': '\x1b[1;31m',
                           'pass': '\x1b[1;32m',
                           'warn': '\x1b[1;33m',
                           'info': '\x1b[1;34m',
                           'bold': '\x1b[1;37m',
                           'norm': '\x1b[0;37m',
                           'light': '\x1b[1;90m',
                           }
        # html colors to use
        self.html_end = '</p>'
        self.html = {'fail': '<p style="color:red">',
                     'pass': '<p style="color:green">',
                     'warn': '<p style="color:orange">',
                     'info': '<p style="color:blue">',
                     'bold': '<p style="font-weight: bold">',
                     'norm': '<p style="font-weight: normal">',
                     'light': '<p style="font-weight: lighter">',
                     }

    # write to terminal
    def __write(self, flavor, message,
                prefix='',
                file=sys.stdout,
                end='\n'):

        # write to terminal using the built-in print function
        print(self.term_color[flavor] +
              prefix +
              str(message) +
              self.term_postfix,
              file=file,
              end=end)

        # write to file
        if self.filename is not None:
            html = self.html[flavor] + prefix + \
                str(message) + self.html_end + end
            with open(self.filename, 'a', encoding='UTF-8') as f:
                f.write(html)

    # available print methods
    def fail(self, message, end='\n'):
        self.__write('fail', message, prefix='ERROR: ',
                     file=sys.stderr, end=end)
    # alias
    error = fail

    def success(self, message, end='\n'):
        self.__write('pass', message, end=end)
    # alias
    ok = success
    good = success

    def warn(self, message, end='\n'):
        self.__write('warn', message, end=end)
    # alias
    warning = warn

    def info(self, message, end='\n'):
        self.__write('info', message, end=end)
    # alias
    msg = info

    def bold(self, message, end='\n'):
        self.__write('bold', message, end=end)

    def norm(self, message, end='\n'):
        self.__write('norm', message, end=end)
    # alias
    normal = norm

    def light(self, message, end='\n'):
        self.__write('light', message, end=end)
    # alias
    fade = light
