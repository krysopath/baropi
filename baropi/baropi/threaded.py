#!/usr/bin/env python3
from threading import Thread, Event
from sqlalchemy.exc import SQLAlchemyError
from . import database as db
from . import sensors as sensors_module
from .config import cfg, conf
from redisworks import Root

redis_conf = conf['redis']['connection']


class GrabberThread(Thread):
    def __init__(self, event, sensor):
        Thread.__init__(self)
        self.sensor = sensor
        self.stopped = event
        self.db = db.make_session()
        # if cfg.redis.enabled:
        #    self.redis = Root(
        #        **conf['redis']['connection'],
        #        root_name="baropi")
        #    print(" +++", self.redis, "connecting to", redis_conf)

    def ask_sensor(self):
        return self.sensor.get_sample()

    def put_db(self, sample):
        try:
            self.db.add(sample)
            self.db.commit()
        except SQLAlchemyError as sqlae:
            self.db.rollback()
            print("   --", sqlae.args, sample)
            raise SQLAlchemyError("general sql db error?!", sqlae.args, sample)

    def put_redis(self, sample):

        data = getattr(
            self.redis,
            "{}".format(self.sensor.name))
        getattr(data, "update")(
            {sample.timestamp: sample.data}
        )

    def commit(self, sample):
        self.put_db(sample)
        # if cfg.redis.enabled:
        #    self.put_redis(sample)

    def run(self):
        while not self.stopped.wait(self.sensor.delay):
            try:
                sample = self.ask_sensor()
            except Exception as e:
                raise e
            finally:
                self.commit(sample)


def __create_thread__(threaded_sensor):
    stop_flag = Event()
    return GrabberThread(
        stop_flag,
        threaded_sensor
    ), stop_flag


def run_sensor_thread(sensor_class_name, pin, delay):
    try:
        such_sensor_class = getattr(
            sensors_module, sensor_class_name
        )

        thread, stop_flag = __create_thread__(
            such_sensor_class(
                pin=pin, delay=delay)
        )
        try:
            thread.start()
        except KeyboardInterrupt:
            stop_flag.set()

    except:
        raise ValueError("%s is not a valid sensor!" % sensor_class_name)