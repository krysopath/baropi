#!/usr/bin/env python3
# coding=utf-8

from flask import g
from flask_restful import Resource
from .config import conf
from . import models as m
import datetime as dt

# from redisworks import Root

redis_conf = conf['redis']['connection']

__all__ = [
    "ViewDHT22",
    "ViewSentinel"
]


class SampleViewer(Resource):
    path = "get"
    such_args = "<string:unix_time>"

    def __init__(self):
        Resource.__init__(self)

    def get(self, unix_time):
        if unix_time == "last":
            s = self.last_item
        else:
            s = self.get_by_timestamp(unix_time)
        if s:
            return s.data

    def get_by_timestamp(self, unix_time):
        return g.db.query(
            self.Model
        ).filter(
            self.Model.creation_time == dt.datetime.fromtimestamp(
                float(unix_time)
            )
        ).first()


    @property
    def last_item(self):
        return g.db.query(self.Model).order_by(
            self.Model.id.desc()
        ).first()


class ViewDHT22(SampleViewer):
    # name = "get"

    def __init__(self, *args, **kwargs):
        super(ViewDHT22, self).__init__()
        self.Model = m.ClimateSample


class ViewSentinel(SampleViewer):
    #name = "get"

    def __init__(self, *args, **kwargs):
        super(ViewSentinel, self).__init__()
        self.Model = m.SentinelSample