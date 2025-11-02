#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

docker build . \
    --no-cache \
    -t oddstracker:latest \
    -t maxo5499/sportsstack-oddstracker:latest