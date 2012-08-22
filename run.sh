#!/bin/bash

if [ -a env  ]
then
    echo "Environment exists, leaving alone."
else
    echo "Creating environment."
    virtualenv env
    pip install -r requirements
fi

source env/bin/activate
python generate.py

