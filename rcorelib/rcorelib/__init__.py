# -*- coding: utf-8 -*-

import zmq
import threading

PORT_MGT=12210
PORT_PUB=12211
PORT_SUB=12212

MGT_CMD_REGISTER_SELF        = 0
MGT_CMD_REGISTER_EVENT_TYPE  = 1
MGT_CMD_REQUEST_EVENT_TYPE   = 2
MGT_CMD_LOCK_EVENT_TYPE      = 3
MGT_CMD_UNLOCK_EVENT_TYPE    = 4


class RCoreClient(object):
    '''RobotCore Client'''
    def __init__(self, server, name):
        self.ctx = zmq.Context()

        self.sockMgt = self.ctx.socket(zmq.REQ)
        self.sockMgt.connect("tcp://%s:%d" % ( server, PORT_MGT ))

        self.sockPub = self.ctx.socket(zmq.PUB)
        self.sockPub.connect("tcp://%s:%d" % ( server, PORT_PUB ))

        self.sockSub = self.ctx.socket(zmq.SUB)
        self.sockSub.connect("tcp://%s:%d" % ( server, PORT_SUB ))

        self.self = None
        self.types = {}
        self.listeners = {}
    
    def get_event_types(self):
        pass # list event types via management interface
    
    def get_event_type(self, name):
        pass # read event type via management interface

    def register_event_type(self, eventType):
        pass # register event type via management interface
    
    def send(self, event):
        data = event.serialize()
        self.sockPub.send(data)

    def register_listener(self, eventTypeName, callback):
        eventListeners = None
        if eventTypeName in self.listeners:
            eventListeners = self.listeners[eventTypeName]
        else:
            eventListeners = []
            self.listeners[eventTypeName] = eventListeners
            self.sockSub.setsockopt(zmq.SUBSCRIBE, '%s' % ( eventTypeName ))
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
            print 'Received: %s' % ( data )
            firstSpace = data.find(' ')
            eventTypeName = data[0:firstSpace]
            eventData = data[firstSpace+1:]
            if eventTypeName in self.listeners:
                for listener in self.listeners[eventTypeName]:
                    listener(eventTypeName, eventData)


def demo():
    def my_receiver(t, d):
        print 'GOT [type:%s] [data:%s]' % ( t, d )
    
    c = RCoreClient('localhost', 'me')
    c.register_listener('foo', my_receiver)
    c.start()
    return c

