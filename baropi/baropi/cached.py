#!/usr/bin/env python3
# coding=utf-8
from baropi import init_db, db_session
from baropi.models import EventRequest
from baropi.config import conf
from baropi import pydis as p

p.redis_config = conf['redis']['connection']
import bcrypt


class User(p.RedisDict):
    def __init__(self, id=None, email=None, **defaults):
        # Use email as id, if specified
        if email:
            id = email
            defaults['email'] = email

        p.RedisDict.__init__(
            self,
            id=email,
            fields={
                'name': str,
                'email': str,
                'password': str,
                'friends': p.RedisList.as_child(self, 'friends', str),
            },
            defaults=defaults
        )

    def __setitem__(self, key, val):
        '''Override the behavior if user is trying to change the password'''
        if key == 'password':
            val = bcrypt.hashpw(
                val.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
        p.RedisDict.__setitem__(self, key, val)

    def verify(self, pw):
        hashed = bcrypt.hashpw(
            pw.encode('utf-8'),
            self['password'].encode('utf-8')
        ).decode('utf-8')

        return hashed == self['password']


class SampleHolder(p.RedisDict):
    def __init__(self, id=None, **defaults):
        p.RedisDict.__init__(
            self,
            id=id,
            fields={
                'climate': p.RedisList.as_child(self, 'friends', dict),
                'sentinel': p.RedisList.as_child(self, 'friends', dict),
                'event_request': p.RedisList.as_child(self, 'friends', dict),
            },
            # defaults=defaults
        )

    def __setitem__(self, key, val):
        '''Override the behavior if user is trying to change the password'''
        if key == 'password':
            val = bcrypt.hashpw(
                val.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
        p.RedisDict.__setitem__(self, key, val)

    def verify(self, pw):
        hashed = bcrypt.hashpw(
            pw.encode('utf-8'),
            self['password'].encode('utf-8')
        ).decode('utf-8')

        return hashed == self['password']


class RedisSample(p.RedisDict):
    """
    {'timestamp': None, 'steampressure_saturated_hPa': 18.179817588509366, 'dew_point_celsius': 3.1103139701744253, 'mdate': None, 'moisture_gpm3': 5.7220058489083, 'temperature': 16, 'steam_pressure_hPa': 7.635523387173933, 'humidity': 42, 'id': None, 't_Kelvin': Fraction(2543390297371443, 8796093022208), 'extra': None}
    {'disk_free': 32887.615488, 'shared': 93.843456, 'avail_ram': 5646.11072, 'active_ram': 4353.077248, 'extra': None, 'cached': 3762.3808, 'temperature': 52.0, 'total_ram': 8356.532224, 'id': None, 'buffer': 88.469504, 'used_ram': 2349.211648, 'timestamp': None, 'percent_ram': 32.4, 'freq_current': 3288.92475, 'disk_used': 13676.167168, 'freq_min': 1600.0, 'free_ram': 2156.470272, 'inactive_ram': 1573.138432, 'disk_total': 49080.573952, 'freq_max': 3400.0}
    


    """

    def __init__(self, Model=None, *args, **kwargs):
        fields = {'id': int}
        super().__init__(fields=fields)


class RedisEventRequest(p.RedisDict):
    def __init__(self, event_request_instance, *args, **kwargs):
        sample = event_request_instance
        fields = {
            'requester_phone': str,
            'visitor_count': int,
            'timestamp': float,
            'requester_email': str,
            'start': float,
            'extra': str,
            'end': int,
            'location': str,
            'id': str,
            'requester_name': str,
            'event_name': str
        }

        super().__init__(
            id=str(sample.timestamp), fields=fields, defaults=kwargs
        )


if __name__ == "__main__":
    u = User(email="krysopath@gmail.com", name="Georg vom Endt", password="g25v09e85")
    init_db()
    s = db_session.query(EventRequest).limit(1).first()
    sh = SampleHolder("baropi")
    print(sh)
    # r = RedisEventRequest(s)
    # print(r)
    # print(r.keys())
    # print(r['end_time'])