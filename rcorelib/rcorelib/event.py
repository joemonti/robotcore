# -*- coding: utf-8 -*-

import struct
import json

MSG_DATA_TYPE_BYTE    = 0
MSG_DATA_TYPE_INT     = 1
MSG_DATA_TYPE_LONG    = 2
MSG_DATA_TYPE_FLOAT   = 3
MSG_DATA_TYPE_DOUBLE  = 4
MSG_DATA_TYPE_STRING  = 5
MSG_DATA_TYPE_BYTEA   = 6
MSG_DATA_TYPE_JSON    = 7

MSG_DATA_TYPE_STRUCT = {
    MSG_DATA_TYPE_BYTE : { 'fmt': 'B' },
    MSG_DATA_TYPE_INT : { 'fmt': 'i' },
    MSG_DATA_TYPE_LONG : { 'fmt': 'l' },
    MSG_DATA_TYPE_FLOAT : { 'fmt': 'f' },
    MSG_DATA_TYPE_DOUBLE : { 'fmt': 'd' }
}

for k in MSG_DATA_TYPE_STRUCT.keys():
    MSG_DATA_TYPE_STRUCT[k]['size'] = struct.calcsize('>%s' % ( MSG_DATA_TYPE_STRUCT[k]['fmt'] ))

class RCoreEventTypeBuilder(object):
    def __init__(self, name):
        self.name = name
        self.dataTypes = []

    def add_byte(self):
        self.dataTypes.append(MSG_DATA_TYPE_BYTE)
        return self

    def add_int(self):
        self.dataTypes.append(MSG_DATA_TYPE_INT)
        return self

    def add_long(self):
        self.dataTypes.append(MSG_DATA_TYPE_LONG)
        return self

    def add_float(self):
        self.dataTypes.append(MSG_DATA_TYPE_FLOAT)
        return self

    def add_double(self):
        self.dataTypes.append(MSG_DATA_TYPE_DOUBLE)
        return self

    def add_string(self):
        self.dataTypes.append(MSG_DATA_TYPE_STRING)
        return self

    def add_bytea(self):
        self.dataTypes.append(MSG_DATA_TYPE_BYTEA)
        return self

    def add_json(self):
        self.dataTypes.append(MSG_DATA_TYPE_JSON)
        return self

    def build(self):
        return RCoreEventType(self.name, self.dataTypes)


class RCoreEventType(object):
    '''RobotCore Message Type'''
    def __init__(self, name, dataTypes, id=None, lock=None):
        self.name = name
        self.id = id
        self.lock = lock
        self.count = len(dataTypes)
        self.dataTypes = dataTypes

        if self.count > 1:
            for dtype in dataTypes[0:self.count-1]:
                if dtype in [ MSG_DATA_TYPE_STRING, MSG_DATA_TYPE_BYTEA, MSG_DATA_TYPE_JSON ]:
                    raise Exception("Invalid Types. Variable length type can only be last.")

    def buildEvent(self):
        return RCoreEventBuilder(self)

class RCoreEventBuilder(object):
    '''Builder for a RobotCore event'''
    def __init__(self, eventType):
        self.eventType = eventType
        self.buffer = bytearray()
        self.index = 0

    def add(self, value):
        if self.index >= self.eventType.count:
            raise Exception("Can't add to event, already %d items" % ( self.eventType.count ) )
        
        dtype = self.eventType.dataTypes[self.index]

        if dtype == MSG_DATA_TYPE_STRING or dtype == MSG_DATA_TYPE_BYTEA or dtype == MSG_DATA_TYPE_JSON:
            self.buffer.extend(value)
        else:
            fmt = '>%s' % ( MSG_DATA_TYPE_STRUCT[dtype]['fmt'] )
            self.buffer.extend(struct.pack(fmt, value))

        self.index += 1

        return self

    def build(self):
        return RCoreEvent(self.eventType, self.buffer)


class RCoreEvent(object):
    '''RCore Event'''
    def __init__(self, eventType, data):
        self.eventType = eventType
        self.data = data
        self.index = 0
    
    def serialize(self):
        buffer = bytearray(struct.pack('>h', self.eventType.id))
        buffer.extend(self.data)
        return buffer

    def reader(self):
        return RCoreEventReader(self)


class RCoreEventReader(object):
    def __init__(self, event):
        self.event = event
        self.data = None
        self.index = 0
        self.reset()

    def reset(self):
        self.data = self.event.data
        self.index = 0

    def read(self):
        if self.index >= self.event.eventType.count:
            raise Exception("Can't read more, already read %d items" % ( self.eventType.count ) )

        value = None

        dtype = self.event.eventType.dataTypes[self.index]
        if dtype == MSG_DATA_TYPE_STRING:
            value = self.data.decode()
            self.data = None
        elif dtype == MSG_DATA_TYPE_BYTEA:
            value = self.data
            self.data = None
        elif dtype == MSG_DATA_TYPE_JSON:
            value = json.loads(self.data.decode())
            self.data = None
        else:
            fmt = '>%s' % ( MSG_DATA_TYPE_STRUCT[dtype]['fmt'] )
            size = MSG_DATA_TYPE_STRUCT[dtype]['size']
            value = struct.unpack(fmt, self.data[:size])[0]
            self.data = self.data[size:]

        self.index += 1

        return value
