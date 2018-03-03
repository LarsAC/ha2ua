# README for HA2UA - HAss - UPC UA Bridge

This is a very basic attempt to provide access to Home Assistant (http://www.home-assistant.io) via an OPC UA interface. The current status is more of a feasibility test based on OPC UA bindings for Python (https://github.com/FreeOpcUa/python-opcua). Current functionality is rather limited, HA entity nodes are represented as a flat list of OPC UA nodes (with a state variable as a child). HA events are caught and value changes are propagated to the corresponding OPC UA nodes.

Run with 
```
  python server.py <ip-of-ha-server> <api-password-of-ha>
```

Not for production use !

## ToDo

* catch write access on nodes to change state variable in HA
* broadcast events on HASS events ?
* use Methods to call services (e.g. methods on/off for light nodes)
* Authentication
* Certificates

## Ideas

* none

## Done

* Read HAss structure and setup corresponding nodes
* use websockets event loop to update state of UA nodes
* HASS state attributes mapped to AU property child nodes
