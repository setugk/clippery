#!/bin/sh
# Journery NAS rebuild — builds shared image, restarts all instances.
# Runs on the NAS via deploy.sh.
# To add a new instance: add its container name to INSTANCES below.

INSTANCES="clipboard clipboard-agrams"

cd /volume1/docker/journery-build

echo "Building journery:latest..."
docker build -t journery:latest . || { echo "Build failed"; exit 1; }

for instance in $INSTANCES; do
  docker restart "$instance" && echo "Restarted: $instance"
done

echo "All instances updated."
