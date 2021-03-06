# -*- coding: utf-8 -*-
"""
event.py

This file is part of RobotCore.

RobotCore is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

RobotCore is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with RobotCore.  If not, see <http://www.gnu.org/licenses/>.

@author: Joseph Monti <joe.monti@gmail.com>
@copyright: 2015 Joseph Monti All Rights Reserved, http://joemonti.org/
"""

import struct
import json
# import traceback


MSG_DATA_TYPE_BYTE = 0
MSG_DATA_TYPE_INT = 1
MSG_DATA_TYPE_LONG = 2
MSG_DATA_TYPE_FLOAT = 3
MSG_DATA_TYPE_DOUBLE = 4
MSG_DATA_TYPE_STRING = 5
MSG_DATA_TYPE_BYTEA = 6
MSG_DATA_TYPE_JSON = 7

MSG_DATA_TYPE_STRUCT = {
    MSG_DATA_TYPE_BYTE: {'fmt': 'B'},
    MSG_DATA_TYPE_INT: {'fmt': 'i'},
    MSG_DATA_TYPE_LONG: {'fmt': 'l'},
    MSG_DATA_TYPE_FLOAT: {'fmt': 'f'},
    MSG_DATA_TYPE_DOUBLE: {'fmt': 'd'}
}

MSG_DATA_TYPES_VARS = [
    MSG_DATA_TYPE_STRING,
    MSG_DATA_TYPE_BYTEA,
    MSG_DATA_TYPE_JSON
]

for k in MSG_DATA_TYPE_STRUCT.keys():
    MSG_DATA_TYPE_STRUCT[k]['size'] = \
        struct.calcsize('>%s' % (MSG_DATA_TYPE_STRUCT[k]['fmt']))


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

        '''
        if self.count > 1:
            for dtype in dataTypes[0:self.count-1]:
                if dtype in MSG_DATA_TYPES_VARS:
                    raise Exception(
                        "Invalid Types. Variable length type can only be last."
                        )
        '''

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
            raise Exception("Can't add to event, already %d items" %
                            (self.eventType.count))

        dtype = self.eventType.dataTypes[self.index]

        if dtype in MSG_DATA_TYPES_VARS:
            if dtype == MSG_DATA_TYPE_STRING and type(value) != str:
                value = str(value)
            elif dtype == MSG_DATA_TYPE_JSON and \
                    type(value) not in [str, unicode, bytearray]:
                value = json.dumps(value)

            if (self.index+1) < self.eventType.count:
                self.buffer.extend(struct.pack('>i', len(value)))

            self.buffer.extend(value)
        else:
            fmt = '>%s' % (MSG_DATA_TYPE_STRUCT[dtype]['fmt'])
            self.buffer.extend(struct.pack(fmt, value))

        self.index += 1

        return self

    def add_byte(self, value):
        if self.index >= self.eventType.count:
            raise Exception("Can't add to event, already %d items" %
                            (self.eventType.count))
        self.buffer.extend(struct.pack('>B', value))
        self.index += 1
        return self

    def add_int(self, value):
        if self.index >= self.eventType.count:
            raise Exception("Can't add to event, already %d items" %
                            (self.eventType.count))
        self.buffer.extend(struct.pack('>i', value))
        self.index += 1
        return self

    def add_long(self, value):
        if self.index >= self.eventType.count:
            raise Exception("Can't add to event, already %d items" %
                            (self.eventType.count))
        self.buffer.extend(struct.pack('>l', value))
        self.index += 1
        return self

    def add_float(self, value):
        if self.index >= self.eventType.count:
            raise Exception("Can't add to event, already %d items" %
                            (self.eventType.count))
        self.buffer.extend(struct.pack('>f', value))
        self.index += 1
        return self

    def add_double(self, value):
        if self.index >= self.eventType.count:
            raise Exception("Can't add to event, already %d items" %
                            (self.eventType.count))
        self.buffer.extend(struct.pack('>d', value))
        self.index += 1
        return self

    def add_string(self, value):
        if self.index >= self.eventType.count:
            raise Exception("Can't add to event, already %d items" %
                            (self.eventType.count))
        if type(value) != str:
            value = str(value)
        if (self.index+1) < self.eventType.count:
            self.buffer.extend(struct.pack('>i', len(value)))

        self.buffer.extend(value)
        self.index += 1
        return self

    def add_bytea(self, value):
        if self.index >= self.eventType.count:
            raise Exception("Can't add to event, already %d items" %
                            (self.eventType.count))
        if (self.index+1) < self.eventType.count:
            self.buffer.extend(struct.pack('>i', len(value)))

        self.buffer.extend(value)
        self.index += 1
        return self

    def add_json(self, value):
        if self.index >= self.eventType.count:
            raise Exception("Can't add to event, already %d items" %
                            (self.eventType.count))
        if type(value) not in [str, unicode, bytearray]:
            value = json.dumps(value)
        if (self.index+1) < self.eventType.count:
            self.buffer.extend(struct.pack('>i', len(value)))

        self.buffer.extend(value)
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
        self.serialized = None

    def serialize(self):
        if self.serialized is None:
            buffer = bytearray(struct.pack('>h', self.eventType.id))
            buffer.extend(self.data)
            self.serialized = buffer
            return buffer
        else:
            return self.serialized

    def reader(self):
        return RCoreEventReader(self)

    @staticmethod
    def from_data(data, getEventForId):
        eventTypeId = struct.unpack('>h', data[:2])[0]
        eventType = getEventForId(eventTypeId)
        eventData = data[2:]
        if type(eventData) != bytearray:
            eventData = bytearray(eventData)
        return RCoreEvent(eventType, eventData)


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
            raise Exception("Can't read more, already read %d items" %
                            (self.event.eventType.count))

        value = None

        dtype = self.event.eventType.dataTypes[self.index]
        if dtype == MSG_DATA_TYPE_STRING:
            value = self.read_var_data().decode()
        elif dtype == MSG_DATA_TYPE_BYTEA:
            value = self.read_var_data()
        elif dtype == MSG_DATA_TYPE_JSON:
            value = json.loads(self.read_var_data().decode())
        else:
            fmt = '>%s' % (MSG_DATA_TYPE_STRUCT[dtype]['fmt'])
            size = MSG_DATA_TYPE_STRUCT[dtype]['size']
            value = struct.unpack(fmt, self.data[:size])[0]
            self.data = self.data[size:]

        self.index += 1

        return value

    def read_var_data(self):
        value = None
        if (self.index+1) < self.event.eventType.count:
            lensize = MSG_DATA_TYPE_STRUCT[MSG_DATA_TYPE_INT]['size']
            lenval = struct.unpack('>i', self.data[:lensize])[0]
            value = self.data[lensize:lensize+lenval]
            self.data = self.data[lensize+lenval:]
        else:
            value = self.data
            self.data = None
        return value


EVT_TYPE_MGT_REGISTER_EVENT_TYPE = \
    RCoreEventTypeBuilder('register_event_type') \
    .add_string() \
    .add_bytea() \
    .build()

EVT_TYPE_MGT_REGISTER_EVENT_TYPE_RESP = \
    RCoreEventTypeBuilder('register_event_type_response') \
    .add_int() \
    .build()

EVT_TYPE_MGT_READ_EVENT_TYPE = \
    RCoreEventTypeBuilder('read_event_type') \
    .add_string() \
    .build()

EVT_TYPE_MGT_READ_EVENT_TYPE_RESP = \
    RCoreEventTypeBuilder('read_event_type_response') \
    .add_int() \
    .add_string() \
    .add_bytea() \
    .build()

EVT_TYPE_MGT_EVENT_RESP = \
    RCoreEventTypeBuilder('event_response') \
    .build()

EVT_TYPE_MGT_TYPES = [
    EVT_TYPE_MGT_REGISTER_EVENT_TYPE,
    EVT_TYPE_MGT_REGISTER_EVENT_TYPE_RESP,
    EVT_TYPE_MGT_READ_EVENT_TYPE,
    EVT_TYPE_MGT_READ_EVENT_TYPE_RESP,
    EVT_TYPE_MGT_EVENT_RESP
]

for i in range(len(EVT_TYPE_MGT_TYPES)):
    EVT_TYPE_MGT_TYPES[i].id = (i+1)
