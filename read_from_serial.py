#!/usr/bin/python
import serial
import time
import csv
import sys
from pprint import pprint
from vc820 import MultimeterMessage
import json
import getopt

def handle_message(message): 
    packet_time = time.time()
    elapsed_time = round(packet_time - start_time,4)
    if save_csv:
        csv_writer.writerow([elapsed_time,message.value*message.multiplier,message.base_unit,message.hold,message.rel])
    if save_rawtime:
        rawtimefile.write(str(elapsed_time)+" "+message.raw_message.hex()+"\n")
    if current_json:
        f = open(currentjsonfile, "w")
        mdict =   { "reading": message.get_reading(),
                    "base_reading": message.get_base_reading(),
                    "value": message.value,
                    "unit": message.unit,
                    "mode": message.mode,
                    "battery_low": message.batlow,
                    "hold": message.hold,
                    "relative": message.rel,
                    "autorange": message.auto,
                    "raw_message": message.raw_message.hex(),
                    "time": elapsed_time,
                    "diode_test": message.diode }
        json.dump(mdict,f)
        f.close()
    print(message)
    values_list.append(message.raw_message)

def usage():
    print("""Usage:

--csv <file>            Write recorded data as CSV to the specified file
--raw <file>            Write raw recorded data to the specified file
--rawtime <file>        Write the timedelta and the hex representation of the message to the specified file
--currentjson <file>    Write the decoded message in JSON format to the specified file each time a new message is received
--debug <file>          Debug mode. Read values from specified file instead of serial port
--serialport <device>   Specify th serial port to be used. Defaults to /dev/ttyUSB0
--help                  Show this message
    """)

save_csv = False
csvfile = None
save_raw = False
rawfile = None
save_rawtime = False
rawtimefile = None
current_json = False
currentjsonfile = None

portname = "/dev/ttyUSB0"

debug = False
debugfile = None

opts, args = getopt.getopt(sys.argv[1:], "", ["csv=", "raw=", "rawtime=", "currentjson=", "debug=", "serialport=", "help"])
for opt,arg in opts:
    if opt == "--csv":
        save_csv = True
        csvfile = open(arg, "w")
    elif opt == "--raw":
        save_raw = True
        rawfile = open(arg, "wb")
    elif opt == "--rawtime":
        save_rawtime = True
        rawtimefile = open(arg, "w")
    elif opt == "--currentjson":
        current_json = True
        currentjsonfile = arg
    elif opt == "--debug":
        debug = True
        debugfile = arg
    elif opt == "--serialport":
        portname = arg
    elif opt == "--help":
        usage()
        exit(0)

values_list = []
start_time = time.time()

if save_csv:
    csv_writer = csv.writer(csvfile, 'excel-tab')
    csv_writer.writerow(["Time [s]","Value","Unit", "Hold", "Relative"])

if not debug:
    serial_port = serial.Serial(portname, baudrate=2400, parity='N', bytesize=8, timeout=1, rtscts=1, dsrdtr=1)
    serial_port.dtr = True
    serial_port.rts = False
else:
    serial_port = open(debugfile, "rb")


while True:
    test = serial_port.read(1)
    if len(test) != 1:
        if debug:
            exit(0) #EOF
        print("recieved incomplete data, skipping...", file=sys.stderr)
        continue
    if (test[0]&0b11110000) == 0b00010000: #check if first nibble is 0x01
        data = test + serial_port.read(13)
    else:
        print("received incorrect data, skipping...", file=sys.stderr)
        continue
    if save_raw:
        rawfile.write(data)
    message = MultimeterMessage(data)
    handle_message(message)
    if debug:
        time.sleep(0.5)
