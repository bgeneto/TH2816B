from logging import warning
import os
import sys


class ColorPrint:
    '''Print terminal messages in colors.
       Alternatively, print html color code to file
    '''

    def __init__(self, filename=None):
        # filename to log to
        self.filename = filename
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
    def __write_term(self, flavor, prefix, message, end):
        sys.stderr.write(self.term_color[flavor] + prefix +
                         str(message) + self.term_postfix + end)

    # write to file
    def __write_html(self, flavor, prefix, message):
        if not self.filename:
            return
        html = self.html[flavor] + prefix + \
            str(message) + self.html_end
        with open(self.filename, 'a') as f:
            f.write(html)

    # print methods
    def fail(self, message, end='\n'):
        self.__write_term('fail', 'ERROR: ', message, end)
        self.__write_html('fail', '', message)
    error = fail

    def success(self, message, end='\n'):
        self.__write_term('pass', '', message, end)
        self.__write_html('pass', '', message)
    ok = success

    def warn(self, message, end='\n'):
        self.__write_term('warn', 'WARNING: ', message, end)
        self.__write_html('warn', '', message)
    warning = warn

    def info(self, message, end='\n'):
        self.__write_term('info', '', message, end)
        self.__write_html('info', '', message)

    def bold(self, message, end='\n'):
        self.__write_term('bold', '', message, end)
        self.__write_html('bold', '', message)

    def norm(self, message, end='\n'):
        self.__write_term('norm', '', message, end)
        self.__write_html('norm', '', message)
    normal = norm

    def light(self, message, end='\n'):
        self.__write_term('light', '', message, end)
        self.__write_html('light', '', message)
    fade = light
