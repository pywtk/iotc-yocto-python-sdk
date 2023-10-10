from model.DeviceModel import ConnectedDevice

from model.JsonParser import parse_json_for_config, ToSDK
import struct

from model.Enums import Enums as E

class DynAttr:

    name = None
    path = None
    read_type = None

    def __init__(self, name, path,read_type):
        self.name = name
        self.path = path
        self.read_type = read_type

    def update_value(self):
        val = None
        try:
            if self.read_type == E.ReadTypes.ascii:
                with open(self.path, "r", encoding="utf-8") as f:
                    val = f.read()

            if self.read_type == E.ReadTypes.binary:
                with open(self.path, "rb") as f:
                    val = f.read()

        except FileNotFoundError:
            print("File not found at", self.path)
        return val

    def get_value(self,to_type):
        val = self.update_value()
        val = self.convert(val,to_type)
        return val
    
    def convert(self,val,to_type):
        if self.read_type == E.ReadTypes.binary:
            if to_type in [E.SendDataTypes.INT, E.SendDataTypes.LONG]:
                return int.from_bytes(val, 'big')
            
            elif to_type in [E.SendDataTypes.FLOAT]:
                return (struct.unpack('f', val)[0])
            
            elif to_type in [E.SendDataTypes.STRING]:
                return val.decode("utf-8")
            
            elif to_type in [E.SendDataTypes.Boolean]:
                return struct.unpack('?', val)[0]
            
            elif to_type in [E.SendDataTypes.BIT]:
                if struct.unpack('?', val)[0]:
                    return 1
                return 0

        if self.read_type == E.ReadTypes.ascii:
            try:
                if to_type in [E.SendDataTypes.INT, E.SendDataTypes.LONG]:
                    return int(float(val))
                
                elif to_type in [E.SendDataTypes.FLOAT]:
                    return float(val)
                
                elif to_type in [E.SendDataTypes.STRING]:
                    return str(val)
                
                elif to_type in [E.SendDataTypes.BIT]:
                    if self.convert(val, E.SendDataTypes.INT) != 0:
                        return 1
                    return 0
                
                elif to_type in [E.SendDataTypes.Boolean]:
                    if type(val) == bool:
                        return val
                    
                    elif type(val) == int:
                        return val != 0
                    
                    elif type(val) == str:
                        if val in ["False", "false", "0", ""]:
                            return False
                        return True
                    
            except Exception as exception:
                print(exception)
        return None


class JsonDevice(ConnectedDevice):
    attributes: DynAttr = []
    # attributes is a list of attributes brought in from json
    # the DynAttr class holds the metadata only, E.g. where the value is saved as a file - the attribute itself is set on the class
    # in the override of the super get_state()
    parsed_json: dict = {}

    def __init__(self, conf_file):
        parsed_json: dict = parse_json_for_config(conf_file)

        # Construct DynAttrs from json 
        for attr in parsed_json[ToSDK.Credentials.attributes]:
            m_att = DynAttr(attr[ToSDK.Attributes.name],attr[ToSDK.Attributes.private_data],attr[ToSDK.Attributes.private_data_type])
            self.attributes.append(m_att)

        super().__init__(
            parsed_json[ToSDK.Credentials.company_id],
            parsed_json[ToSDK.Credentials.unique_id],
            parsed_json[ToSDK.Credentials.environment],
            parsed_json[ToSDK.Credentials.sdk_id],
            parsed_json[ToSDK.Credentials.sdk_options]
        )
        # make accessible to any inheriting classes
        self.parsed_json = parsed_json


    def get_state(self):
        '''Do not override'''
        data_obj = {}
        data_obj.update(self.get_attributes_state())
        data_obj.update(self.get_local_state())
        return data_obj
    
    def get_attributes_state(self) -> dict:
        '''Gets all attributes specified from the JSON file'''
        data_obj = {}
        attribute: DynAttr
        for attribute in self.attributes:
            for metadata in self.attribute_metadata:
                if attribute.name == metadata[E.MetadataKeys.name]:
                    data_obj[attribute.name] = attribute.get_value(metadata[E.MetadataKeys.data_type])
                    break

        return data_obj
    
    def get_local_state(self) -> dict:
        '''Overrideable - return dictionary of local data to send to the cloud'''
        #print("no class-defined object properties")
        return {}

