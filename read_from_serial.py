#!/usr/bin/python
import serial
import time
import csv
import sys
from pprint import pprint
from vc820 import MultimeterMessage
import json
import getopt

#huge fucking mess
#TODO: split into smaller functions
def handle_message(message): 
    if base:
        print(message.get_base_reading())
    else:
        print(str(message))
    packet_time = time.time()
    elapsed_time = round(packet_time - start_time,4)
    global under_threshold
    global over_threshold
    if save_csv:
        csv_writer.writerow([elapsed_time,message.value*message.multiplier,message.base_unit,message.mode,message.hold,message.rel])
        csvfile.flush()
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
    if threshold is not None:
        if under_threshold is None or over_threshold is None:
            under_threshold = (threshold > message.base_value)
            over_threshold = (threshold < message.base_value)
        else:
            if message.base_value == threshold:
                pass
            elif (threshold < message.base_value) != over_threshold:
                print("WARNING, THRESHOLD CROSSED")
                if s_o_threshold:
                    exit(0)
                under_threshold = (threshold > message.base_value)
                over_threshold = (threshold < message.base_value)
            elif (threshold > message.base_value) != under_threshold:
                print("WARNING, THRESHOLD CROSSED")
                if s_o_threshold:
                    exit(0)
                under_threshold = (threshold > message.base_value)
                over_threshold = (threshold < message.base_value)
    values_list.append(message.raw_message)

def usage():
    print("""Usage:

--csv <file>            Write recorded data as CSV to the specified file
--raw <file>            Write raw recorded data to the specified file
--rawtime <file>        Write the timedelta and the hex representation of the message to the specified file
--currentjson <file>    Write the decoded message in JSON format to the specified file each time a new message is received
--debug <file>          Debug mode. Read values from specified file instead of serial port
--debugwait <sec>       Set the waittime between values in debug mode
--serialport <device>   Specify th serial port to be used. Defaults to /dev/ttyUSB0
--threshold <number>    Warn if base reading crosses this value
--stop-on-threshold     Stop if threshold is crossed
--base                  Print values in the base unit
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
debugwait = 0.5

threshold = None
s_o_threshold = False

base = False

#start parsing arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["csv=", "raw=", "rawtime=", "currentjson=", "debug=", "serialport=", "help", "debugwait=", "threshold=", "base", "stop-on-threshold"])
except getopt.GetoptError as e:
    print(e)
    usage()
    exit(1)

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
    elif opt == "--debugwait":
        debugwait = float(arg)
    elif opt == "--help":
        usage()
        exit(0)
    elif opt == "--threshold":
        threshold = float(arg)
    elif opt == "--base":
        base = True
    elif opt == "--stop-on-threshold":
        s_o_threshold = True
#stop parsing arguments

values_list = []
start_time = time.time()

if save_csv:
    csv_writer = csv.writer(csvfile, 'excel-tab')
    csv_writer.writerow(["#Time [s]", "Value", "Unit", "Modus", "Hold", "Relative"])

if not debug:
    serial_port = serial.Serial(portname, baudrate=2400, parity='N', bytesize=8, timeout=1, rtscts=1, dsrdtr=1)
    #dtr and rts settings required for adapter
    serial_port.dtr = True
    serial_port.rts = False
else:
    serial_port = open(debugfile, "rb")

under_threshold = None
over_threshold = None

while True:
    test = serial_port.read(1)
    if len(test) != 1:
        if debug:
            exit(0) #EOF
        print("recieved incomplete data, skipping...", file=sys.stderr)
        continue
    if (test[0]&0b11110000) == 0b00010000: #check if first nibble is 0x1, if it isn't this is not the start of a message
        data = test + serial_port.read(13)
    else:
        if save_raw:
            rawfile.write(test)
        print("received incorrect data (%s), skipping..."%test.hex(), file=sys.stderr)
        continue
    if save_raw:
        rawfile.write(data)
    if len(data) != 14:
        print("received incomplete message (%s), skipping..."%data.hex(), file=sys.stderr)
        continue
    try:
        message = MultimeterMessage(data)
    except ValueError as e:
        print("Error decoding: %s on message %s"%(str(e),data.hex()))
        continue
    handle_message(message)
    if debug:
        time.sleep(debugwait)
