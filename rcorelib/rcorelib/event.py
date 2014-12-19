# -*- coding: utf-8 -*-

import struct

MSG_DATA_TYPE_BYTE    = 0
MSG_DATA_TYPE_INT     = 1
MSG_DATA_TYPE_LONG    = 2
MSG_DATA_TYPE_FLOAT   = 3
MSG_DATA_TYPE_DOUBLE  = 4
MSG_DATA_TYPE_STRING  = 5
MSG_DATA_TYPE_BYTEA   = 6

MSG_DATA_TYPE_STRUCT_FMT = {
    MSG_DATA_TYPE_BYTE : 'B',
    MSG_DATA_TYPE_INT : 'i',
    MSG_DATA_TYPE_LONG : 'l',
    MSG_DATA_TYPE_FLOAT : 'f',
    MSG_DATA_TYPE_DOUBLE : 'd'
}


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

    def build(self):
        return RCoreEventType(self.name, self.dataTypes)


class RCoreEventType(object):
    '''RobotCore Message Type'''
    def __init__(self, name, dataTypes):
        self.name = name
        self.count = len(dataTypes)
        self.dataTypes = dataTypes

        if self.count > 1:
            for dtype in dataTypes[0:self.count-1]:
                if dtype in [ MSG_DATA_TYPE_STRING, MSG_DATA_TYPE_BYTEA ]:
                    raise Exception("Invalid Types. Variable length type can only be last.")


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
        if dtype == MSG_DATA_TYPE_STRING or dtype == MSG_DATA_TYPE_BYTEA:
            self.buffer.extend(value)
        else:
            fmt = '>%s' % ( MSG_DATA_TYPE_STRUCT_FMT[dtype] )
            struct.pack_into(fmt, self.buffer, len(self.buffer), value)
        return self

    def build(self):
        return RCoreEvent(self.evenType, self.data)


class RCoreEvent(object):
    '''RCore Event'''
    def __init__(self, eventType, data):
        self.eventType = eventType
        self.data = data
        self.index = 0

