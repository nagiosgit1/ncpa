#!/bin/bash

echo -e "***** osx/package.sh"

# Get version
DIR=$( cd "$(dirname "$0")" ; pwd -P )
BUILD_DIR="$DIR/.."
NCPA_VER=$(cat $BUILD_DIR/../VERSION)
ARCH=$(arch)

(
    # Move .dylib files into lib folder. TODO: make python install do this correctly?
    mv ncpa-$NCPA_VER/*.dylib ncpa-$NCPA_VER/lib
    mkdir NCPA-INSTALL-$NCPA_VER
    mv ncpa-$NCPA_VER NCPA-INSTALL-$NCPA_VER/ncpa
    cp NCPA-INSTALL-$NCPA_VER/ncpa/build_resources/macosuninstall.sh NCPA-INSTALL-$NCPA_VER/ncpa/uninstall.sh
    mv NCPA-INSTALL-$NCPA_VER/ncpa/build_resources/macosinstall.sh NCPA-INSTALL-$NCPA_VER/install.sh
#     install_name_tool -change /Library/Frameworks/Python.framework/Versions/2.7/Python @executable_path/Python NCPA-INSTALL-$NCPA_VER/ncpa/ncpa_listener
#     install_name_tool -change /Library/Frameworks/Python.framework/Versions/2.7/Python @executable_path/Python NCPA-INSTALL-$NCPA_VER/ncpa/ncpa_passive
    hdiutil create -volname NCPA-$NCPA_VER -srcfolder NCPA-INSTALL-$NCPA_VER -ov -format UDZO ncpa_$NCPA_VER-1_amd64.dmg
)
