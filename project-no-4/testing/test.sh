#! /bin/bash

echo "Running tests on container $1..."

# Download and run the docker image
docker run -d -p 5000:5000 $1

# Run the test suite (in python)
python test.py

# Clean up the docker image
#docker image rm -f $1