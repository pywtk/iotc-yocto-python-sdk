# IoT-Connect Yocto C SDK
***This IoT-Connect connect layer only supports `hardknott`***

*The following details yocto layers designed to integrate the [iotc Python SDK]([https://github.com/avnet-iotconnect/iotc-python-sdk/tree/master-std-21]). The end result is an image with the SDK repo & a couple of sample python scripts installed. Once said image is flashed to a target, the sample scripts should successfully run & establish comms with an appropriately setup device on https://avnet.iotconnect.io/*

## Layers
There are 2 layers thus far: `meta-iotc-python-sdk` & `meta-my-iotc-python-sdk-example`.
### `meta-iotc-python-sdk`
This layer draws in the various sources required to utilise the SDK. From a yocto perspective it largely serves to install the python SDK as a module into the image.

```
iotc-yocto-python-sdk$ tree meta-iotc-python-sdk/
meta-iotc-python-sdk/
├── conf
│   └── layer.conf
└── recipes-apps
    └── iotc-python-sdk
        ├── iotc-python-sdk_0.1.bb
        └── jsonlib-python3_1.6.1.bb
```

### `meta-my-iotc-python-sdk-example`
This layer provides an example of how a user might write a recipe suitable for their application. It contains a simple application that demonstrates telemetry. Once installed on the image it can be started by logging in & executing `/usr/bin/local/iotc/telemetry-demo.py /path/to/config.json` where `config.json` is a file that contains device authentication information and paths to where telemetry-demo will read data from on the host device. It's expected that in the 1st instance a user would run this demo on their hardware after editing a sample `config.json` to reflect a device they've defined on avnet.iotconnect.io and sensor data particular to their hardware.

By adding the recipe to your image (e.g. `IMAGE_INSTALL += " iotc-telemetry-demo"` in `conf/local.conf`) you will via dependency include `iotc-python-sdk` from `meta-iotc-python-sdk`

```
iotc-yocto-python-sdk$ tree meta-my-iotc-python-sdk-example/
meta-my-iotc-python-sdk-example/
├── conf
│   └── layer.conf
├── recipes-apps
│   └── iotc-telemetry-demo <------------------ Recipe directory
│       ├── files
│       │   ├── eg-private-repo-data <--------- Location for certificates/keys & other config data for development purposes.
│       │   │   ├── configSymmrcKy.json
│       │   │   ├── configX509.json
│       │   ├── model <------------------------ Directory of support sources
│       │   │   ├── device_model.py
│       │   │   ├── enums.py
│       │   │   ├── json_device.py
│       │   │   ├── ota_handler.py <----------- Handling OTA logic application side
│       │   │   └── json_parser.py
│       │   ├── iotc-application.sh <---------- Application launcher for A/B system updates
│       │   └── telemetry_demo.py <------------ Top level python source.
│       └── iotc-telemetry-demo_0.1.bb <------- Recipe
└── recipes-systemd
    └── iotc-telemetry-demo-service <---------- Example of a systemd service designed to start telemetry on boot (disabled by default)
        ├── files
        │   └── iotc-telemetry-demo.service
        └── iotc-telemetry-demo-service_git.bb
```

As developing a iotc application involves the use of private/secure data like keys/certificates and the user is expected to develop same application using SCM like git, it's worth taking a moment to be aware of risks of accidentally uploading private data to places it should not belong. The directory `eg-private-repo-data` seeks to provide a safe space to place sensitive data like device keys etc for development purposes only. When the user installs the _development_ version of the recipe (e.g. `IMAGE_INSTALL += " iotc-telemetry-demo-dev"` in `conf/local.conf`) any files within `eg-private-repo-data` will be installed in the rootfs of the image. The `.gitignore` settings for this repo are also configured to prevent accidental upload of *.pem or *.crt files.

This approach allows the user to develop their solution conveniently, then when it's time to provide production builds, the result would be a clean installation awaiting first time configuration post image flash.

## Configuration JSONs
One schema for a commerical iotc solution that uses a fleet of devices would be a single set of binaries that use individual config files to implement individual devices. This telemetry demo illustrates one way the user might achieve this.

In `eg-private-repo-data` are sample JSON files, these are explained in more detail in the drop-down section below. In summary:

By editing the `duid`, `cpid`, `env`, `sdk_id` and `auth` members of a config.json, the binary should have all the info required to successfully establish a connection to avnet.iotconnect.io with no code edits.

Within config.json there is an object called `device` which has a child called `attributes`. Inside is an array of attributes, the names are derived from the Device Template's attributes in avnet.iotconnect.io, the names must match for data to be correctly sent to the right place.

`private_data` is a path to the data on the device that is sent to the cloud.

`private_data_type` allows you to read the file in either `ascii` or `binary` mode, though `ascii` is recommended.

By editing these members you should be able to send data from your device to avnet.iotconnect.io again with no edits. (You may need to get your sensor data into a file, or it may already be in that form).

<details>
  <summary>JSON Config More Info</summary>
  The config json provides a quick and easy way to provide a user's executable with the requisite device credentials for any connection and a convenient method of mapping sensors to iotc device attributes. The demo source provided will match an `attribute.name` to a path on the user's host where the relevant sensor data resides. It also indicates to the demo what format to expect the data at the path to be in.

```json
{
    "sdk_ver": "2.1",
    "duid": "Your Device's name in https://avnet.iotconnect.io/device/1",
    "cpid": "'CPID' from https://avnet.iotconnect.io/key-vault",
    "env": "'Environment' from https://avnet.iotconnect.io/key-vault",
    "iotc_server_cert": "/etc/ssl/certs/DigiCert_Global_Root_G2.pem",
    "sdk_id": "'SDK Identities -> Language: Python **, Version: 1.0' from https://avnet.iotconnect.io/key-vault",
    "auth": {
      "auth_type": "IOTC_AT_X509",
      "params": {
        "client_key": "/path/to/device.key",
        "client_cert": "/path/to/DeviceCertificate.pem"
      }
    },
    "device": {
      "commands_list_path": "Path to folder containing all commands",
      "offline_storage": {
        "available_space_MB": 1,
        "file_count": 1
      },
      "attributes": [
        {
          "name": "power",
          "private_data": "/usr/bin/local/iotc/dummy_sensor_power",
          "private_data_type": "ascii"
        },
        {
          "name": "level",
          "private_data": "/usr/bin/local/iotc/dummy_sensor_level",
          "private_data_type": "ascii"
        }
      ]
    }
}
```

Say you have a device `my-demo-device` based on a template on avnet.iotconnect.io that looks like:
```json
{
  "code": "my-template",
  "name": "My Template",
  "authType": 5,
  "isIotEdgeEnable": false,
  "attributes": [
    {
      "name": "Version",
      "type": "STRING",
      "description": null,
      "unit": null
    }
  ],
  "commands": [
  ],
  "messageVersion": "1.0",
  "msgCode": "7LIBCD6",
  "properties": {
    "description": null,
    "dataFrequency": "60",
    "fileSupport": false
  },
  "_meta": {
    "version": "2.0"
  }
}
```

You would first (copy &) edit config.json with relevant device connection details thusly:

```json
{
    "sdk_ver": "2.1",
    "duid": "Your Device's name in https://avnet.iotconnect.io/device/1",
```
Would become: 
```json
{
    "sdk_ver": "2.1",
    "duid": "myDemoDevice",
```

Then with regard to mapping template attributes to paths, in order to map the `Version` attribute to a path on the device you would edit config.json to include:
```json
      "attributes": [
        {
          "name": "Version",
          "private_data": "/proc/version",
          "private_data_type": "ascii"
        },
```
</details>

### How to include layers
To include the layers within a yocto environment:

1. check them out to the `sources` directory in your yocto environment. 
1. add them to `conf/bblayers` file in your build directory
1. add the recipes to your build target e.g. add `IMAGE_INSTALL += " iotc-telemetry-demo-dev"` to the bottom of `build/conf/local.conf`
1. using the config.json files in `eg-private-repo-data` as a template, create your own config.json with details of the device you have setup on iotconnect.io.
1. editing the same json as in the last step, edit the `attributes` section of the JSON so the `name` of the attribute maps to a path on your system where the relevant data can be found e.g. the path to the position data of an I2C accelerometer might be: `/sys/bus/i2c/devices/1-0053/position`.
1. build with a bitbake call e.g. `./bitbake core-image-base`
1. Flash the resultant image to the device.
1. Login into the device & run the command `/usr/bin/local/iotc/telemetry-demo.py /usr/local/iotc/config.json`

## Board specific examples can be found [here](board_specific_readmes/README.md)

# OTA

  This demo showcases OTA update functionality, it involves three new components,
  1. `iotc-application.sh` which is used to run the telemetry demo, it also contains mechanisms to execute a fallback version of the telemetry demo in case of erroneous OTA.

  1. `ota-handler.py` which includes all functionality to download and execute the OTA payload.

  1. The OTA payload, a tarball including all files to update the application, the structure of the payload can be found [here](/meta-my-iotc-python-sdk-example/recipes-apps/iotc-telemetry-demo/files/ota-payload-template/README)

