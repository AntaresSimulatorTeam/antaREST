#!/bin/bash

ANTARES_SOLVER_VERSION="8.2"
ANTARES_SOLVER_FULL_VERSION="$ANTARES_SOLVER_VERSION.0"
ANTARES_SOLVER_FULL_VERSION_INT=$(echo $ANTARES_SOLVER_FULL_VERSION | sed 's/\.//g')

ANTARES_SOLVER_FOLDER_NAME="rte-antares-$ANTARES_SOLVER_FULL_VERSION-installer-64bits"
ANTARES_SOLVER_ZIPFILE_NAME="$ANTARES_SOLVER_FOLDER_NAME.zip"

LINK="https://github.com/AntaresSimulatorTeam/Antares_Simulator/releases/download/v$ANTARES_SOLVER_FULL_VERSION/$ANTARES_SOLVER_ZIPFILE_NAME"
DESTINATION="../dist/AntaresWebServer/antares_solver"

echo "Downloading AntaresSimulator from $LINK"
wget -q $LINK

echo "Unzipping $ANTARES_SOLVER_ZIPFILE_NAME and move Antares solver to $DESTINATION"
unzip -q $ANTARES_SOLVER_ZIPFILE_NAME
mkdir $DESTINATION

mv "$ANTARES_SOLVER_FOLDER_NAME/bin/antares-$ANTARES_SOLVER_VERSION-solver.exe" $DESTINATION
mv $ANTARES_SOLVER_FOLDER_NAME/bin/sirius_solver.dll $DESTINATION
mv $ANTARES_SOLVER_FOLDER_NAME/bin/zlib1.dll $DESTINATION


echo "Cleaning up"
rm $ANTARES_SOLVER_ZIPFILE_NAME
rm -rf $ANTARES_SOLVER_FOLDER_NAME

echo "Copy basic configuration files"
cp -r ../resources/deploy/* ../dist/
cp ../README.md ../dist/
sed -i "s/700: path\/to\/700/$ANTARES_SOLVER_FULL_VERSION_INT: .\/antares_solver\/antares-$ANTARES_SOLVER_VERSION-solver.exe/g" ../dist/config.yaml

echo "Create symbolic link to antares_solver"
cd ../dist
ln -s AntaresWebServer/AntaresWebServer.exe AntaresWebServer.exe

echo "Zip the package"
zip --symlinks -r -q AntaresWebServer *

echo "Cleaning up"
shopt -s extglob
rm -rf !(*.zip)

echo "Done"


