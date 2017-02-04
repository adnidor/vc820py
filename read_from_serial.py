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
    print(message)
    values_list.append(message.raw_message)

save_csv = False
csvfile = None
save_raw = False
rawfile = None
save_rawtime = False
rawtimefile = None

opts, args = getopt.getopt(sys.argv[1:], "", ["csv=", "raw=", "rawtime="])
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

values_list = []
start_time = time.time()

if save_csv:
    csv_writer = csv.writer(csvfile, 'excel-tab')
    csv_writer.writerow(["Time [s]","Value","Unit", "Hold", "Relative"])

#serial_port = serial.Serial("/dev/ttyUSB0", baudrate=2400, parity='N', bytesize=8, timeout=1, rtscts=1, dsrdtr=1)
#serial_port.dtr = True
#serial_port.rts = False
serial_port = open("real_logfile", "rb")


while True:
    test = serial_port.read(1)
    if len(test) != 1:
        exit(0) #XXX comment out before connecting to serial
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
