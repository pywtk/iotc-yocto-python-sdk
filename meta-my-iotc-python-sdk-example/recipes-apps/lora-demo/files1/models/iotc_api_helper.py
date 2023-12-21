import requests
import json
import datetime

from models.iotc_types import IOTCTypes

timeout = 10

api_user_url = "https://avnetuser.iotconnect.io"
api_auth_url = "https://avnetauth.iotconnect.io"
api_device_url ="https://avnetdevice.iotconnect.io"

solution_key = "RjQ5QkE1M0EtNThFRC00RDRBLThBMTQtOEZDRTlDQUFDMEEyLWFjY2Vzc0tFWS1jaTJ2djdxNmFj"
company_guid = "b892c358-e375-4cc3-8841-32e271e26151"

company_name = "Witekio"



def get_template_guid(access_token,template_name):
    header = {
        "Authorization": f"Bearer {access_token}",
        "Content-type": "application/json",
    }
    response = requests.get(f"{api_device_url}/api/v2/device-template{'?DeviceTemplateName='}{template_name}", headers=header, timeout=timeout)
    response = json.loads(response.text)
    for data in response["data"]:
        return data["guid"]     
    

def get_device_guid(access_token,device_name):
    header = {
        "Authorization": f"Bearer {access_token}",
        "Content-type": "application/json",
    }
    response = requests.get(f"{api_device_url}/api/v2/Device?Name={device_name}", headers=header, timeout=timeout)
    response = json.loads(response.text)
    for data in response["data"]:
        return data["guid"]     
    
def get_entity_guid(access_token,company_name):
    header = {
        "Authorization": f"Bearer {access_token}",
        "Content-type": "application/json",
    }
    response = requests.get(f"{api_user_url}/api/v2/Entity", headers=header, timeout=timeout)
    response = json.loads(response.text)
    ret = ""
    for data in response["data"]:
        if data["name"] == company_name:
            ret = data["guid"]
            break
    return ret

def get_data_types(access_token):
    # useless, does not provide all of the attributes
    header = {
        "Authorization": f"Bearer {access_token}",
        "Content-type": "application/json",
    }
    response = requests.get("https://avnetmaster.iotconnect.io/api/v2/Property/custom-field-type", headers=header, timeout=timeout)
    response = json.loads(response.text)
    print(response)


def create_gateway_template(access_token, template_code, auth_type, tag, template_name):
    header = {
        "Authorization": f"Bearer {access_token}",
        "Content-type": "application/json",
    }
    template_create_request = {
        "code": template_code,
        "isEdgeSupport": "false",
        "authType": auth_type,
        "tag": tag,
        # "dataLength": 0,
        # "isIotEdgeEnable": "true",
        "messageVersion": "2.1",
        # "isSphere": "true",
        # "trustedPartnerGuid": "string",
        "name": template_name,
        # "firmwareguid": "string"
        }

    response = requests.post(f"{'https://avnetdevice.iotconnect.io'}/api/v2/device-template", timeout=timeout, headers=header, json=template_create_request)
    response = json.loads(response.text)
    print(response)
    # for data in response["data"]:
    #     return data["guid"]    

    
def delete_device(access_token, device_guid):
    header = {
        "Authorization": f"Bearer {access_token}",
        "Content-type": "application/json",
    }

    response = requests.delete(f"{'https://avnetdevice.iotconnect.io'}/api/v2/Device/{device_guid}", timeout=timeout, headers=header)
    response = json.loads(response.text)
    print(response)

def delete_template(access_token, template_guid):
    header = {
        "Authorization": f"Bearer {access_token}",
        "Content-type": "application/json",
    }

    response = requests.delete(f"{'https://avnetdevice.iotconnect.io'}/api/v2/device-template/{template_guid}", timeout=timeout, headers=header)
    response = json.loads(response.text)
    print(response)


def add_template_object_attribute(access_token, template_guid, attribute_name, child_attributes, attribute_tag):
    
    children = []

    sequence = 0
    for child_key, child_value in child_attributes.items():
        AttributeBaseObject = {
            'localName' : child_key,
            # 'description' : "",
            # 'dataValidation' : '',
            "dataTypeGuid": IOTCTypes.to_guid(child_value),
            "sequence": sequence,
            # "unit": "string",
            # "startIndex": 0,
            # "numChar": 0,
            # "attributeColor": "string"
        }
        sequence += 1
        children.append(AttributeBaseObject)

    
    header = {
        "Authorization": f"Bearer {access_token}",
        "Content-type": "application/json",
    }
    attribute_create_request = {
        "localName": attribute_name,
        # "description": "string",
        "deviceTemplateGuid": template_guid,
        "dataTypeGuid": IOTCTypes.guids["OBJECT"],
        # "dataValidation": "string",
        # "unit": "string",
        "tag": attribute_tag,
        # "aggregateType": [
        #     "string"
        # ],
        # "tumblingatewayindow": "string",
        "attributes": children,
        # "xmlAttributes": {},
        # "startIndex": 0,
        # "numChar": 0,
        # "attributeColor": "string"
    }

    response = requests.post(f"{api_device_url}/api/v2/template-attribute", timeout=timeout, headers=header, json=attribute_create_request)
    response = json.loads(response.text)
    # for data in response["data"]:
    #     return data["newid"]    
    print(response)

def add_template_attribute(access_token, template_guid, attribute_name, attribute_type_guid, attribute_tag):
    header = {
        "Authorization": f"Bearer {access_token}",
        "Content-type": "application/json",
    }
    attribute_create_request = {
        "localName": attribute_name,
        # "description": "string",
        "deviceTemplateGuid": template_guid,
        "dataTypeGuid": attribute_type_guid,
        # "dataValidation": "string",
        # "unit": "string",
        "tag": attribute_tag,
        # "aggregateType": [
        #     "string"
        # ],
        # "tumblingatewayindow": "string",
        # "attributes": [
        #     {
        #     "localName": "string",
        #     "description": "string",
        #     "dataValidation": "string",
        #     "dataTypeGuid": "string",
        #     "sequence": 0,
        #     "unit": "string",
        #     "startIndex": 0,
        #     "numChar": 0,
        #     "attributeColor": "string"
        #     }
        # ],
        # "xmlAttributes": {},
        # "startIndex": 0,
        # "numChar": 0,
        # "attributeColor": "string"
    }

    response = requests.post(f"{api_device_url}/api/v2/template-attribute", timeout=timeout, headers=header, json=attribute_create_request)
    response = json.loads(response.text)
    # for data in response["data"]:
    #     return data["newid"]    
    print(response)

def get_access_token():
    service_account = requests.get(f"{api_user_url}/api/v2/company/{company_guid}/service-account", timeout=timeout)
    service_account = json.loads(service_account.text)

    username = service_account["data"]["username"]
    password = service_account["data"]["password"]

    basic_token = requests.get(f"{api_auth_url}/api/v2/Auth/basic-token", timeout=timeout)
    if basic_token.status_code != 200:
        print("error")
        exit(-1)

    basic_token = json.loads(basic_token.text)
    basic_token = basic_token['data']

    header = {
        "Authorization": f"Basic {basic_token}",
        "solution-key": solution_key,
        "Content-type": "application/json",
    }

    body = {
        "username" : username,
        "password" : password
    }
    access_token = requests.post(f"{api_auth_url}/api/v2/Auth/login", timeout=timeout, headers=header, json=body)
    access_token = json.loads(access_token.text)
    return access_token["access_token"]


def create_device(access_token, unique_id, template_guid, tag, name, entity_guid, parent_device_id=None):
    header = {
        "Authorization": f"Bearer {access_token}",
        "Content-type": "application/json",
    }
    request = {
        "uniqueId": unique_id,
        # "firmwareUpgradeGuid": "string",
        "deviceTemplateGuid": template_guid,
        "tag": tag,
        "parentDeviceGuid" : parent_device_id,
        # "primaryThumbprint": "string",
        # "secondaryThumbprint": "string",
        # "endorsementKey": "string",
        # "properties": [
        #     {
        #     "guid": "string",
        #     "value": "string"
        #     }
        # ],
        # "xmlProperties": {},
        # "deviceCertificateGuid": "string",
        # "deviceCertificate": "string",
        # "deviceCertificatePassword": "string",
        # "primaryKey": "string",
        # "secondaryKey": "string",
        # "certificateText": "string",
        "displayName": name,
        # "note": "string",
        "entityGuid": entity_guid
        }
        
    response = requests.post(f"{'https://avnetdevice.iotconnect.io'}/api/v2/Device", timeout=timeout, headers=header, json=request)
    response = json.loads(response.text)
    print(response)



def remove_chars(in_str,chars):
    return ''.join(c for c in in_str if c not in chars)

def create_template_and_gateway_device_on_iotc(network_server):
    access_token = get_access_token()

    # Create template
    create_gateway_template(access_token, network_server.code, 1, network_server.tag, network_server.name)
    template_guid = get_template_guid(access_token, network_server.name)
    network_server.template_guid = template_guid

    # # Add gateways's attributes
    # for attribute,value in network_server.get_state().items():
    #     if isinstance(value,dict):
    #         add_template_object_attribute(access_token, template_guid, attribute, value, network_server.tag)
    #         continue
    #     add_template_attribute(access_token, template_guid, attribute, IOTCTypes.to_guid(value), network_server.tag)

    # Need at least one attribute to create devices etc
    add_template_attribute(access_token, template_guid, "dummy", IOTCTypes.to_guid("dummy"), network_server.tag)


    entity_guid = get_entity_guid(access_token, company_name)
    # Create Actual instance of gateway
    create_device(access_token,network_server.unique_id, template_guid, network_server.tag, network_server.name, entity_guid)
    network_server.device_guid = get_device_guid(access_token, network_server.name)


def create_child_on_iotc(gateway, child_obj):
    access_token = get_access_token()

    for attribute,value in child_obj.get_state().items():
        if isinstance(value,dict):
            add_template_object_attribute(access_token, gateway.template_guid, attribute, value, child_obj.tag)
            continue
        add_template_attribute(access_token, gateway.template_guid, attribute, IOTCTypes.to_guid(value), child_obj.tag)

    entity_guid = get_entity_guid(access_token, company_name)
    parent_device_guid = get_device_guid(access_token, gateway.name)

    create_device(access_token, child_obj.unique_id, gateway.template_guid, child_obj.tag, child_obj.name, entity_guid, parent_device_guid)

def delete_device_and_template(device_name):
    access_token = get_access_token()

    try:
        device_guid = get_device_guid(access_token,device_name)
        delete_device(access_token,device_guid)
    except:
        pass

    try:
        template_name = device_name
        template_guid = get_template_guid(access_token, template_name)
        delete_template(access_token, template_guid)
    except:
        pass

