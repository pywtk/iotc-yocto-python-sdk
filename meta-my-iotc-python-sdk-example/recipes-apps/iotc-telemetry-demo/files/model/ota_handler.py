'''
    Module handling OTA update functionality
'''
import os
import tarfile
import shutil
import subprocess

from urllib.request import urlretrieve
from model.json_device import JsonDevice

from model.enums import Enums as E
# from model.app_paths import AppPaths as AP


# OTA payload must be a single file of extension .tar.gz
# the updated application .py file  must be called the same
# as a previous version otherwise it will not load, refer to AP.app_name

# OTA payload will replace entire contents of primary folder with contents of payload

OTA_DOWNLOAD_DIRECTORY = "/tmp/.ota/"
OTA_INSTALL_SCRIPT = "install.sh"

EXTENSIONS_THAT_REQUIRE_REBOOT = ['.py', '.json']


class OtaHandler:
    '''Class for handling OTA'''
    device: JsonDevice = None

    def __init__(self, connected_device: JsonDevice, msg):
        self.device = connected_device
        self.device.in_ota = True
        self.device.needs_exit = False
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

        valid_payload: bool = False
        data: dict = msg

        if ("urls" in data) and len(data["urls"]) == 1:
            if ("url" in data["urls"][0]) and ("fileName" in data["urls"][0]):
                if data["urls"][0]["fileName"].endswith(".gz"):
                    valid_payload = True

        if not valid_payload:
            self.send_ack(data, E.Values.OtaStat.FAILED, "payload not valid, check file extension or url invalid")
            return

        # download tarball from url to download_dir
        urls = data["urls"][0]
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

        try:
            file = tarfile.open(payload_path)
            file.extractall(extracted_path)
            file.close()
        
        except tarfile.ExtractError:
            self.send_ack(data, E.Values.OtaStat.FAILED, "Failed to extract OTA, aborting")
            shutil.rmtree(OTA_DOWNLOAD_DIRECTORY, ignore_errors=True)
            return
        
        requires_reboot: bool = False
        commands_list_needs_updating: bool = False

        install_script_path: str = None
        for root, dirs, files in os.walk(extracted_path):
            for file in files:
                if file.endswith(OTA_INSTALL_SCRIPT):
                    install_script_path = os.path.join(root, file)
                    continue
                
                if file.endswith(tuple(EXTENSIONS_THAT_REQUIRE_REBOOT)):
                    requires_reboot = True
                
                if file.endswith(tuple('.sh')):
                    commands_list_needs_updating = True

        if install_script_path is None:
            self.send_ack(data, E.Values.OtaStat.FAILED, OTA_INSTALL_SCRIPT + " Not found in payload")
            return

        process = subprocess.run(install_script_path, check=False, capture_output=True)
        process_success:bool = (process.returncode == 0)

        ack = E.Values.OtaStat.SUCCESS if process_success else E.Values.OtaStat.FAILED
        process_output: bytes = process.stdout if process_success else process.stderr
        
        ack_message = str(process_output, 'UTF-8')
        self.send_ack(msg, ack, ack_message)

        if commands_list_needs_updating is True and requires_reboot is False:
            self.device.get_all_scripts()
        self.device.needs_exit = requires_reboot

        shutil.rmtree(OTA_DOWNLOAD_DIRECTORY, ignore_errors=True)
        return