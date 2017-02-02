#!/usr/bin/python

class MultimeterMessage:
    def __init__(self, message_bytes):
        self.raw_message = message_bytes
        self._parse()

    def __str__(self):
        measurement_str = self.number+self.unit+" "+self.mode
        hold = "HOLD" if self.hold else ""
        bat = "BATTERY_LOW" if self.batlow else ""
        warnings_str = hold+" "+bat

        return measurement_str+" "+warnings_str

    def get_reading(self):
        measurement_str = self.number+self.unit+" "+self.mode
        return measurement_str

    def _parse(self):
        raw = self.raw_message
        seg1 = raw[0]
        seg2 = raw[1]
        seg3 = raw[2]
        seg4 = raw[3]
        seg5 = raw[4]
        seg6 = raw[5]
        seg7 = raw[6]
        seg8 = raw[7]
        seg9 = raw[8]
        seg10 = raw[9]
        seg11 = raw[10]
        seg12 = raw[11]
        seg13 = raw[12]
        seg14 = raw[13]

        self.last_segment = seg14

        self.rs232  = True if (seg1&0b0001) else False
        self.auto   = True if (seg1&0b0010) else False
        self.dc     = True if (seg1&0b0100) else False
        self.ac     = True if (seg1&0b1000) else False

        self.diode  = True if (seg10&0b0001) else False
        self.kilo   = True if (seg10&0b0010) else False
        self.nano   = True if (seg10&0b0100) else False
        self.micro  = True if (seg10&0b1000) else False

        self.sound  = True if (seg11&0b0001) else False
        self.mega   = True if (seg11&0b0010) else False
        self.percent= True if (seg11&0b0100) else False
        self.milli  = True if (seg11&0b1000) else False

        self.hold   = True if (seg12&0b0001) else False
        self.rel    = True if (seg12&0b0010) else False
        self.ohm    = True if (seg12&0b0100) else False
        self.farad  = True if (seg12&0b1000) else False

        self.batlow = True if (seg13&0b0001) else False
        self.hertz  = True if (seg13&0b0010) else False
        self.volt   = True if (seg13&0b0100) else False
        self.amp    = True if (seg13&0b1000) else False

        if self.dc:
            self.mode = "DC"
        elif self.ac:
            self.mode = "AC"
        else:
            self.mode = "Unknown"

        self.unit = self._get_unit()
        self.number = self._get_number()
        try:
            self.value = float(self.number)
        except ValueError:
            pass

    def _get_number(self):
        raw = self.raw_message
        minus = "-" if raw[1]&0b1000 else ""
        digit1 = self._get_digit(raw[1], raw[2])
        point1 = "." if raw[3]&0b1000 else ""
        digit2 = self._get_digit(raw[3], raw[4])
        point2 = "." if raw[5]&0b1000 else ""
        digit3 = self._get_digit(raw[5], raw[6])
        point3 = "." if raw[7]&0b1000 else ""
        digit4 = self._get_digit(raw[7], raw[8])

        return minus+digit1+point1+digit2+point2+digit3+point3+digit4

    def _get_digit(self, seg1, seg2):
        a = seg1&0b0001
        b = seg2&0b0001
        c = seg2&0b0100
        d = seg2&0b1000
        e = seg1&0b0100
        f = seg1&0b0010
        g = seg2&0b0010

        if not a and not b and not c and not d and not e and not f and not g:
            return ""
        if not a and b and c and not d and not e and not f and not g:
            return "1"
        if a and b and not c and d and e and not f and g:
            return "2"
        if a and b and c and d and not e and not f and g:
            return "3"
        if not a and b and c and not d and not e and f and g:
            return "4"
        if a and not b and c and d and not e and f and g:
            return "5"
        if a and not b and c and d and e and f and g:
            return "6"
        if a and b and c and not d and not e and not f and not g:
            return "7"
        if a and b and c and d and e and f and g:
            return "8"
        if a and b and c and d and not e and f and g:
            return "9"
        if a and b and c and d and e and f and not g:
            return "0"
        return "X"

    def _get_unit(self):
        modifier = ""
        if self.kilo:
            modifier = "k"
        elif self.nano:
            modifier = "n"
        elif self.micro:
            modifier = "u" #um Probleme mit Zeichenkodierungen zu vermeiden
        elif self.milli:
            modifier = "m"
        elif self.mega:
            modifier = "M"
        
        unit = ""
        if self.percent:
            unit = "%"
        elif self.ohm:
            unit = "Ohm" #same as micro
        elif self.farad:
            unit = "F"
        elif self.hertz:
            unit = "Hz"
        elif self.volt:
            unit = "V"
        elif self.amp:
            unit = "A"
        else:
            raise ValueError("no unit found")

        return modifier+unit
