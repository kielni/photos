#!/bin/bash

cd ../deploy
pip install -r requirements.txt -t .
zip -r ../lambda.zip .
echo
echo "uploading"
aws lambda update-function-code --function-name photos-to-s3 --zip-file fileb://../lambda.zip --region us-east-1 --profile megapis
cd ../photos-to-s3
