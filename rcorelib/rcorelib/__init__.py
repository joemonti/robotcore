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

class RCoreClientListener(object):

    def __init__(self, sockSub):
        self.listeners = {}
        self.sockSub = sockSub
        self.running = True
        self.t = threading.Thread(target=self.run)
        self.t.start()

    def run(self):
        while self.running:
            data = self.socketSub.recv()



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

    def register_listener(self, eventTypeName, callback):
