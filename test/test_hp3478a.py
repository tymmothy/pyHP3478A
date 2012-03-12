#!/usr/bin/python

from hp3478a import HP3478A

if __name__ == '__main__':
    import time

    meter = HP3478A('dev23')

    meter.function = 'VDC'
    print meter.function
    meter.range = 30
    print meter.range
    meter.text = "HI"
    time.sleep(5)
    meter.normal_display()
    for i in xrange(0, 100):
        print meter.reading
