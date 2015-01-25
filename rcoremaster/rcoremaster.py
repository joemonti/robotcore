#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import zmq
import signal
import threading

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
        self.sock.close()
    
    def run(self):
        pass

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
        
        while self.running:
            data = self.sockSub.recv()
            
            # verify type
            # check if locked
            
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
