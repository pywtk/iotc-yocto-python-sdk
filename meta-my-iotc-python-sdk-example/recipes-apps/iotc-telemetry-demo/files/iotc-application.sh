#!/bin/bash
app_name="telemetry_demo.py"
config_name="config.json"

app_A_dir="/usr/bin/local/iotc/"
config_A_dir="/usr/local/iotc/"
app_B_dir="${app_A_dir::-1}.backup/"
config_B_dir="${config_A_dir::-1}.backup/"

run_app() {
    /usr/bin/python3 -u $1 $2
}

SECONDARY_EXISTS=false
SECONDARY_PATH=$app_B_dir$app_name
if [ -e "${SECONDARY_PATH}" ]; then
    SECONDARY_EXISTS=true
fi

PRIMARY_EXISTS=false
PRIMARY_PATH=$app_A_dir$app_name
if [ -e "${PRIMARY_PATH}" ]; then
    PRIMARY_EXISTS=true
fi

if [ "${PRIMARY_EXISTS}"] && [ "${SECONDARY_EXISTS}" ]; then
    echo "Primary and Secondary exist, running"
    run_app $app_A_dir$app_name $config_A_dir$config_name || (echo "Primary app has failed, trying backup" && run_app $app_B_dir$app_name $config_B_dir$config_name)

elif [ "${PRIMARY_EXISTS}" ]; then
    echo "Only Primary exists, running"
    run_app $app_A_dir$app_name $config_A_dir$config_name

elif [ "${SECONDARY_EXISTS}" ]; then
    echo "Only Secondary exists, running"
    run_app $app_B_dir$app_name $config_B_dir$config_name 

else
    echo "No valid application exists to run"
fi