# -*- coding: utf-8 -*-
"""
__init__.py

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

import zmq
import threading
import traceback
import event
import struct
# import json

PORT_MGT = 12210
PORT_PUBSUB = 12211


class RCoreClient(object):
    '''RobotCore Client'''
    def __init__(self, server, name, ctx=None):
        self.ctx = ctx
        self.termContext = False
        if self.ctx is None:
            self.ctx = zmq.Context()
            self.termContext = True

        self.sockMgt = self.ctx.socket(zmq.REQ)
        self.sockMgt.connect("tcp://%s:%d" % (server, PORT_MGT))

        self.sockSub = self.ctx.socket(zmq.SUB)
        self.sockSub.connect("tcp://%s:%d" % (server, PORT_PUBSUB))

        self.typesByName = {}
        self.typesById = {}

        for eventType in event.EVT_TYPE_MGT_TYPES:
            self.typesByName[eventType.name] = eventType
            self.typesById[eventType.id] = eventType

        self.listeners = {}

    def get_event_types(self):
        pass  # list event types via management interface

    def read_event_type(self, name):
        if name in self.typesByName:
            return self.typesByName[name]
        else:
            evt = event.RCoreEventBuilder(event.EVT_TYPE_MGT_READ_EVENT_TYPE) \
                    .add(name).build()
            respevt = self.call_mgt_command(evt)

            respreader = respevt.reader()
            respid = respreader.read()
            respname = respreader.read()
            respDataTypes = [i for i in respreader.read()]

            if respid >= 0:
                eventType = event.RCoreEventType(respname,
                                                 respDataTypes,
                                                 id=respid)
                self.typesByName[name] = eventType
                self.typesById[respid] = eventType
                return eventType
            else:
                return None

    def register_event_type(self, eventType):
        evt = event.RCoreEventBuilder(event.EVT_TYPE_MGT_REGISTER_EVENT_TYPE) \
                    .add(eventType.name).add(eventType.dataTypes).build()

        respevt = self.call_mgt_command(evt)

        respreader = respevt.reader()
        respid = respreader.read()
        if respid >= 0:
            eventType.id = respid
            self.typesByName[eventType.name] = eventType
            self.typesById[respid] = eventType
            return eventType
        else:
            raise Exception("Error registering event type %s" %
                            (eventType.name))

    def call_mgt_command(self, evt):
        data = evt.serialize()
        self.sockMgt.send(data)
        resp = self.sockMgt.recv()
        respevt = event.RCoreEvent.from_data(resp,
                                             lambda id: self.typesById[id])
        return respevt

    def send(self, evt):
        data = evt.serialize()
        self.sockMgt.send(data)
        self.sockMgt.recv()  # ignore response, but must receive on pub-sub

    def register_listener(self, eventTypeName, callback):
        eventListeners = None
        if eventTypeName in self.listeners:
            eventListeners = self.listeners[eventTypeName]
        else:
            eventListeners = []
            self.listeners[eventTypeName] = eventListeners
            eventType = self.read_event_type(eventTypeName)
            self.sockSub.setsockopt(zmq.SUBSCRIBE,
                                    struct.pack('>h', eventType.id))

        eventListeners.append(callback)

    def start(self):
        self.t = threading.Thread(target=self.run_listeners)
        self.running = True
        self.t.start()

    def close(self):
        self.running = False
        self.sockMgt.close()
        self.sockSub.close()
        if self.termContext:
            self.ctx.term()

    def run_listeners(self):
        print 'Started Listener'
        try:
            while self.running:
                data = self.sockSub.recv()

                print 'Received: %s' % (data)

                evt = event.RCoreEvent.from_data(data,
                                                 lambda id: self.typesById[id])

                if evt.eventType.name in self.listeners:
                    for listener in self.listeners[evt.eventType.name]:
                        listener(evt)
        except:
            traceback.print_exc()
            self.close()


def demo():
    def my_receiver(t, d):
        print 'GOT [type:%s] [data:%s]' % (t, d)

    c = RCoreClient('localhost', 'me')
    c.register_listener('foo', my_receiver)
    c.start()

    return c
