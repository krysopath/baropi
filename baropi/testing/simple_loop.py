import time as t
from . import database as db
from . import models as m
from .sensors import dht


def grab_from_sensors_loop():
    sensor = dht.DHT22
    pin = 4
    db.init_db()
    while True:
        sample = m.ClimateSample(
            dht.read_retry(sensor, pin)
        )
        db.db_session.add(sample)
        t.sleep(10)
        db.db_session.commit()


