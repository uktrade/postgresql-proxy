#!/bin/sh

export DOWNSTREAM__IP=0.0.0.0
export DOWNSTREAM__PORT=5432

export UPSTREAM__HOST=$(echo $VCAP_SERVICES | jq -r '.["postgres"][0].credentials.host')
export UPSTREAM__PORT=$(echo $VCAP_SERVICES | jq -r '.["postgres"][0].credentials.port')

exec $@
