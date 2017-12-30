# !/usr/bin/env python3
# coding=utf-8
from os import mkdir, environ, chmod, lstat
from os.path import exists
import stat
from os.path import isfile
import yaml

# import pydis

paranoid = False
__home__ = '%s/baropi' % environ['HOME']
__dbfile__ = '%s/klima.db' % __home__

default = """---
server:                                         # informs the flask-app about interface and port to bind to
    interface: 192.168.0.192 
    port: 5555
    prefix: baropi

db:                                             # connection info on the sql server, we dump sensor data in
    path: %s                                    # we used sqlite in the past, so we keep this for the future
    connection:                                      # 
        dialect: mysql+pymysql                      # change this at your own risk
        user: baropi                                # sql user that can SELECT/INSERT on the baropi db
        pw: g25v09e85                               # the password of the user
        host: 192.168.0.254                         # the interface the sql server is listening
        port: 3306                                  # port of the sql server

redis:                                          # we use redis for not wearing sd cards of raspberry-pi
    enabled: no                                 # we really use redis now?
    pickle:
        enabled: yes
        pickle_proto: -1                            # protocol for pickled objects in redis 0-2, -1 for highest
    connection:
        host: 192.168.0.254                         # interface of redis
        port: 6379                                  # port of redis
        db: 0                                       # redis db index we use for baropi data
        password: $5aEc8-0/4d7F9-8                        # we better secured our redis in the past and need to auth via password



# define all sensors we baropi with

sensors:                                        
    - {module: DHT22Sensor, pin: 4, delay: 10, path: dht22}  # options dictionary for your sensor goes here
    - {module: SentinelSensor, pin: 4, delay: 10, path: sentinel}
    #- {module: EmailEventSensor, pin: false, delay: 100}

 
""" % (__dbfile__,)

user_conf_path = "%s/baropi.yml" % __home__


def check_perms(path):
    if not oct(stat.S_IMODE(lstat(path).st_mode)) in ["0o600"]:
        if paranoid:
            raise RuntimeError("%s has wrong permissions (needs 600)" % path)
        else:
            print(' ---', path, "has wrong permissions. adjusting")
            chmod(path, 0o600)


def load_cfg(path):
    check_perms(path)
    return yaml.safe_load(
        open(path)
    )


def recreate_cfg():
    print(" --- no valid config found. creating..")
    with open(user_conf_path, "w") as default_cfg:
        default_cfg.write(default)


def start_up():
    if not exists(__home__):
        mkdir(__home__)

    if not isfile(user_conf_path):
        recreate_cfg()
        chmod(user_conf_path, 0o600)

    return load_cfg(user_conf_path)


class Config:
    def __init__(self, data):
        for k, v in data.items():
            if isinstance(v, dict):
                setattr(
                    self,
                    str(k), Config(v)
                )
            else:
                setattr(
                    self,
                    str(k), v
                )


conf = start_up()
print(" +++ running config:", conf)
cfg = Config(conf)