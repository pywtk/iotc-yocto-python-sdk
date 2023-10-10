from enum import Enum
import sys
from Enums import Enums as E
from JsonDevice import JsonDevice
sys.path.append("iotconnect")
from typing import Union # to use Union[Enum, None] type hint
import os

import subprocess

class CommandDevice(JsonDevice):
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
            
            # Potentially move this variable to Json
            SCRIPTS_DIR = "/home/akarnil/Documents/Work/iotc-yocto-python-sdk/meta-my-iotc-python-sdk-example/recipes-apps/iotc-telemetry-demo/files/"
            
            # Potentially run once on start up
            scripts: list = [f for f in os.listdir(SCRIPTS_DIR) if os.path.isfile(os.path.join(SCRIPTS_DIR, f))]
            
            if command[0] in scripts:
                command[0] = SCRIPTS_DIR + command[0]
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


