#!/bin/bash
app_name="telemetry_demo.py"
config_name="config.json"

app_A_dir="/usr/bin/local/iotc/"
config_A_dir="/usr/local/iotc/"
app_B_dir="${app_A_dir::-1}.backup/"
config_B_dir="${config_A_dir::-1}.backup/"

echo $app_A_dir$app_name
echo $config_A_dir$config_name

# Execute the first program
/usr/bin/python3 -u $app_A_dir$app_name $config_A_dir$config_name

# Check the exit status of the first program
if [ $? -ne 0 ]; then
    echo "The first program failed."
    if [-d "$app_B_dir" ]; then
        echo "Executing backup program"
        /usr/bin/python3 -u $app_B_dir$app_name $config_B_dir$config_name
    fi
fi
