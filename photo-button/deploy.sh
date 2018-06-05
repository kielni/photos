#!/bin/bash

cd ../deploy-button
pip install -r requirements.txt -t .
zip -r ../lambda.zip .
echo
echo "uploading"
aws lambda update-function-code --function-name button-mms --zip-file fileb://../lambda.zip --region us-east-1 --profile megapis
cd ../photo-button
