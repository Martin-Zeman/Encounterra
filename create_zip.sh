#!/bin/bash

if [ -f core_deployment_package.zip ]; then
    rm core_deployment_package.zip
fi

cd .venv/lib/python3.10/site-packages
zip -r ../../../../core_deployment_package.zip .

cd ../../../../
zip core_deployment_package.zip lambda_function.py
zip -r -g core_deployment_package.zip simulator/