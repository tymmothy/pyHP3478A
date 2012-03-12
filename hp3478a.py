"""
HP3478A.py

(c) 2012 Tymm Twillman

This module provides an API for interfacing with HP3478A bench meters
over GPIB, via the Python gpib-devices package.

Copyright (c) 2011-2012, Timothy Twillman
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice,
       this list of conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY TIMOTHY TWILLMAN ''AS IS'' AND ANY EXPRESS
OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN
NO EVENT SHALL TIMOTHY TWILLMAN OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are
those of the authors and should not be interpreted as representing official
policies, either expressed or implied, of Timothy Twillman.
"""

from gpib import generic488
import struct
import math   # math.log used in setting range.


def bit_is_set(value, bitnum):
    """Test whether the given bit number is set in value."""
    if value & (1 << bitnum):
        return True
    else:
        return False


class HP3478A(generic488.Device488):

    """HP 3478A Bench Meter interface class.

    This class allows control of HP3478A bench meters over GPIB.

    Example:

        # Multimeter is set to device #23
        meter = HP3478A('dev23')

        # Set function to DC voltage
        meter.function = 'VDC'

        # Set range to 3V
        meter.range = 3.0

        # Print 100 readings
        for i in xrange(0, 100):
            print meter.reading
    """

    # Volts DC, volts AC, 2-wire resistance, 4-wire resistance, current DC,
    # current AC, extended resistance
    functions = [ 'VDC', 'VAC', 'RTW', 'RFW', 'IDC', 'IAC', 'REX' ]

    # Internal, external, single, hold, fast
    triggers = [ 'I', 'E', 'S', 'H', 'F' ]

    def __init__(self,name=None,pad=None,sad=None,board=None):
        """Create an HP3478A object."""
        super(HP3478A, self).__init__(name=name, pad=pad, sad=sad, board=board)

        # Default text mode does not turn off display.
        self._textmode = 2
        # Default SRQ Mask
        self._srq_mask = 0x00
        self.write('M00')

    @property
    def _bstatus(self):
        """Get binary status bytes from the meter.

        Return value is a 5-tuple of status bytes:
            1: Function/range/resolution settings
            2: Status bits
            3: Serial poll mask (SRQ)
            4: Error bits
            5: DAC value
        """
        self.wrt('B')
        temp = self.read()
        bstat = struct.unpack('>BBBBB', temp)
        return bstat

    @property
    def reading(self):
        """Get a reading from the meter.

        Return:
            Float value; current meter reading.
        """
        return float(self.read())

    @property
    def status(self):
        """General meter status.  Read-only dict value.

        The dict has the following keys:
            ext_trigger    (bool) True if external trigger is enabled.
            cal_ram        (bool) True if calibration RAM is enabled.
            front          (bool) True if front/rear switch in front position.
            50hz           (bool) True if meter is set up for 50hz operation.
            autozero       (bool) True if auto-zero is enabled.
            autorange      (bool) True if auto-range is enabled
            int_trigger    (bool) True if internal trigger is enabled.
        """
        bstat = self._bstatus
        return {
            'ext_trigger' : bit_is_set(bstat[1], 6),
            'cal_ram' : bit_is_set(bstat[1], 5),
            'front' : bit_is_set(bstat[1], 4),
            '50hz' : bit_is_set(bstat[1], 3),
            'autozero' : bit_is_set(bstat[1], 2),
            'autorange' : bit_is_set(bstat[1], 1),
            'int_trigger' : bit_is_set(bstat[1], 0),
        }

    @property
    def srq(self):
        """Meter SRQ status.  Read-only dict value.

        The dict has the following keys:
            pon_srq        (bool) True if the power-on SRQ is set.
            cal_failed     (bool) True if meter calibration failed.
            keyboard_srq   (bool) True if the keyboard SRQ is set.
            hardware_error (bool) True if a hardware error occurred.
            syntax_error   (bool) True if a syntax error occurred.
            available      (bool) True if a reading is available(?).
        """
        bstat = self._bstatus
        return {
            'pon_srq' : bit_is_set(bstat[2], 7),
            'cal_failed' : bit_is_set(bstat[2], 5),
            'keyboard_srq' : bit_is_set(bstat[2], 4),
            'hardware_error' : bit_is_set(bstat[2], 3),
            'syntax_error' : bit_is_set(bstat[2], 2),
            'available' : bit_is_set(bstat[2], 0),
        }

    @property
    def error(self):
        """Meter error status.  Read-only dict value.

        The dict has the following keys:
            adc_link_error        (bool) True if the ADC had a link error.
            adc_selftest_error    (bool) True if the ADC had a self-test error.
            adc_slope_error       (bool) True if the ADC had a slope error.
            rom_selftest_error    (bool) True if the ROM had a self-test error.
            ram_selftest_error    (bool) True if the RAM had a self-test error.
            calram_checksum_error (bool) True if the calibration ram had a
                                         checksum error.
        """
        bstat = self._bstatus
        return {
            'adc_link_error' : bit_is_set(bstat[3], 5),
            'adc_selftest_error' : bit_is_set(bstat[3], 4),
            'adc_slope_error' : bit_is_set(bstat[3], 3),
            'rom_selftest_error' : bit_is_set(bstat[3], 2),
            'ram_selftest_error' : bit_is_set(bstat[3], 1),
            'calram_checksum_error' : bit_is_set(bstat[3], 0),
        }

    @property
    def function(self):
        """The current function of the meter.  Read/write string value.

        Valid values:
            VDC: DC Voltage (volts)
            VAC: AC Voltage (volts)
            RTW: Resistance (2-Wire, ohms)
            RFW: Resistance (4-Wire, ohms)
            IDC: DC Current (amps)
            IAC: AC Current (amps)
            REX: Extended Resistance
        """
        bstat = self._bstatus
        return HP3478A.functions[(bstat[0] >> 5) - 1]

    @function.setter
    def function(self, value):
        func = HP3478A.functions.index(value) + 1
        self.write("F{:d}".format(func))

    @property
    def range(self):
        """The meter reading range.  Read/write float or 'AUTO'.

        Note:
            Ranges are 3 * powers of 10, though will pick a reasonable
            range for most values in the ballpark.

            'AUTO' is the only valid non-numeric value.
        """
        bstat = self._bstatus
        # Get the bits that correspond to the range exponent
        exp_val = ((bstat[0] >> 2) & 0x07)

        # Adjust for function setting (unfortunately set/get of
        # range isn't symmetric)
        func = bstat[0] >> 5

        if func == 1:
            # DC Volts; range exponent offset by 3
            exp_val -= 3
        elif func in (2, 5, 6):
            # AC Volts, DC Current or AC Current; range exp offset by 2
            exp_val -= 2

        # Range is 3 * 10^exp_val
        return 3 * (10 ** exp_val)

    @range.setter
    def range(self, value):
        if value == 'AUTO':
            self.write('RA')
        else:
            # Problems with using log to determine rval on
            # some ranges so just implemented it the long way.
            if value <= 0.03:
                rval = -2
            elif value <= 0.3:
                rval = -1
            elif value <= 3:
                rval = 0
            elif value <= 30:
                rval = 1
            elif value <= 300:
                rval = 2
            elif value <= 3000:
                rval = 3
            elif value <= 30000:
                rval = 4
            elif value <= 300000:
                rval = 5
            elif value <= 3000000:
                rval = 6
            else:
                rval = 7

            self.write("R{:d}".format(rval))

    @property
    def resolution(self):
        """The number of digits in results.  Read/write int between 3 and 5.

        Higher resolutions will decrease conversion speed.
        """
        bstat = self._bstatus
        # Bottom 2 bits specify resolution
        r_val = bstat [0] & 0x03

        # 1 -> 5.5 digit mode, 2-> 4.5 digit mode, 3 -> 3.5 digit mode
        if r_val == 1:
            return 5
        elif r_val == 2:
            return 4
        else:
            return 3

    @resolution.setter
    def resolution(self, value):
        value = int(value)
        if 3 <= value <= 5:
            self.write('N{:d}'.format(value))
        else:
            raise ValueError("Invalid number of digits (must be between 3 and 5).")

    @property
    def trigger(self):
        bstat = self._bstatus
        if bit_is_set(bstat[1], 6):
            return 'E'
        elif bit_is_set(bstat[1], 0):
            return 'I'
        else:
            return 'H'

    @trigger.setter
    def trigger(self, value):
        """Meter trigger source control.  Read/write string value.

        Value is a single letter:
            I: Internal trigger
            E: External trigger
            S: Single trigger (immediate)
            H: Hold Trigger (stop triggering)
            F: Fast Trigger (immediate)
        """
        trig = HP3478A.triggers.index(value) + 1
        self.write("T{:d}".format(trig))

    @property
    def autozero(self):
        """Auto-zero control.  Read/write bool value.

        When true, auto-zero is enabled.
        """
        bstat = self._bstatus
        if bstat[1] & (1 << 2):
            return True
        else:
            return False

    @autozero.setter
    def autozero(self, value):
        if value:
            self.write('Z1')
        else:
            self.write('Z0')

    @property
    def text(self):
        """Text to show on meter's screen.  Write-only.

        Valid characters in string are space (32) through @ (95).
        """
        return None

    @text.setter
    def text(self, value):
        for i in range(0, len(value)):
            if ord(value[i]) < 32 or ord(value[i]) > 95:
                raise ValueError('Invalid characters in text.')

        self.write("D{:d}{:s}\n".format(self._textmode, value))

    @property
    def textmode(self):
        """The meter's text mode.  Read/write int value between 2 and 3.

        When 2, text written to display will persist; when 3, the display
        is turned off after writing the text, and will fade after about
        10 minutes.
        """
        return self._textmode

    @textmode.setter
    def textmode(self, value):
        value = int(value)
        if 2 <= value <= 3:
            self._textmode = value
        else:
            raise ValueError('Text mode must be 2 or 3.')

    @property
    def srq_mask(self):
        """The meter's SRQ mask.  Read/write int value."""
        return self._srq_mask

    @srq_mask.setter
    def srq_mask(self, value):
        value = int(value)
        self._srq_mask = value
        self.write("M{:2o}".format(value))

    def srq_clear(self):
        """Clear meter's SRQ bits."""
        self.write('K')

    def normal_display(self):
        """Set display to normal (use after setting text to for normal use)."""
        self.write('D1')

    def calibrate(self):
        """Enter calibration mode."""
        self.write('C')
