#!/bin/bash

scene=$1
orbit=$2

cd /Projects/remote_sensing/sarris_images/Orbit_${orbit}


s3cmd -c ~/.s3cfg --skip-existing -r get s3://${scene}
