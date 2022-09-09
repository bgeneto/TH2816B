import os
import sys
from devices import *
import mycfg


def start_experiment():
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

    try:
        run_experiment(lcr, arduinos, **params)
    except KeyboardInterrupt:
        ColorPrint.print_fail("Program interrupted!")
    finally:
        shutdown(lcr, arduinos)


if __name__ == '__main__':
    # find out this script's directory
    SCRIPT_DIR = os.path.dirname(sys.argv[0])
    if len(SCRIPT_DIR) < 1:
        SCRIPT_DIR = '.' + os.sep

    # user defined ini file
    CFGFN = os.path.join(SCRIPT_DIR, "config.ini")

    cfg = mycfg.MyConfig(CFGFN)

    start_experiment()
