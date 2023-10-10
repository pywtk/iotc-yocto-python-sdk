"""Showcase cloud commands that execute scripts"""
from enum import Enum
from JsonParser import ToSDK
import sys
from Enums import Enums as E
from JsonDevice import JsonDevice
sys.path.append("iotconnect")
from typing import Union # to use Union[Enum, None] type hint
import os


import subprocess

class CommandDevice(JsonDevice):

    SCRIPTS_PATH:str = ""
    scripts: list = []

    def __init__(self, conf_file):
        super().__init__(conf_file)
        self.SCRIPTS_PATH = self.parsed_json[ToSDK.Credentials.script_path]
        self.get_all_scripts()

    class DeviceCommands(Enum):
        ECHO = "echo "
        LED = "led "
        TEST = "test_command"

        @classmethod
        def get(cls, full_command:str) -> Union[Enum, None]:
            '''Validates full command string against accepted enumerated commands'''
            if full_command is not None:
                for dc in [dc.value for dc in cls]:
                    if (sliced := full_command[:len(dc)]) == dc:
                        return cls(sliced)
            return None

    def get_all_scripts(self):
        self.scripts: list = [f for f in os.listdir(self.SCRIPTS_PATH) if os.path.isfile(os.path.join(self.SCRIPTS_PATH, f))]

    def device_cb(self,msg):
        # Only handles messages with E.Values.Commands.DEVICE_COMMAND (also known as CMDTYPE["DCOMM"])
        full_command = E.get_value(msg, E.Keys.device_command)
        hardcoded_command = self.DeviceCommands.get(full_command)

        if hardcoded_command == self.DeviceCommands.ECHO:
            to_print = full_command[len(self.DeviceCommands.ECHO.value):]
            print(to_print)
            self.send_ack(msg,E.Values.AckStat.SUCCESS, "Command Executed Successfully")

        elif hardcoded_command == self.DeviceCommands.TEST:
            self.send_ack(msg,E.Values.AckStat.SUCCESS, "Command Executed Successfully")

        else:
            command = full_command.split(' ')
                        
            if command[0] in self.scripts:
                command[0] = self.SCRIPTS_PATH + command[0]
                process_result = subprocess.run(command, check=False, capture_output=True)

                ack = E.Values.AckStat.FAIL
                process_output_bytes: bytes = process_result.stderr

                if process_result.returncode == 0:
                    ack = E.Values.AckStat.SUCCESS
                    process_output_bytes = process_result.stdout

                ack_message = str(process_output_bytes, 'UTF-8')
                self.send_ack(msg,ack, ack_message)
                return
            
            self.send_ack(msg,E.Values.AckStat.FAIL, "Command not valid/script not found")


