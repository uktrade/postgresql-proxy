#!/bin/sh

export DOWNSTREAM_IP=0.0.0.0
export DOWNSTREAM_PORT=5432

export UPSTREAM_HOST=$(echo $VCAP_SERVICES | jq -r '.["postgres"][0].credentials.host')
export UPSTREAM_PORT=$(echo $VCAP_SERVICES | jq -r '.["postgres"][0].credentials.port')

exec $@
