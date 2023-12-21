import time
import sys
from grpc import insecure_channel

from models.lora_device_model import *
import models.iotc_api_helper as API_Helper



# Configuration.
# This must point to the API interface. overridden by sys.argv[1]
server_ip = "10.103.1.150"
server_port = "8080"
server = f"{server_ip}:{server_port}"
# API key ID b69e55e2-92fc-45a5-a5e5-dc0e5b21f4d2
api_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcGlfa2V5X2lkIjoiYjQ3NWYzYjYtYzcyYy00YmYyLTkyY2YtOTAzODg5MWVhMzRlIiwiYXVkIjoiYXMiLCJpc3MiOiJhcyIsIm5iZiI6MTcwMDczMjYwMiwic3ViIjoiYXBpX2tleSJ9.7tskIsmhx5v_HeZ5jaQwYg_5UlKnvRYlMzGw308a5Hw'

# Iotconnect setup
cpid = 'avtds'
env = 'avnetpoc'
sid = 'Yjg5MmMzNThlMzc1NGNjMzg4NDEzMmUyNzFlMjYxNTE=UDI6MDM6NzAuMTQ='

# if len(sys.argv) > 1:
#     server = '{}:8080'.format(sys.argv[1])
print("Connecting to", server)

# Connect without using TLS.
channel = insecure_channel(server)

# instantiate gateway
gw = LoraNetwork(cpid, "", env, sid=sid)
gw.server_ip = server_ip
gw.server_port = server_port
gw.server = server
gw.min_transmit = 30
gw.channel = channel
gw.auth_token = [("authorization", "Bearer %s" % api_token)]

m_time = time.time()

gw.populate()
device_count = len(gw.children)
API_Helper.delete_device_and_template(gw.name)
API_Helper.create_template_and_gateway_device_on_iotc(gw)

gw.mqtt_listener_thread_init()
gw.connect()
# print(json.dumps(gw.for_iotconnect_children_upload(), indent=2))



while 1:
    # try:
    if time.time() - m_time > gw.min_transmit:
        
        if len(gw.children) != device_count:
            gw.connect()
            device_count = len(gw.children)

        print("sending data ...")
        res = gw.send_device_states()
        m_time = time.time()

