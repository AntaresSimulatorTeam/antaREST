#!/bin/bash

CURDIR=$(cd `dirname $0` && pwd)
BASEDIR=`dirname $CURDIR`

cd $BASEDIR
alembic downgrade 298aecf6ea40
cd -
