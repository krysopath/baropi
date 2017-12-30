#!/usr/bin/env python3
# coding=utf-8
import pickle as p
from uuid import uuid4
from baropi.config import cfg
import base64
import json
import redis
import os


class RedisObject(object):
    '''
    A base object backed by redis.
    Genrally, use RedisDict or RedisList rather than this directly.
    '''

    def __init__(self, id=None):
        '''Create or load a RedisObject.'''
        self.redis = make_strict_redis_conn()  # redis.StrictRedis(host='redis', decode_responses=True)
        if id:
            self.id = id
        else:
            self.id = base64.urlsafe_b64encode(os.urandom(9)).decode('utf-8')
        if ':' not in self.id:
            self.id = self.__class__.__name__ + ':' + self.id

    def __bool__(self):
        '''Test if an object currently exists'''
        return self.redis.exists(self.id)

    def __eq__(self, other):
        '''Tests if two redis objects are equal (they have the same key)'''
        return self.id == other.id

    def __str__(self):
        '''Return this object as a string for testing purposes.'''
        return self.id

    def delete(self):
        """Delete this object from redis"""
        self.redis.delete(self.id)

    @staticmethod
    def decode_value(type, value):
        """Decode a value if it is non-None, otherwise, decode with no arguments."""
        if value == None:
            return type()
        else:
            return type(value)

    @staticmethod
    def encode_value(value):
        '''Encode a value using json.dumps, with default = str'''
        return str(value)


class RedisDict(RedisObject):
    '''An equivalent to dict where all keys/values are stored in Redis.'''

    def __init__(self, id=None, fields={}, defaults=None):
        '''
        Create a new RedisObject
        id: If specified, use this as the redis ID, otherwise generate a random ID.
        fields: A map of field name to construtor used to read values from redis.
            Objects will be written with json.dumps with default = str, so override __str__ for custom objects.
            This should generally be set by the subobject's constructor.
        defaults: A map of field name to values to store when constructing the object.
        '''

        RedisObject.__init__(self, id)

        self.fields = fields

        if defaults:
            for key, val in defaults.items():
                self[key] = val

    def __getitem__(self, key):
        '''
        Load a field from this redis object.
        Keys that were not specified in self.fields will raise an exception.
        Keys that have not been set (either in defaults or __setitem__) will return the default for their type (if set)
        '''

        if key == 'id':
            return self.id

        if not key in self.fields:
            raise KeyError('{} not found in {}'.format(key, self))

        return RedisObject.decode_value(self.fields[key], self.redis.hget(self.id, key))

    def __setitem__(self, key, val):
        '''
        Store a value in this redis object.
        Keys that were not specified in self.fields will raise an exception.
        Keys will be stored with json.dumps with a default of str, so override __str__ for custom objects.
        '''

        if not key in self.fields:
            raise KeyError('{} not found in {}'.format(key, self))

        self.redis.hset(self.id, key, RedisObject.encode_value(val))

    def __iter__(self):
        '''Return (key, val) pairs for all values stored in this RedisDict.'''

        yield ('id', self.id.rsplit(':', 1)[-1])

        for key in self.fields:
            yield (key, self[key])


class RedisList(RedisObject):
    '''An equivalent to list where all items are stored in Redis.'''

    def __init__(self, id=None, item_type=str, items=None):
        '''
        Create a new RedisList
        id: If specified, use this as the redis ID, otherwise generate a random ID.
        item_type: The constructor to use when reading items from redis.
        values: Default values to store during construction.
        '''

        RedisObject.__init__(self, id)

        self.item_type = item_type

        if items:
            for item in items:
                self.append(item)

    @classmethod
    def as_child(cls, parent, tag, item_type):
        '''Alternative callable constructor that instead defines this as a child object'''

        def helper(_=None):
            return cls(parent.id + ':' + tag, item_type)

        return helper

    def __getitem__(self, index):
        '''
        Load an item by index where index is either an int or a slice
        Warning: this is O(n))
        '''

        if isinstance(index, slice):
            if slice.step != 1:
                raise NotImplemented('Cannot specify a step to a RedisObject slice')

            return [
                RedisObject.decode_value(self.item_type, el)
                for el in self.redis.lrange(self.id, slice.start, slice.end)
            ]
        else:
            return RedisObject.decode_value(self.item_type, self.redis.lindex(self.id, index))

    def __setitem__(self, index, val):
        '''Update an item by index
        Warning: this is O(n)
        '''
        self.redis.lset(self.id, index, RedisObject.encode_value(val))

    def __len__(self):
        '''Return the size of the list.'''
        return self.redis.llen(self.id)

    def __delitem__(self, index):
        '''Delete an item from a RedisList by index. (warning: this is O(n))'''
        self.redis.lset(self.id, index, '__DELETED__')
        self.redis.lrem(self.id, 1, '__DELETED__')

    def __iter__(self):
        '''Iterate over all items in this list.'''
        for el in self.redis.lrange(self.id, 0, -1):
            yield RedisObject.decode_value(self.item_type, el)

    def lpop(self):
        '''Remove and return a value from the left (low) end of the list.'''
        return RedisObject.decode_value(self.item_type, self.redis.lpop(self.id))

    def rpop(self):
        '''Remove a value from the right (high) end of the list.'''
        return RedisObject.decode_value(self.item_type, self.redis.rpop(self.id))

    def lpush(self, val):
        '''Add an item to the left (low) end of the list.'''
        self.redis.lpush(self.id, RedisObject.encode_value(val))

    def rpush(self, val):
        '''Add an item to the right (high) end of the list.'''
        self.redis.rpush(self.id, RedisObject.encode_value(val))

    def append(self, val):
        self.rpush(val)


def make_redis_conn(host=cfg.redis.host,
                    port=cfg.redis.port,
                    pw=cfg.redis.password,
                    db=cfg.redis.db):
    return redis.Redis(
        host=host,
        port=port,
        password=pw,
        db=db
    )


def make_strict_redis_conn(
        host=cfg.redis.host,
        port=cfg.redis.port,
        pw=cfg.redis.password,
        db=cfg.redis.db):
    return redis.StrictRedis(
        host=host,
        port=port,
        password=pw,
        db=db,
        decode_responses=True
    )


class Piredis:
    def __init__(self, redis_instance=None, prefix="client"):
        self.uuid = uuid4()
        if not redis_instance:
            redis_instance = make_redis_conn()
            redis_instance.client_setname(
                "piredis-%s-%s" % (prefix, self.uuid)
            )
        self.r = redis_instance
        self.prefix = prefix

    def mk_key(self, k):
        return "{}:{}".format(
            self.prefix, k
        )

    def encode(self, data):
        return p.dumps(
            data,
            protocol=cfg.redis.pickle_proto
        )

    def decode(self, data):
        return p.loads(data)

    def set(self, k, data):
        return self.r.set(
            self.mk_key(k), data
        )

    def get(self, k):
        return self.r.get(
            self.mk_key(k)
        )

    def rpush(self, _list, v):
        return self.r.rpush(
            self.mk_key(_list), v
        )

    def lpush(self, _list, v):
        return self.r.lpush(
            self.mk_key(_list), v
        )

    def lindex(self, _list, i):
        return self.r.lindex(
            self.mk_key(_list), i
        )

    def lrange(self, _list, a, b):
        return self.r.lrange(
            self.mk_key(_list), a, b
        )

    def hget(self, _hash, k):
        return self.r.hget(
            self.mk_key(_hash), k
        )

    def hset(self, _hash, k, v):
        return self.r.hset(
            self.mk_key(_hash), k, v
        )