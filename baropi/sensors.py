import shutil as s
import psutil as ps
from os.path import isfile
from subprocess import check_output
from datetime import datetime
from . import models as m
from . import resources as r


try:
    import Adafruit_DHT as dht

except ImportError:
    print(" +++ using troll sensors with fake data")
    from random import randrange

    class dht():
        DHT22 = None

        @staticmethod
        def read_retry(s, p):
            return randrange(100), randrange(30)


def tomb(n):
    return n / 1000 ** 2


class Sensor:
    name = "noop"
    path = "get"

    def __init__(self, pin, delay, model, *args, **kwargs):
        self.pin = pin
        self.delay = delay
        self.Model = model
        self.resources = []

    def gather(self):
        raise NotImplementedError('you need to override gather() method of your Sensor')

    def get_sample(self):
        return self.Model(
            **self.gather()
        )


class DHT22Sensor(Sensor):
    name = "dht22"

    def __init__(self, *args, **kwargs):
        Sensor.__init__(self, model=m.ClimateSample, *args, **kwargs)
        self.resources = [
            r.ViewDHT22,
        ]

    def gather(self):
        humidity, temperature = dht.read_retry(
            dht.DHT22,
            self.pin
        )
        if not humidity or not temperature:
            raise RuntimeError("ResSensor %s failed to grab data" % self)
        return {
            'humidity': round(humidity, 3),
            'temperature': round(temperature, 3)
        }


class SentinelSensor(Sensor):
    name = "sentinel"

    def __init__(self, *args, **kwargs):
        Sensor.__init__(self, model=m.SentinelSample, *args, **kwargs)
        self.resources = [
            r.ViewSentinel,
        ]

    def get_temp(self):
        measure = None
        if isfile("/sys/class/thermal/thermal_zone0/temp"):
            temp = check_output(['cat', '/sys/class/thermal/thermal_zone0/temp']).decode()
            measure = int(temp) / 1000

        return {
            "temperature": measure
        }

    def gather(self):
        du = s.disk_usage('/')
        data = {
            "disk_total": tomb(du[0]),
            "disk_used": tomb(du[1]),
            "disk_free": tomb(du[2])
        }
        if hasattr(ps, "cpu_freq"):
            freq = ps.cpu_freq()
            data.update(
                {
                    "freq_current": freq[0],
                    "freq_min": freq[1],
                    "freq_max": freq[2]
                }
            )
        vms = ps.virtual_memory()
        data.update(
            {
                "total_ram": tomb(vms[0]),
                "avail_ram": tomb(vms[1]),
                "percent_ram": vms[2],
                "used_ram": tomb(vms[3]),
                "free_ram": tomb(vms[4]),
                "active_ram": tomb(vms[5]),
                "inactive_ram": tomb(vms[6]),
                "buffer": tomb(vms[7]),
                "cached": tomb(vms[8]),
                "shared": tomb(vms[9])
            }
        )
        data.update(
            self.get_temp()
        )
        return data