#!/usr/bin/python
import serial
import time
import csv
from sys import stderr,stdout
import sys
from pprint import pprint
from vc820 import MultimeterMessage

def handle_message(message): 
    packet_time = time.time()
    elapsed_time = round(packet_time - start_time,4)
    battery_low = "BATTERY" if message.batlow else ""
    csv_writer.writerow([elapsed_time,message.value*message.multiplier,message.base_unit,battery_low])
    values_list.append(message.raw_message)

values_list = []
start_time = time.time()
csv_writer = csv.writer(stdout, 'excel-tab')
csv_writer.writerow(["Time [s]","Value","Unit", "Warnings"])

logfile = None

if len(sys.argv) == 2:
    logfile = open(sys.argv[1], "wb")

serial_port = serial.Serial("/dev/ttyUSB0", baudrate=2400, parity='N', bytesize=8, timeout=1, rtscts=1, dsrdtr=1)
serial_port.dtr = True
serial_port.rts = False
#serial_port = open("testvalues", "rb")


while True:
    test = serial_port.read(1)
    if len(test) != 1:
        #exit(0) #XXX comment out before connecting to serial
        print("recieved incomplete data, skipping...", file=stderr)
        continue
    if (test[0]&0b11110000) == 0b00010000: #check if first nibble is 0x01
        data = test + serial_port.read(13)
    else:
        print("received incorrect data, skipping...", file=stderr)
        continue
    if logfile is not None:
        logfile.write(data)
    message = MultimeterMessage(data)
    handle_message(message)
