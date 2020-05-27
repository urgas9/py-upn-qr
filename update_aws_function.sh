#!/usr/bin/env bash

venv_name="venv-release"
output_zip_name="upnqr-lambda-release.zip"

# Prepare virtual environment and install required dependencies
virtualenv -p python3 ${venv_name}
source ${venv_name}/bin/activate
pip install -r requirements.txt
deactivate

# Remove possible pre-existing ZIP file
rm ${output_zip_name}

# Add dependencies to the ZIP file
cd ${venv_name}/lib/python3.6/site-packages
zip -r9 ${OLDPWD}/${output_zip_name} .

# Add source code to the ZIP file
cd ${OLDPWD}
zip -g ${output_zip_name} aws_lambda.py qr_generator.py

# Update AWS Lambda function
aws lambda update-function-code --function-name upnqr --zip-file fileb://${output_zip_name} --region=eu-central-1
