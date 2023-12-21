LICENSE = "GPL-3.0"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/GPL-3.0;md5=c79ff39f19dfec6d293b95dea7b07891"

RDEPENDS:${PN} += " bash"
RDEPENDS_${PN} += " python3-iotconnect-sdk"


SRC_URI = "file://iotc-demo.py \
    file://model \
    file://eg-private-repo-data \
    file://scripts \
"

APP_INSTALL_DIR = "${base_prefix}/usr/bin/local/iotc"
PRIVATE_DATA_DIR = "${base_prefix}/usr/local/iotc"

FILES:${PN}-dev = "${PRIVATE_DATA_DIR}/* \
"

do_install() {
    install -d ${D}${APP_INSTALL_DIR}
    for f in ${WORKDIR}/model/*
    do
        if [ -f $f ]; then
            if [ ! -d ${D}${APP_INSTALL_DIR}/model ]; then
                install -d ${D}${APP_INSTALL_DIR}/model
            fi
            install -m 0755 $f ${D}${APP_INSTALL_DIR}/model/
        fi
    done

    # Add command scripts
    for f in ${WORKDIR}/scripts/*
    do
        if [ -f $f ]; then
            if [ ! -d ${D}${APP_INSTALL_DIR}/scripts ]; then
                install -d ${D}${APP_INSTALL_DIR}/scripts
            fi
            install -m 0755 $f ${D}${APP_INSTALL_DIR}/scripts/
        fi
    done

    # Install main app
    install -m 0755 ${WORKDIR}/iotc-demo.py ${D}${APP_INSTALL_DIR}/

    if [ ! -d ${D}${PRIVATE_DATA_DIR} ]; then
        install -d ${D}${PRIVATE_DATA_DIR}
    fi
    cp -R --no-preserve=ownership ${WORKDIR}/eg-private-repo-data/* ${D}${PRIVATE_DATA_DIR}/

    # Add dummy sensor files
    echo 1 > ${D}${APP_INSTALL_DIR}/dummy_sensor_power
    echo 2 > ${D}${APP_INSTALL_DIR}/dummy_sensor_level
}


# systemd component, installs only if systemd is part of image

inherit systemd
SYSTEMD_AUTO_ENABLE = "disable"
SYSTEMD_SERVICE:${PN} = "iotc-demo.service"

SRC_URI += " file://iotc-demo.service "
FILES:${PN} += "${systemd_unitdir}/system/iotc-demo.service"

HAS_SYSTEMD = "${@bb.utils.contains('DISTRO_FEATURES', 'systemd', 'true', 'false', d)}"
do_install:append() {
    if ${HAS_SYSTEMD}; then
        install -d ${D}/${systemd_unitdir}/system
        install -m 0644 ${WORKDIR}/iotc-demo.service ${D}/${systemd_unitdir}/system
    fi
}
