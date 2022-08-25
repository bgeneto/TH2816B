# TH2816B LCR Meter scripts

Python scripts and web interface for controlling and processing data for the TH2816B LCR meter.


## Install

```bash
git clone https://github.com/bgeneto/TH2816B.git
cd TH2816B
python3 -m pip install -r requirements.txt
```

## Running

```bash
python3 <script-name.py>
```

Please configure your serial device and web server settings (serial port, baud rate, ip...) in `config.ini` file.
This file is created automaticaly (with default values) in the first run.

WARNING: it may be required to run this (`server.py`) script as `sudo` if using lower ports (eg. 80, 443) for the tornado web server. 
So install packages also with `sudo` if this is your case.
