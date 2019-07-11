#!/usr/bin/python3

import argparse
import logging

from vc820 import MultimeterMessage


def rawtime_to_json():
    import json

    dictlist = []

    lasttime = 0

    for line in args.infile:
        timestr, msgstr = line.split(" ")
        message = MultimeterMessage(bytes.fromhex(msgstr.strip()))
        time = float(timestr)
        deltatime = time - lasttime
        lasttime = time
        mdict = {"reading": message.get_reading(),
                 "base_reading": message.get_base_reading(),
                 "mode": message.mode,
                 "battery_low": message.batlow,
                 "hold": message.hold,
                 "relative": message.rel,
                 "autorange": message.auto,
                 "raw_message": message.raw_message.hex(),
                 "time": time,
                 "deltatime": deltatime,
                 "value": message.value,
                 "unit": message.unit,
                 "diode_test": message.diode}
        dictlist.append(mdict)

    json.dumps(dictlist, indent=4, fp=args.outfile)


def rawtime_to_csv():
    import csv

    csvw = csv.writer(args.outfile, 'excel-tab')
    csvw.writerow(["#Time [s]", "Value", "Unit", "Modus", "Hold", "Relative"])

    for line in args.infile:
        timestr, msgstr = line.split(" ")
        msg = MultimeterMessage(bytes.fromhex(msgstr.strip()))
        csvw.writerow([timestr, msg.value * msg.multiplier, msg.base_unit, msg.mode, msg.hold, msg.rel])


def rawtime_to_raw():
    for line in args.infile:
        timestr, msgstr = line.split(" ")
        args.outfile.write(bytes.fromhex(msgstr.strip()))


def raw_to_json():
    import json

    values_list = []

    while True:
        test = args.infile.read(1)
        if len(test) != 1:
            break  # EOF reached
        if (test[0] & 0b11110000) == 0b00010000:  # check if first nibble is 0x01
            data = test + args.infile.read(13)
        else:
            logging.info("received incorrect byte, skipping...")
            continue
        message = MultimeterMessage(data)
        values_list.append(message)

    human_readable_list = []
    for message in values_list:
        mdict = {"reading": message.get_reading(),
                 "base_reading": message.get_base_reading(),
                 "mode": message.mode,
                 "battery_low": message.batlow,
                 "hold": message.hold,
                 "relative": message.rel,
                 "autorange": message.auto,
                 "raw_message": message.raw_message.hex(),
                 "value": message.value,
                 "unit": message.unit,
                 "diode_test": message.diode}
        human_readable_list.append(mdict)

    json.dump(human_readable_list, indent=4, fp=args.outfile)

converters = {("rawtime", "json"): rawtime_to_json,
              ("rawtime", "csv"): rawtime_to_csv,
              ("rawtime", "raw"): rawtime_to_raw,
              ("raw", "json"): raw_to_json}

informats = set([x[0] for x in converters.keys()])
outformats = set([x[1] for x in converters.keys()])

parser = argparse.ArgumentParser(description="Convert data files between formats")
parser.add_argument("--infile", type=argparse.FileType("rb"), required=True)
parser.add_argument("--outfile", type=argparse.FileType("w"), required=True)
parser.add_argument("--informat", choices=informats, required=True)
parser.add_argument("--outformat", choices=outformats, required=True)
args = parser.parse_args()

try:
    combo = (args.informat, args.outformat)
    converter = converters[("raw", "json")]
    converter()
except KeyError:
    logging.error("No such converter")
    exit(1)
