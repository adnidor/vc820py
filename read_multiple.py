#!/usr/bin/python
import serial
import time
from time import sleep
import csv
import sys
from pprint import pprint
from vc820 import MultimeterMessage
import json
import getopt
import threading

start_time = time.time()

cur_msg = {}

stop_flag = False

def print_error(text, tag=None):
    thread_name = str(threading.current_thread().getName())
    if tag is None:
        print('\r[%s] %s'%(thread_name,text),file=sys.stderr)
    else:
        print("\r[%s] [%s] %s"%(thread_name,str(tag),str(text)),file=sys.stderr)

class ReadThread(threading.Thread):
    def __init__(self,input):
        threading.Thread.__init__(self)
        self.input = input
        self.setName(str(input))
        if not debug:
            self.serial_port = serial.Serial(input, baudrate=2400, parity='N', bytesize=8, timeout=1, rtscts=1, dsrdtr=1)
            self.serial_port.dtr = True
            self.serial_port.rts = False
        else:
            self.serial_port = open(input, "rb")

    def _delete_value(self):
        try:
            del cur_msg[self.getName()]
        except KeyError:
            pass

    def run(self):
        while True:
            if stop_flag:
                return
            if debug:
                time.sleep(debugwait)
            test = self.serial_port.read(1)
            if len(test) != 1:
                if debug:
                    self._delete_value()
                    print_error("EOF reached (Debug mode)")
                    exit(0) #EOF
                print_error("recieved incomplete data, skipping...")
                self._delete_value()
                continue
            if (test[0]&0b11110000) == 0b00010000: #check if first nibble is 0x1
                data = test + self.serial_port.read(13)
            else:
                print_error("received incorrect data (%s), skipping..."%test.hex())
                self._delete_value()
                continue
            if len(data) != 14:
                print_error("received incomplete message (%s), skipping..."%data.hex())
                self._delete_value()
                continue
            try:
                message = MultimeterMessage(data)
            except ValueError as e:
                print_error("Error decoding: %s on message %s"%(str(e),data.hex()))
                self._delete_value()
                continue
            cur_msg[self.getName()] = message

def handle_message():
    messages = cur_msg
    elapsed_time = round(time.time() - start_time, 4)
    printmsg = "%.4fs | "%elapsed_time
    for key,value in sorted(messages.items()):
        printmsg += str(value).strip()+" | "
    if csvfile is not None:
        csvwriter.writerow({"time": elapsed_time, **messages})
    if output:
        print(printmsg.strip())
        #sys.stdout.write("\r"+printmsg.strip()+"                   \b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b")
        #sys.stdout.flush()

sources = []
readthreads = []

debug = False
debugwait = 0.5

mainwait = 0.5

csvfile = None

output = True

valid_arguments = [ "source=", "debug", "help", "debugwait=", "rate=", "csv=", "no-stdout" ]

try:
    opts, args = getopt.getopt(sys.argv[1:], "", valid_arguments)
except getopt.GetoptError as e:
    print(e)
    exit(1)

for opt,arg in opts:
    if opt == "--debug":
        debug = True
    elif opt == "--source":
        sources.append(arg)
    elif opt == "--help":
        pass
    elif opt == "--debugwait":
        debugwait = float(arg)
    elif opt == "--rate":
        mainwait = float(arg)
    elif opt == "--csv":
        csvfile = open(arg, "w")
    elif opt == "--no-stdout":
        output = False

if csvfile is not None:
    csvwriter = csv.DictWriter(csvfile, ["time"]+sources, dialect="excel-tab")
    csvwriter.writeheader()

for source in sources:
    readthread = ReadThread(source)
    readthreads.append(readthread)
    readthread.start()
    print_error("Thread %s started"%source)

try:
    i = 0
    sleep(1)
    while True:
        sleep(mainwait)
        if len(cur_msg) == 0:
            print_error("No values read, exiting...")
            break
        handle_message()
finally:
    stop_flag = True
