#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
rcoremaster.py

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

# import sys
import threading
import traceback
import time

import zmq

import rcorelib
import rcorelib.event as revent

MGT_EVENT_RESP = revent.RCoreEventBuilder(revent.EVT_TYPE_MGT_EVENT_RESP) \
    .build()

class RCoreMaster(object):
    '''Master RobotCore daemon'''
    def __init__(self, ctx):
        self.clients = {}
        self.types_by_id = {}
        self.types_by_name = {}

        for event_type in revent.EVT_TYPE_MGT_TYPES:
            self.types_by_name[event_type.name] = event_type
            self.types_by_id[event_type.id] = event_type

        self.sock_mgt = ctx.socket(zmq.REP)
        self.sock_mgt.bind("tcp://*:%d" % (rcorelib.PORT_MGT))

        self.sock_pub = ctx.socket(zmq.PUB)
        self.sock_pub.bind("tcp://*:%d" % (rcorelib.PORT_PUBSUB))

        self.running = False
        self.t = threading.Thread(target=self.run)

        self.nextId = 10   # first 10 reserved for MGT interface

    def start(self):
        '''start running master daemon'''
        self.running = True
        self.t.start()

    def isAlive(self):
        '''return true if master daemon is alive'''
        if self.t is not None:
            return self.t.isAlive()
        return False

    def stop(self):
        '''stop running thread'''
        self.running = False
        self.sock_mgt.close()
        self.sock_pub.close()
        self.t = None

    def run(self):
        '''Thread entrypoint'''
        try:
            while self.running:
                data = self.sock_mgt.recv()

                evt = revent.RCoreEvent \
                    .from_data(data,
                               lambda id: self.types_by_id[id])
                
                print 'RCVD EVENT %s' % (evt.eventType.name)

                res = None

                if evt.eventType.name == "register_event_type":
                    res = self.process_register_event_type(evt)
                elif evt.eventType.name == "read_event_type":
                    res = self.process_read_event_type(evt)
                else:
                    res = self.process_event(evt, data)

                self.sock_mgt.send(res.serialize())
        except:
            print 'Error in MGT Thread'
            traceback.print_exc()
            self.running = False

    def process_register_event_type(self, evt):
        '''process the registering of event type'''
        reader = evt.reader()
        name = reader.read()
        data_types = [i for i in reader.read()]  # turns bytearray into int arra

        event_type_id = None

        if self.event_type_exists(name, data_types):
            event_type = self.types_by_name[name]
            event_type_id = event_type.id
            print 'Registered existing event type %s [%d]' % (event_type.name, event_type.id)
        else:
            event_type_id = self.nextId
            self.nextId += 1

            event_type = revent.RCoreEventType(name, data_types, event_type_id)

            self.types_by_name[event_type.name] = event_type
            self.types_by_id[event_type.id] = event_type

            print 'Registered new event type %s [%d]' % (event_type.name, event_type.id)

        return revent.RCoreEventBuilder(
            revent.EVT_TYPE_MGT_REGISTER_EVENT_TYPE_RESP).add(event_type_id).build()

    def event_type_exists(self, name, data_types):
        return name in self.types_by_name and \
            self.event_data_types_match(self.types_by_name[name], data_types)

    def event_data_types_match(self, event_type, data_types):
        if len(event_type.dataTypes) == len(data_types):
            all_equal = True
            for i in range(len(data_types)):
                if event_type.dataTypes[i] != data_types[i]:
                    all_equal = False
            return all_equal
        return False

    def process_read_event_type(self, evt):
        reader = evt.reader()
        name = reader.read()

        if name in self.types_by_name:
            eventType = self.types_by_name[name]
            return revent.RCoreEventBuilder(
                revent.EVT_TYPE_MGT_READ_EVENT_TYPE_RESP) \
                .add(eventType.id) \
                .add(eventType.name) \
                .add(bytearray(eventType.dataTypes)) \
                .build()
        else:
            return revent.RCoreEventBuilder(
                revent.EVT_TYPE_MGT_READ_EVENT_TYPE_RESP) \
                .add(-1) \
                .add('NOT_FOUND') \
                .add(bytearray([])) \
                .build()

    def process_event(self, evt, data):
        # TODO: INSPECT EVENT, VERIFY NOT LOCKED, ETC

        self.sock_pub.send(data)

        return MGT_EVENT_RESP


class RCoreMain(object):
    def __init__(self):
        self.ctx = zmq.Context()

        self.master = RCoreMaster(self.ctx)

    def run(self):
        self.master.start()

        running = True
        while running:
            try:
                if self.master.isAlive():
                    time.sleep(1.0)
                else:
                    running = False
            except KeyboardInterrupt:
                print 'Interrupted'
                self.master.stop()
                self.ctx.term()
                time.sleep(1)


def main():
    rcoreMain = RCoreMain()
    rcoreMain.run()


if __name__ == "__main__":
    main()
