'''
    Module handling OTA update functionality
'''
import os
import tarfile
import shutil
import subprocess

from urllib.request import urlretrieve
from .DeviceModel import ConnectedDevice

from .Enums import Enums as E
# from model.app_paths import AppPaths as AP


# OTA payload must be a single file of extension .tar.gz
# the updated application .py file  must be called the same
# as a previous version otherwise it will not load, refer to AP.app_name

# OTA payload will replace entire contents of primary folder with contents of payload

OTA_DOWNLOAD_DIRECTORY = "/tmp/.ota/" 
OTA_INSTALL_SCRIPT = "install.sh"

class OtaHandler:
    '''Class for handling OTA'''
    device: ConnectedDevice = None

    def __init__(self, connected_device: ConnectedDevice, msg):
        self.device = connected_device
        self.device.in_ota = True
        self.ota_perform_update(msg)

    def __del__(self):
        self.device.in_ota = False

    def send_ack(self, msg, status: E.Values.AckStat, message):
        # check if ack exists in message
        if E.get_value(msg, E.Keys.ack) is None:
            print("Ack not requested, returning")
            return
        id_to_send = E.get_value(msg, E.Keys.id)
        self.device.SdkClient.sendOTAAckCmd(msg[E.Keys.ack], status, message, id_to_send)

    def ota_perform_update(self,msg):
        """Perform OTA logic"""
        print(msg)

        if (command_type := E.get_value(msg, E.Keys.command_type)) != E.Values.Commands.FIRMWARE:
            print("fail wrong command type, got " + str(command_type))
            return

        payload_valid: bool = False
        data: dict = msg

        if ("urls" in data) and len(data["urls"]) == 1:
            if ("url" in data["urls"][0]) and ("fileName" in data["urls"][0]):
                if data["urls"][0]["fileName"].endswith(".gz"):
                    payload_valid = True

        if payload_valid:
            urls = data["urls"][0]

            # download tarball from url to download_dir
            url: str = urls["url"]
            payload_filename: str = urls["fileName"]
            payload_path: str = OTA_DOWNLOAD_DIRECTORY + payload_filename
            extracted_path: str = OTA_DOWNLOAD_DIRECTORY + "extracted/"

            if not os.path.exists(OTA_DOWNLOAD_DIRECTORY):
                os.mkdir(OTA_DOWNLOAD_DIRECTORY)

            try:
                self.send_ack(data, E.Values.OtaStat.DL_IN_PROGRESS, "downloading payload")
                urlretrieve(url, payload_path)
            except:
                self.send_ack(data, E.Values.OtaStat.DL_FAILED, "payload download failed")
                raise
            self.send_ack(data, E.Values.OtaStat.DL_DONE, "payload downloaded")

            self.device.needs_exit = False

            file = tarfile.open(payload_path)
            file.extractall(extracted_path)
            file.close()

            install_script_path: str = None
            for root, dirs, files in os.walk(extracted_path):
                for file in files:
                    if file.endswith(OTA_INSTALL_SCRIPT):
                        install_script_path = os.path.join(root, file)
                        break

            if install_script_path is not None:
                process = subprocess.run(install_script_path, check=False, capture_output=True)
                process_success:bool = (process.returncode == 0)

                ack = E.Values.OtaStat.SUCCESS if process_success else E.Values.OtaStat.FAILED
                process_output: bytes = process.stdout if process_success else process.stderr
                
                ack_message = str(process_output, 'UTF-8')
                self.send_ack(msg, ack, ack_message)
                self.device.needs_exit = True

                shutil.rmtree(OTA_DOWNLOAD_DIRECTORY, ignore_errors=True)
                return