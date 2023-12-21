import threading
from typing import Any
from chirpstack_api.as_pb.external import api
from google.protobuf.json_format import MessageToJson
import paho.mqtt.client as mqtt
import hashlib
import base64

import time

import models.iotc_api_helper as API_Helper


from models.device_model import *
from models.iotc_types import IOTCTypes
import chirpstack_api.gw, chirpstack_api.nc
from models.enums import Enums as E

def remove_chars(in_str,chars):
    return ''.join(c for c in in_str if c not in chars)


class LoraNode(GenericDevice):
    
    attributes_sent = False

    def __init__(self, unique_id, tag=None):
        super().__init__(unique_id, tag)
        self.attributes_sent = False

    def set_attributes(self, message):
        output = json.loads(message.payload.decode())
        if 'objectJSON' in output:
            obj_json = json.loads(output['objectJSON'])
            for m_key in obj_json:
                for m_index in obj_json[m_key]:

                    # # DEBUG, remove everything but one attribute
                    # if m_key != "digitalInput":
                    #     continue

                    # Defining custom attribute gpsLatLong
                    if m_key == "gpsLocation":
                        setattr(self, "gpsLatLong", IOTCTypes.to_lat_long(obj_json[m_key][m_index]['latitude'], obj_json[m_key][m_index]['longitude']))
                        if "gpsLatLong" not in self.attributes_to_send:
                            self.attributes_to_send.append("gpsLatLong")
                        continue # Comment out if want to include gpsLocation

                    setattr(self, m_key, obj_json[m_key][m_index])
                    if m_key not in self.attributes_to_send:
                        self.attributes_to_send.append(m_key)
            self.attributes_sent = False

    @classmethod
    def process_node_message(cls, node, topic, message):
        print(topic)            
        if topic[4] == "event":
            if topic[5] == 'up':
                node.set_attributes(message)
                return            

def dump(obj):
    for attr in dir(obj):
        if hasattr( obj, attr ):
            print( "obj.%s = %s" % (attr, getattr(obj, attr)))

class LoraConcentrator(LoraNode):

    channel = None
    auth_token = None
    
    def __init__(self, unique_id, channel, auth_token, tag=None):
        super().__init__(unique_id, tag)
        self.channel = channel
        self.auth_token = auth_token

    def get_state(self):
        client = api.GatewayServiceStub(self.channel)
        req = api.Gateway(id=self.unique_id)
        response = client.Get(req, metadata=self.auth_token)
        result = json.loads(MessageToJson(response))

        for key, value in {key : value for key, value in result.items() if key in self.get_attributes_to_send()}.items():
            setattr(self,key,value)

        for key, value in {key : value for key, value in result['gateway'].items() if key in self.get_attributes_to_send()}.items():
            setattr(self,key,value)

        self.attributes_sent = False
        return super().get_state()

    # def mqtt_set_attributes(self, message):
    #     response = LoraNetwork.unmarshal(message.payload, chirpstack_api.gw.GatewayStats())
    #     self.location = { "altitude" : response.location.altitude, "longitude" : response.location.longitude, "latitude": response.location.latitude }
    #     self.attributes_sent = False
    
    # @classmethod
    # def mqtt_process_concentrator_message(cls, concentrator, topic, message):
    #     if topic[2] == "state":
    #         if topic[3] == 'conn':
    #             response = LoraNetwork.unmarshal(message.payload, chirpstack_api.gw.ConnState())
    #             connected_status = True if response.ONLINE == 1 else False
    #             concentrator.connected = connected_status

    #             print(response)
    #             return

    #     if topic[2] == "event":
    #         if topic[3] == 'up':
    #             response = LoraNetwork.unmarshal(message.payload, chirpstack_api.gw.UplinkFrame())
    #             dump(response)
    #             print(response)
    #             return
            
    #         if topic[3] == 'ack':
    #             response = LoraNetwork.unmarshal(message.payload, chirpstack_api.gw.DownlinkTXAck())
    #             print(response)
    #             return
            
    #         if topic[3] == 'stats':
    #             concentrator.set_attributes(message)
    #             return
            
    #     if topic[2] == "command":
    #         if topic[3] == 'down':
    #             response = LoraNetwork.unmarshal(message.payload, chirpstack_api.gw.DownlinkFrame())
    #             print(response)
    #             return

    #     print(message.payload)
    #     pass

class LoraNetwork(Gateway):

    min_transmit = 30
    auth_token = None
    channel = None
    LIMIT = 100
    tag = "lora"
    created = None
    device_guid = ""
    template_guid = ""
    code = ""
    server = ""
    server_ip = ""
    server_port = ""
    mqtt_client = None
    concentrators = None
    application_id = None
    mqtt_topic = ""

    def __init__(self, company_id, unique_id, environment, sdk_options=None, sid=None):
        super().__init__(company_id, unique_id, environment, sdk_options, sid)
        self.created = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        self.application_id = ""
        self.mqtt_topic = ""

    def get_device_states(self):
        data_array = [self.get_d2c_data()]
        for c in self.children:
            if c.attributes_sent is False or isinstance(c,LoraConcentrator):
                data_array.append(c.get_d2c_data())
                c.attributes_sent = True
        return data_array

    def send_forever(self):
        device_count = len(self.children)
        m_time = time.time()
        while 1:
            if time.time() - m_time > self.min_transmit:
                m_time = time.time()

                if len(self.children) > 0:
                    if isinstance(self.children[0], LoraConcentrator):
                        self.init_concentrators()
                
                if len(self.children) != device_count:
                    self.connect()
                    device_count = len(self.children)

                print(f"sending data ... {self.name}")
                res = self.send_device_states()

    def mqtt_listener_thread_init(self):
        t = threading.Thread(target=self.mqtt_listener)
        t.setName(f"MQTT Listener of {self.name}")
        t.daemon = True  # thread dies when main thread exits.
        t.start()
        
    def mqtt_listener(self):

        self.mqtt_client = mqtt.Client()
        self.mqtt_client.message_callback_add(f"application/{self.application_id}/device/+/event/up", self.mqtt_on_device_up)
        self.mqtt_client.connect(self.server_ip, 1883, keepalive=500)
        self.mqtt_client.subscribe(f"application/{self.application_id}/device/+/event/up")
        self.mqtt_client.loop_forever()

    @classmethod
    def unmarshal(cls,message, pl):
        pl.ParseFromString(message)
        return pl
    
    def mqtt_on_device_up(self,client, userdata, message):
        topic:str = message.topic
        print(topic)
        topic = topic.split('/')
        
        application_id = topic[1]
        unique_id = topic[3]

        node: LoraNode = next((c for c in self.children if c.unique_id == unique_id), None)
        if node is None:
            output = json.loads(message.payload.decode())
            tag = f"{output['deviceName'][:3]}{unique_id[-4:]}{output['applicationName']}"[:10].lower()
            tag = f"{output['deviceProfileName']}"[:10].lower()
            node = LoraNode(unique_id, tag)
            node.name = output['deviceName']
            node.set_attributes(message)

            if self.SdkClient is not None:
                self.add_child(node)
                API_Helper.create_child_on_iotc(self,node)
                # self.SdkClient.createChildDevice(node.unique_id, node.tag, node.name)

        LoraNode.process_node_message(node,topic,message)
        return
    
    def get_children_attributes_by_name(self, attribute_name):
        attributes = []
        for c in self.children:
            if hasattr(c, attribute_name):
                attributes.append(getattr(c,attribute_name))
        
        return attributes

    def device_cb(self,msg):
        command: list = E.get_value(msg, E.Keys.device_command).split(' ')
        from_id = E.get_value(msg, E.Keys.id)

        success = False

        node: LoraNode = next((c for c in self.children if c.unique_id == from_id), None)
        if node is not None:
            if command[0] == "set_nucleo_led":
        
                    pub_topic = f"application/{self.application_id}/device/{node.unique_id}/command/down"

                    value = command[1] == 'True'

                    packet = {
                    "fPort" : 2,
                    "confirmed": True,
                    "data" : base64.b64encode(bytes([int(value)])).decode("utf-8")
                    }
                    packet = json.dumps(packet)

                    self.mqtt_client.publish(pub_topic, packet, 0, False)
                    success = True

        ack = E.Values.AckStat.SUCCESS if success else E.Values.AckStat.FAIL
        self.send_ack(msg,ack, "Whatever")

    # def populate(self):

    #     # Get all service profiles
    #     client = api.ServiceProfileServiceStub(self.channel)
    #     req = api.ListServiceProfileRequest()
    #     req.limit = self.LIMIT
    #     response = client.List(req, metadata=self.auth_token)
    #     raw_json = MessageToJson(response)
    #     json_obj = json.loads(raw_json)
    #     service_profiles = json_obj["result"]

    #     # Get all applications
    #     client = api.ApplicationServiceStub(self.channel)
    #     req = api.ListApplicationRequest()
    #     req.limit = self.LIMIT
    #     response = client.List(req, metadata=self.auth_token)
    #     raw_json = MessageToJson(response)
    #     json_obj = json.loads(raw_json)
    #     applications = json_obj["result"]

    #     # Get all network servers
    #     client = api.NetworkServerServiceStub(self.channel)
    #     req = api.ListNetworkServerRequest()
    #     req.limit = 1
    #     response = client.List(req, metadata=self.auth_token)
    #     raw_json = MessageToJson(response)
    #     json_obj = json.loads(raw_json)
    #     network_servers = json_obj["result"]

    #     # # get gateway unique id from grpc channel
    #     client = api.GatewayServiceStub(self.channel)
    #     req = api.ListGatewayRequest()
    #     req.limit = 1
    #     response = json.loads(MessageToJson(client.List(req, metadata=self.auth_token)))
    #     gateways = response

    #     # need to rewrite to use network server details
    #     self.unique_id = str(hashlib.sha256(network_servers[0]['name'].encode()).hexdigest())[:10]
    #     self.name = f"{remove_chars(network_servers[0]['name'], ' -_')}{self.unique_id[:3]}"
    #     self.code = f"{self.name}{self.unique_id[:3]}"[:10]
    #     self.tag = f"{self.name}{self.unique_id[:3]}"[:10]

    #     # self.attributes = {key : value for key, value in response['result'][0].items() if key in self.gateway_attribute_filter}
    #     # for key, value in response['result'][0].items():
    #     #     if key in self.chirpstack_attributes_wanted:
    #     #         setattr(self, key, value)
    #     #         self.attributes_to_send.append(key)


    #     # get all devices that are in all service profiles
    #     devices = []
    #     for app in applications:
    #         client = api.DeviceServiceStub(self.channel)
    #         req = api.ListDeviceRequest()
    #         req.limit = self.LIMIT
    #         req.service_profile_id = app["serviceProfileID"]
    #         response = json.loads(MessageToJson(client.List(req, metadata=self.auth_token)))
    #         for res in response["result"]:
    #             devices.append(res)

    def init_network_server(self):
        client = api.NetworkServerServiceStub(self.channel)
        req = api.ListNetworkServerRequest()
        req.limit = 1
        response = client.List(req, metadata=self.auth_token)
        raw_json = MessageToJson(response)
        json_obj = json.loads(raw_json)
        network_servers = json_obj["result"]

        # need to rewrite to use network server details
        self.unique_id = str(hashlib.sha256(network_servers[0]['name'].encode()).hexdigest())[:10]
        self.name = f"{remove_chars(network_servers[0]['name'], ' -_')}{self.unique_id[:3]}"
        self.code = f"{self.name}{self.unique_id[:3]}"[:10]
        self.tag = f"{self.name}{self.unique_id[:3]}"[:10]


    def init_concentrators(self):

        chirpstack_gateway_attributes = ['createdAt', 'updatedAt', 'firstSeenAt', 'lastSeenAt', 'location']
        # # get gateway unique id from grpc channel
        client = api.GatewayServiceStub(self.channel)
        req = api.ListGatewayRequest()
        req.limit = self.LIMIT
        response = json.loads(MessageToJson(client.List(req, metadata=self.auth_token)))

        for c in [r for r in response['result'] if r['id'] not in self.get_children_attributes_by_name('unique_id')]:
            concentrator = LoraConcentrator(c['id'], channel=self.channel, auth_token=self.auth_token)
            concentrator.name = c['name']
            concentrator.tag = f"{c['name'][:3]}{c['id'][-4:]}{c['networkServerName']}"[:10].lower()

            for key, value in {key : value for key, value in c.items() if key in chirpstack_gateway_attributes}.items():
                setattr(concentrator, key, value)
                concentrator.attributes_to_send.append(key)
            
            self.children.append(concentrator)
            API_Helper.create_child_on_iotc(self,concentrator)
            self.SdkClient.createChildDevice(concentrator.unique_id, concentrator.tag, concentrator.name)