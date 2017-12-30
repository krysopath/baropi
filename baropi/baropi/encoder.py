#!/usr/bin/env python3
# coding=utf-8
from datetime import datetime
from functools import wraps
from json import JSONEncoder, dumps
from fractions import Fraction

from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.orm.query import Query

from .models import DataModel

__date_as_string__ = False
__date_as_dict__ = False
__date_as_epoche__ = True


class FractionEncoder(JSONEncoder):
    def default(self, obj):
        return float(obj)


class DatetimeEncoder(JSONEncoder):
    def default(self, obj):
        if __date_as_string__:
            res = str(obj)
        elif __date_as_dict__:
            res = {
                'year': obj.year,
                'month': obj.month,
                'day': obj.day,
                'hour': obj.hour,
                'minute': obj.minute,
                'second': obj.second,
            }
        elif __date_as_epoche__:
            res = obj.timestamp()

        return res


class AlchemyEncoder(JSONEncoder):
    def default(self, obj):
        fields = {}
        for field in [x for x in dir(obj)
                      if not x.startswith('_')
                      and x not in ['metadata',
                                    'query',
                                    'query_class',
                                    'generate_auth_token',
                                    'set_hash',
                                    'check_hash',
                                    'verify_auth_token',
                                    'hash']]:
            data = obj.__getattribute__(field)
            try:
                # print('AlchemyEncoder:', data.__class__, data)
                dumps(data)  # this will fail on non-encodable values, like other classes
                fields[field] = data
            except TypeError as te:
                if isinstance(data, datetime):
                    print(data)
                    if __date_as_string__:
                        fields[field] = str(data)
                    elif __date_as_dict__:
                        fields[field] = {
                            'year': data.year,
                            'month': data.month,
                            'day': data.day,
                            'hour': data.hour,
                            'minute': data.minute,
                            'second': data.second,
                        }
                    elif __date_as_epoche__:
                        fields[field] =  data.timestamp()

                elif isinstance(data, InstrumentedList):
                    fields[field] = {
                        x.id: x.__str__() for x in data
                    }

                elif isinstance(data, Query):
                    fields[field] = {
                        x.id: x.name for x in data.all()
                    }

                else:
                    print(obj.__class__())
                    fields[field] = None
                    raise RuntimeError("unhandled object for custom json encoder")

        return fields


class APIEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return DatetimeEncoder(
                indent=None,
                check_circular=False
            ).default(obj)

        elif isinstance(obj, Fraction):
            return FractionEncoder(
                indent=None,
                check_circular=False
            ).default(obj)

            # elif isinstance(obj.__class__, DeclarativeMeta):
            #    return AlchemyEncoder(
            #        indent=None,
            #        check_circular=False
            #    ).default(obj)


def jsonize(obj):
    """
    !!!unused!!!
    :param obj: 
    :return: 
    """

    @wraps(obj)
    def wrapped(*args,
                **kwargs):
        result = obj(*args,
                     **kwargs)
        return dumps(
            result,
            cls=APIEncoder,
            indent=None
        )

    return wrapped