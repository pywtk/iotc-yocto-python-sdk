import time
import sys
from grpc import insecure_channel

from models.lora_device_model import *

# Configuration.
# The API token (retrieved using the web-interface).
# # Org API key ID 73ca0ab0-f664-4178-a68d-4e65231e96fa
# api_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcGlfa2V5X2lkIjoiNzNjYTBhYjAtZjY2NC00MTc4LWE2OGQtNGU2NTIzMWU5NmZhIiwiYXVkIjoiYXMiLCJpc3MiOiJhcyIsIm5iZiI6MTcwMDAzOTkwNiwic3ViIjoiYXBpX2tleSJ9.O4Ec0ImAFKf_FFZtKMqou-La_h4D6jaBGCCkLZ2La9g"

# This must point to the API interface. overridden by sys.argv[1]
server = "localhost:8080"
# API key ID b69e55e2-92fc-45a5-a5e5-dc0e5b21f4d2
api_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcGlfa2V5X2lkIjoiYjY5ZTU1ZTItOTJmYy00NWE1LWE1ZTUtZGMwZTViMjFmNGQyIiwiYXVkIjoiYXMiLCJpc3MiOiJhcyIsIm5iZiI6MTcwMDEzNzI5OSwic3ViIjoiYXBpX2tleSJ9.lJ8aVFIaRylm0HCdjmLUZ-rdExxFCWJpMAWZtUklrPc'

# Iotconnect setup
cpid = 'avtds'
env = 'avnetpoc'
sid = 'Yjg5MmMzNThlMzc1NGNjMzg4NDEzMmUyNzFlMjYxNTE=UDI6MDM6NzAuMTQ='

if len(sys.argv) > 1:
    server = '{}:8080'.format(sys.argv[1])
print("Connecting to", server)

# Connect without using TLS.
channel = insecure_channel(server)

# instantiate gateway
#  company_id, unique_id, environment, sdk_options=None):
gw = LoraNetwork(cpid, "stmp32mp1-networkserver1", env, sid=sid)
gw.min_transmit = 30
gw.channel = channel
gw.auth_token = [("authorization", "Bearer %s" % api_token)]
gw.populate()

gw.connect()
print('\n\ngw.for_iotconnect_upload()')
print(json.dumps(gw.for_iotconnect_children_upload(), indent=2))

print('\n\ngw.template_output():')
print(json.dumps(gw.template_output('IOTC_CODE', 'IOTC_NAME', gw.AUTH_TYPE_TOKEN), indent=2))

# print(gw.show_children())

m_device = GenericDevice("fzdfsdfsfs")
print(m_device.for_iotconnect_upload())
