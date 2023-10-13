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
                print(ack_message)
                self.send_ack(msg, ack, ack_message)
                self.device.needs_exit = True

                shutil.rmtree(OTA_DOWNLOAD_DIRECTORY, ignore_errors=True)
                return

    #         self.ota_backup_primary()
    #         try:
    #             self.ota_extract_to_a_and_move_old_a_to_b(payload_filename)
    #             self.device.needs_exit  = True
    #         except:
    #             self.ota_restore_primary()
    #             self.send_ack(data, E.Values.OtaStat.FAILED, "OTA FAILED to install")
    #             self.device.needs_exit  = False
    #             raise

    #         if self.device.needs_exit:
    #             self.ota_delete_primary_backup()
    #             self.send_ack(data, E.Values.OtaStat.SUCCESS, "OTA SUCCESS")
    #             return

    #     self.send_ack(data, E.Values.OtaStat.FAILED, "OTA FAILED,invalid payload")



    # @staticmethod
    # def ota_extract_to_a_and_move_old_a_to_b(tarball_name:str):
    #     """Extract OTA tarball and assign to primary, move old primary to secondary"""
    #     # extract tarball to new directory
    #     file = tarfile.open(AP.main_app_dir + AP.tarball_download_dir + tarball_name)
    #     file.extractall(AP.main_app_dir + AP.tarball_extract_dir)
    #     file.close()

    #     # rm secondary dir
    #     path = AP.main_app_dir + AP.secondary_app_dir
    #     shutil.rmtree(path, ignore_errors=True)

    #     # move primary to secondary
    #     os.rename(AP.main_app_dir + AP.primary_app_dir, AP.main_app_dir + AP.secondary_app_dir)

    #     # copy extracted dir to primary dir
    #     src = AP.main_app_dir + AP.tarball_extract_dir
    #     dst = AP.main_app_dir + AP.primary_app_dir
    #     shutil.copytree(src, dst)

    #     # delete temp folders
    #     shutil.rmtree(AP.main_app_dir + AP.tarball_download_dir, ignore_errors=True)
    #     shutil.rmtree(AP.main_app_dir + AP.tarball_extract_dir, ignore_errors=True)

    # @staticmethod
    # def ota_backup_primary():
    #     """Copy primary app folder for backup"""
    #     src = AP.main_app_dir + AP.primary_app_dir
    #     dst = AP.main_app_dir + AP.primary_app_backup_folder_name

    #     if os.path.exists(dst):
    #         shutil.rmtree(dst, ignore_errors=True)
    #     shutil.copytree(src, dst)

    # @staticmethod
    # def ota_restore_primary():
    #     """Delete faulty primary app folder and replace with backup"""
    #     shutil.rmtree(AP.main_app_dir + AP.primary_app_dir, ignore_errors=True)
    #     os.rename(AP.main_app_dir + AP.primary_app_backup_folder_name, AP.main_app_dir + AP.primary_app_dir)

    # @staticmethod
    # def ota_delete_primary_backup():
    #     """Delete primary app backup folder"""
    #     shutil.rmtree(AP.main_app_dir + AP.primary_app_backup_folder_name, ignore_errors=True)
