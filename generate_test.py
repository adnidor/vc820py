#!/usr/bin/python
from random import randrange
import vc820
import sys

def _generate_bytes():  
    bts = bytes()
    for segment in range (1,15):
        random = randrange(0,16)
        number = (segment<<4)|random
        bts += bytes([number])
    return(bts)

def get_random_list(count):
    lst = []
    for i in range(count):
        while True:
            bts = _generate_bytes()
            try:
                mm = vc820.MultimeterMessage(bts)
                mm.value
            except (ValueError, AttributeError) as e:
                continue
            print("found valid message")
            lst.append(bts)
            break
    return lst

filename = sys.argv[1]
testvaluesfile = open(filename, "wb")

for item in get_random_list(20):
    testvaluesfile.write(item)
