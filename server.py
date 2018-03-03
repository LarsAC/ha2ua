import sys
sys.path.insert(0, "..")
import time
import asyncio
import asyncws
import json

from opcua import ua, Server
import homeassistant.remote as remote

@asyncio.coroutine
def echo(server, ha_ip, pwd, idx, loc_name):
    websocket = yield from asyncws.connect('ws://%s:8123/api/websocket?api_password=%s' % (ha_ip, pwd) )

    objects = server.get_objects_node()

    yield from websocket.send(json.dumps(
       {'id': 1, 'type': 'subscribe_events', 'event_type': 'state_changed'}))

    while True:
        message = yield from websocket.recv()
        if message is None:
            break
        msgobj = json.loads(message)

        if( msgobj['type'] == 'event' ):
            entity_id = msgobj['event']['data']['entity_id']
            new_state = msgobj['event']['data']['new_state']['state']
            old_state = msgobj['event']['data']['old_state']['state']

            if new_state != old_state:
                print( entity_id + ": " + old_state + " -> " + new_state )
                var_node = objects.get_child(["%d:%s" % (idx, loc_name), "%d:%s" % (idx, entity_id), "%d:state" % idx])
                var_node.set_value(new_state)

                # need to update attributes - e.g. lat/lon for device trackers

                # throw event ?

def setup_uaserver():
    server = Server()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/hass/server/")

    return server

def structure_init(server, ha_ip, pwd):

    api = remote.API(ha_ip, pwd)
    cfg = remote.get_config(api)
    # e.g. make version property

    print(cfg)

    uri = "http://hassopcua.lvonwedel.net"
    idx = server.register_namespace(uri)

    # create state type for HASS
    types = server.get_node(ua.ObjectIds.BaseObjectType)
    
    object_type_to_derive_from = server.get_root_node().get_child(["0:Types", 
                                                                   "0:ObjectTypes", 
                                                                   "0:BaseObjectType"])
    ha_state_type = types.add_object_type(idx, "HAStateType")
    ha_state_type.add_variable(idx, "state", 1.0)

    # create objects
    objects = server.get_objects_node()

    loc_name = cfg['location_name']
    loc_node = objects.add_folder(idx, loc_name)
    loc_node.add_property(idx, "location_name", loc_name)
    loc_node.add_property(idx, "elevation", cfg['elevation'])
    loc_node.add_property(idx, "latitiude", cfg['latitude'])
    loc_node.add_property(idx, "longitude", cfg['longitude'])
    loc_node.add_property(idx, "version", cfg['version'])
    
    entities = remote.get_states(api)
    for entity in entities:
        # create the node
        node = loc_node.add_object(idx, entity.entity_id, ha_state_type.nodeid)

        # set the value for the state child variable
        state = node.get_child('%d:state' % idx)
        state.set_value(entity.state)

        # node.set_attribute(ua.AttributeIds.DisplayName, entity.attributes['friendly_name'])

        for attr in entity.attributes.keys():
            if attr in ['latitude', 'longitude', 'unit_of_measurement', 'friendly_name']:
                node.add_property(idx, attr, entity.attributes[attr])

    return (idx, loc_name)

if __name__ == "__main__":

    server = setup_uaserver()
    server.start()

    ha_ip = sys.argv[1]
    pwd = sys.argv[2]
    ns_idx, loc_name = structure_init(server, ha_ip, pwd)

    try:
        asyncio.get_event_loop().run_until_complete(echo(server, ha_ip, pwd, ns_idx, loc_name))
    finally:
        asyncio.get_event_loop().close()
        server.stop()
