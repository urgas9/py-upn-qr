#!/usr/bin/env bash

temp_dir="temp-release"
output_zip_name="upnqr-lambda-release.zip"

# Prepare virtual environment and install required dependencies
mkdir ${temp_dir}
pip install -r requirements.txt -t ${temp_dir}
deactivate

# Remove possible pre-existing ZIP file
rm ${output_zip_name}

# Add dependencies to the ZIP file
cd ${temp_dir}
zip -r9 ${OLDPWD}/${output_zip_name} .

# Add source code to the ZIP file
cd ${OLDPWD}
zip -g ${output_zip_name} aws_lambda.py qr_generator.py upn-qr-schema.json

rm -r ${temp_dir}

echo " ++ Updating AWS Lambda... ++ "
# Update AWS Lambda function
aws lambda update-function-code --function-name upnqr --zip-file fileb://${output_zip_name} --region=eu-central-1
