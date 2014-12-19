#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import zmq

import rcorelib
import rcorelib.event as revent


def main():

    ctx = zmq.Context()

    sockSub = ctx.socket(zmq.SUB)
    sockSub.bind("tcp://*:" % ( rcorelib.PORT_PUB )) #subscribe to client pub
    sockSub.setsockopt(zmq.SUBSCRIBE, b'')

    sockPub = ctx.socket(zmq.PUB)
    sockSub.bind("tcp://*:" % ( rcorelib.PORT_SUB )) #publish to client sub

    zmq.device(zmq.FORWARDER, sockSub, sockPub)


if __name__ == "__main__":
    main()