#!/bin/bash

git clone git://git.openembedded.org/meta-openembedded -b hardknott
git clone git://git.yoctoproject.org/poky.git -b hardknott

source poky/oe-init-build-env

# Add required layers for minimal qemu build
bitbake-layers add-layer ../meta-openembedded/meta-oe/ 
bitbake-layers add-layer ../meta-openembedded/meta-python/
bitbake-layers add-layer ../meta-openembedded/meta-multimedia/
bitbake-layers add-layer ../meta-openembedded/meta-networking/
     
 
# Add all meta layers from the repo
search_directory=../../
search_directory=$(readlink -f $search_directory)
echo $search_directory
find "$search_directory" -maxdepth 1 -type d -name 'meta-*' | while read -r folder; do
    # Check if the folder exists
    if [ -d "$folder" ]; then
        echo "adding folder: $folder to bitake-layers"
        bitbake-layers add-layer $folder
    fi
done
    
# Add systemd
echo -e 'DISTRO_FEATURES_append = " systemd"' >> ./conf/local.conf
echo -e 'DISTRO_FEATURES_BACKFILL_CONSIDERED += " sysvinit"' >> ./conf/local.conf
echo -e 'VIRTUAL-RUNTIME_init_manager = " systemd"' >> ./conf/local.conf
echo -e 'VIRTUAL-RUNTIME_initscripts = " systemd-compat-units"\n' >> ./conf/local.conf

# Add minimal required image changes
# REPLACE iotc-python-sdk WITH WHAT YOU NEED
echo -e '\nIMAGE_INSTALL += " iotc-telemetry-demo-dev packagegroup-core-boot kernel-modules nano"' >> ./conf/local.conf

# Config to build as fast as we can
echo -e '\nBB_NUMBER_THREADS = "${@oe.utils.cpu_count()}"\nPARALLEL_MAKE = "-j ${@oe.utils.cpu_count()}"' >> ./conf/local.conf

# echo 'INHERIT += "rm_work"'                      >> conf/local.conf
CACHE_PATH="/mnt/resource/hardknott/"
echo "DL_DIR     = \"${CACHE_PATH}downloads\""        >> conf/local.conf
echo "SSTATE_DIR = \"${CACHE_PATH}sstate-cache\""     >> conf/local.conf
echo "TMPDIR     = \"${CACHE_PATH}tmp\""              >> conf/local.conf

