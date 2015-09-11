# -*- coding: utf-8 -*-

import zmq
import threading
import event
import struct
import json

PORT_MGT = 12210
PORT_PUB = 12211
PORT_SUB = 12212


class RCoreClient(object):
    '''RobotCore Client'''
    def __init__(self, server, name):
        self.ctx = zmq.Context()

        self.sockMgt = self.ctx.socket(zmq.REQ)
        self.sockMgt.connect("tcp://%s:%d" % (server, PORT_MGT))

        self.sockPub = self.ctx.socket(zmq.PUB)
        self.sockPub.connect("tcp://%s:%d" % (server, PORT_PUB))

        self.sockSub = self.ctx.socket(zmq.SUB)
        self.sockSub.connect("tcp://%s:%d" % (server, PORT_SUB))

        self.self = None
        self.typesByName = {}
        self.typesById = {}
        self.listeners = {}

    def get_event_types(self):
        pass  # list event types via management interface

    def read_event_type(self, name):
        if name in self.typesByName:
            return self.typesByName[name]
        else:
            data = {"name": name}
            resp = self.call_mgt_command("read_event_type", data)
            if resp["result"] == "ack":
                respData = resp["data"]
                eventType = event.RCoreEventType(respData["name"],
                                                 respData["dataTypes"],
                                                 respData["id"])
                self.typesByName[name] = eventType
                self.typesById[eventType.id] = eventType
                return eventType
            else:
                return None

    def register_event_type(self, eventType):
        data = {
            "name": eventType.name,
            "dataTypes": eventType.dataTypes
        }

        resp = self.call_mgt_command("register_event_type", data)
        if resp["result"] == "ack":
            respData = resp["data"]
            eventType.id = respData["id"]
            self.typesByName[eventType.name] = eventType
            self.typesById[eventType.id] = eventType
            return eventType
        else:
            raise Exception("Error registering event type %s" %
                            (eventType.name))

    def call_mgt_command(self, command, data):
        self.sockMgt.send(json.dumps({"command": command, "data": data}))
        resp = self.sockMgt.recv()
        return json.loads(resp)

    def send(self, evt):
        data = evt.serialize()
        self.sockPub.send(data)

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
        self.sockPub.close()
        self.sockSub.close()

    def run_listeners(self):
        print 'Started Listener'
        while self.running:
            data = self.sockSub.recv()

            print 'Received: %s' % (data)

            evt = event.RCoreEvent.from_data(data,
                                             lambda id: self.typesById[id])

            if evt.eventType.name in self.listeners:
                for listener in self.listeners[evt.eventType.name]:
                    listener(evt)


def demo():
    def my_receiver(t, d):
        print 'GOT [type:%s] [data:%s]' % (t, d)

    c = RCoreClient('localhost', 'me')
    c.register_listener('foo', my_receiver)
    c.start()

    return c
