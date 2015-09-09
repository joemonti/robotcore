RobotCore
=============

A software framework for modular robotics. Performs two key functions:

1. Communication
2. Component Management

Communication
-------------

The communication system is event-based, where internal and external
components communciate through the RobotCore event router. The event router 
exposes internally and externally accessible endpoints, allowing all 
components to participate in open data exchange. 

Communication is managed by zero-mq, which provides a very low-overhead, high 
performance and cross language and platform system. A websocket and accompanying
javascript library can also be provided to facilitate web-based clients.

Data is byte-packed into [1-byte: type][n-bytes: data]. The event type
determines the format of the data.

The data format is up to the data type. However, it is intended to 
be used via helper methods for building and extracting elements
from the data. Builders and extractors work by maintaining an
index into the buffer, from which add/get[Type] methods are called
to add to or get the next piece of data. Type is the data type such as 
Int, Double, String, etc. Variable length data requires custom
parsing handlers. 


Component Management
-------------

Component management provides lifecycle management to components. This
includes loading components from external resources, executing 
initialization and teardown methods, providing access to the 
communication system, as well as a number of other utilities. 

The component management system is language-dependent, as such
each langauge requries its own component manager. Components
may opt to run as their own process, however the component management
system offers a much more robust and easy to use framework for
executing components. 


Command Overview
-------------

1. Register client
   1. client submits name/description (dependencies? authentication?)
   2. server returns client id (sent in all subsequent requests)
2. Register event type
    1. client requests new topic name
        1. topic can be exclusive (only owner can send)
    2. server sets up new topic with id
    3. server returns topic id
3. Get topic
   1. client asks by topic name
   2. server returns topic id if exists
4. Subscribe to topic
   1. client asks to subscribe to topic by name or id
   2. client is subscribed to topic
   3. server returns topic id if exists
   4. client listens to events from topic
5. Post to topic
   1. client posts topic id and data
   2. server verifies client is authorized (if exlusive, then client must be owner)
   3. server forwards to subscribers


Management Commands
-------------

Management commands allow clients to interact with the robot core master. 
Management commands are executed over the management interface (REQ/REP socket)
and data is transferred via JSON.

COMMAND: Register Event Type

Request:
    {
      "command": "register_event_type",
      "data" : {
        "name" : <string>,
        "dataTypes" : <array[int]>
      }
    }

Response:
    {
      "result" : "ack",
      "data" : {
        "id" : <short>
      }
    }

COMMAND: Read Event Type

Request:
    {
      "command" : "read_event_type",
      "data" : {
        "name" : <string>
      }
    }

Response: Found

    {
      "result" : "ack",
      "data" : {
        "id" : <short>,
        "name" : <string>,
        "dataTypes" : <array[int]>
      }
    }

Response: Not Found

    {
      "result" : "nack",
      "data" : {
        "errorKey" : "NOT_FOUND"
      }
    }

