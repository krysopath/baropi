# !/usr/bin/env python3
# coding=utf-8
import baropi as b


def run_test(sensor, pin, delay):
    try:
        test_sensor = getattr(b.sensors, sensor)
    except:
        raise ValueError("%s is not a valid sensor!" % test_sensor)

    s = test_sensor(pin=pin, delay=delay)

    print(s.name)
    print(s, s.Model)
    print(s.get_sample().data)
    print(s.resources)
    for r in s.resources:
        print(r.name, r.such_args)



if __name__ == "__main__":
    b.init_db()
    for sensor in b.cfg.sensors:
        run_test(sensor['module'], sensor['pin'], sensor['delay'])

    b.run_sensor_thread("DHTSensor", None, 5)