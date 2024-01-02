#!/usr/bin/env python3

import time
import sys
from grpc import insecure_channel

from models.lora_device_model import *
import models.iotc_api_helper as API_Helper
import hashlib
import threading


# Configuration.
# This must point to the API interface. overridden by sys.argv[1]
server_ip = "localhost"
server_port = "8080"
server = f"{server_ip}:{server_port}"
# API key ID b69e55e2-92fc-45a5-a5e5-dc0e5b21f4d2
api_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcGlfa2V5X2lkIjoiYjQ3NWYzYjYtYzcyYy00YmYyLTkyY2YtOTAzODg5MWVhMzRlIiwiYXVkIjoiYXMiLCJpc3MiOiJhcyIsIm5iZiI6MTcwMDczMjYwMiwic3ViIjoiYXBpX2tleSJ9.7tskIsmhx5v_HeZ5jaQwYg_5UlKnvRYlMzGw308a5Hw'
auth_token = [("authorization", "Bearer %s" % api_token)]

# Iotconnect setup
cpid = 'avtds'
env = 'avnetpoc'
sid = 'Yjg5MmMzNThlMzc1NGNjMzg4NDEzMmUyNzFlMjYxNTE=UDI6MDM6NzAuMTQ='

min_transmit = 30

# if len(sys.argv) > 1:
#     server = '{}:8080'.format(sys.argv[1])
print("Connecting to", server)

# Connect without using TLS.
channel = insecure_channel(server)

def init_network_server():
    ns = LoraNetwork(cpid, "", env, sid=sid)
    ns.server_ip = server_ip
    ns.server_port = server_port
    ns.server = server
    ns.min_transmit = min_transmit
    ns.channel = channel
    ns.auth_token = auth_token


    ns.init_network_server()
    API_Helper.delete_device_and_template(ns.name)
    API_Helper.create_template_and_gateway_device_on_iotc(ns)

    ns.connect()
    ns.init_concentrators()

    ns.send_forever()


def init_app_thread(app: LoraNetwork):
    API_Helper.delete_device_and_template(app.name)
    API_Helper.create_template_and_gateway_device_on_iotc(app)

    app.mqtt_listener_thread_init()
    app.connect()
    app.send_forever()

def main():
    threads = []

    # ns_thread = threading.Thread(target=init_network_server)
    # ns_thread.setName("Network Server")
    # threads.append(ns_thread)
    # ns_thread.start()

    applications = []

    # Check for applications on chirpstack, and create our analogues and threads
    m_time = time.time()
    while 1:
        if time.time() - m_time > min_transmit:
            m_time = time.time()

            client = api.ApplicationServiceStub(channel)
            req = api.ListApplicationRequest()
            req.limit = 100
            response = client.List(req, metadata=auth_token)
            raw_json = MessageToJson(response)
            json_obj = json.loads(raw_json)

            existing_applications = []
            for a in applications:
                if hasattr(a, 'name'):
                    existing_applications.append(getattr(a,'name'))

            for a in json_obj["result"]:
                if a['name'] not in existing_applications:
                    app = LoraNetwork(cpid, "", env, sid=sid)
                    app.server_ip = server_ip
                    app.server_port = server_port
                    app.server = server
                    app.min_transmit = min_transmit
                    app.channel = channel
                    app.auth_token = auth_token

                    app.name = a['name']
                    app.unique_id = str(hashlib.sha256(f"{a['name']}{a['id'][-4:]}".encode()).hexdigest())[:10]
                    app.application_id = a['id']
                    app.tag = f"{a['name'][:3]}{a['id'][-4:]}{a['serviceProfileName']}"[:10].lower()
                    # app.tag = f"{a['serviceProfileName']}"[:10].lower()
                    app.code = f"{a['name']}{a['id'][-4:]}"[:10]

                    applications.append(app)
                    app_thread = threading.Thread(target=init_app_thread, args=[app])
                    app_thread.setName(f"App Thread {app.name}")
                    threads.append(app_thread)
                    app_thread.start()

if __name__ == "__main__":
    main()