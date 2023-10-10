#!/bin/bash

led_path="/home/akarnil/Documents/Work/iotc-yocto-python-sdk/meta-my-iotc-python-sdk-example/recipes-apps/iotc-telemetry-demo/files/fake-led"

# Check if the user provided an argument
if [ $# -ne 1 ]; then
    >&2 echo "Usage: $0 <0 or 1>"
    exit 1
fi


# Get the value from the command line argument
value="$1"

# Check if the provided value is either 0 or 1
if [ "$value" -ne 0 ] && [ "$value" -ne 1 ]; then
    >&2 echo "Error: Input must be either 0 or 1."
    exit 1
fi

# Write the value to the hardcoded output file
echo "$value" > "$led_path"

# Check if the write was successful
if [ $? -eq 0 ]; then
    echo "Value '$value' written to '$led_path' successfully."
else
    >&2 echo "Error writing to '$led_path'."
    exit 1
fi
