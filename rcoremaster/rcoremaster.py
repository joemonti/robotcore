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
import zmq
import signal
import threading
import traceback

import rcorelib
import rcorelib.event as revent


MGT_EVENT_RESP = revent.RCoreEventBuilder(revent.EVT_TYPE_MGT_EVENT_RESP) \
    .build()


class RCoreMaster(object):
    def __init__(self, ctx):
        self.clients = {}
        self.typesById = {}
        self.typesByName = {}

        for eventType in revent.EVT_TYPE_MGT_TYPES:
            self.typesByName[eventType.name] = eventType
            self.typesById[eventType.id] = eventType

        self.sockMgt = ctx.socket(zmq.REP)
        self.sockMgt.bind("tcp://*:%d" % (rcorelib.PORT_MGT))

        self.sockPub = ctx.socket(zmq.PUB)
        self.sockPub.bind("tcp://*:%d" % (rcorelib.PORT_PUBSUB))

        self.running = False
        self.t = threading.Thread(target=self.run)

        self.nextId = 10   # first 10 reserved for MGT interface

    def start(self):
        self.running = True
        self.t.start()

    def join(self):
        if self.running:
            self.t.join()

    def stop(self):
        self.running = False
        self.sockMgt.close()
        self.sockPub.close()

    def run(self):
        try:
            while self.running:
                data = self.sockMgt.recv()

                print 'MGT RCVD: %s' % (data)

                evt = revent.RCoreEvent \
                    .from_data(data,
                               lambda id: self.typesById[id])
                res = None
                if evt.eventType.name == "register_event_type":
                    res = self.process_register_event_type(evt)
                elif evt.eventType.name == "read_event_type":
                    res = self.process_read_event_type(evt)
                else:
                    res = self.process_event(evt, data)

                self.sockMgt.send(res.serialize())
        except:
            print 'Error in MGT Thread'
            traceback.print_exc()
            self.running = False

    def process_register_event_type(self, evt):
        id = self.nextId
        self.nextId += 1

        reader = evt.reader()
        name = reader.read()
        dataTypes = [i for i in reader.read()]  # turns bytearray into int arra
        eventType = revent.RCoreEventType(name, dataTypes, id)

        self.typesByName[eventType.name] = eventType
        self.typesById[eventType.id] = eventType

        print 'Registered event type %s [%d]' % (eventType.name, eventType.id)

        return revent.RCoreEventBuilder(
            revent.EVT_TYPE_MGT_REGISTER_EVENT_TYPE_RESP).add(id).build()

    def process_read_event_type(self, evt):
        reader = evt.reader()
        name = reader.read()

        if name in self.typesByName:
            eventType = self.typesByName[name]
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

        self.sockPub.send(data)

        return MGT_EVENT_RESP


class RCoreMain(object):
    def __init__(self):
        ctx = zmq.Context()

        self.master = RCoreMaster(ctx)

    def run(self):
        self.master.start()

        signal.signal(signal.SIGINT, self.shutdown)

        self.master.join()

    def shutdown(self):
        print 'Shutdown received'
        self.master.stop()


def main():
    rcoreMain = RCoreMain()
    rcoreMain.run()


if __name__ == "__main__":
    main()
