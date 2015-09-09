#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import zmq
import signal
import threading
import json

import rcorelib
import rcorelib.event as revent


class RCoreMaster(object):
    def __init__(self):
        self.clients = {}
        self.eventTypes = {}

class RCoreManagementIface(object):
    def __init__(self, master, ctx):
        self.master = master
        
        self.sock = ctx.socket(zmq.REP)
        self.sock.bind("tcp://*:%d" % ( rcorelib.PORT_MGT )) #subscribe to client pub
        
        self.running = False
        self.t = threading.Thread(target=self.run)

        self.nextId = 0
    
    def start(self):
        self.running = True
        self.t.start()
    
    def join(self):
        if self.running:
            self.t.join()
    
    def stop(self):
        self.running = False
        self.sock.close()
    
    def run(self):
        while self.running:
            data = self.sock.recv()

            print 'MGT RCVD: %s' % ( data )

            obj = json.loads(data)

            command = obj["command"]
            data = obj["data"]

            res = None
            if command == "register_event_type":
                res = self.process_register_event_type(data)
            elif command == "read_event_type":
                res = self.process_read_event_type(data)

            self.sock.send(json.dumps(res))


    def process_register_event_type(self, data):
        id = self.nextId
        self.nextId += 1

        eventType = revent.RCoreEventType(data["name"], data["dataTypes"], id)

        self.master.eventTypes[eventType.name] = eventType

        return { "result" : "ack", "data" : {  "id" : id } }

    def process_read_event_type(self, data):
        if data["name"] in self.master.eventTypes:
            eventType = self.master.eventTypes[data["name"]]
            return {
                "result" : "ack",
                "data" : {
                    "id" : eventType.id,
                    "name" : eventType.name,
                    "dataTypes" : eventType.dataTypes
                }
            }
        else:
            return { "result" : "nack", "data" : { "errorKey" : "NOT_FOUND" } }

class RCoreEventIface(object):
    def __init__(self, master, ctx):
        self.master = master
        
        self.sockSub = ctx.socket(zmq.SUB)
        self.sockSub.bind("tcp://*:%d" % ( rcorelib.PORT_PUB )) #subscribe to client pub
        self.sockSub.setsockopt(zmq.SUBSCRIBE, b'')

        self.sockPub = ctx.socket(zmq.PUB)
        self.sockPub.bind("tcp://*:%d" % ( rcorelib.PORT_SUB )) #publish to client sub
        
        self.running = False
        self.t = threading.Thread(target=self.run)
    
    def start(self):
        self.running = True
        self.t.start()
    
    def join(self):
        if self.running:
            self.t.join()
    
    def stop(self):
        self.running = False
        self.sockSub.close()
        self.sockPub.close()
    
    def run(self):
        #zmq.device(zmq.FORWARDER, sockSub, sockPub)
        # can't exactly forward b/c we have some validation/logic we need to perform
        # even though currently we just pass all through

        while self.running:
            data = self.sockSub.recv()
            
            # verify type
            # check if locked
            print 'EV RCVD: %s' % ( data )
            
            self.sockPub.send(data)


class RCoreMain(object):
    def __init__(self):
        ctx = zmq.Context()
        
        self.master = RCoreMaster()
        self.mgtIface = RCoreManagementIface(self.master, ctx)
        self.eventIface = RCoreEventIface(self.master, ctx)
        
    def run(self):
        self.mgtIface.start()
        self.eventIface.start()
        
        signal.signal(signal.SIGINT, self.shutdown)
        
        self.mgtIface.join()
        self.eventIface.join()
        
    def shutdown(self):
        print 'Shutdown received'
        self.mgtIface.stop()
        self.eventIface.stop()

def main():
    rcoreMain = RCoreMain()
    rcoreMain.run()


if __name__ == "__main__":
    main()
