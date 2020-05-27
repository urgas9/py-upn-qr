import json

from qr_generator import generate_qr_code

def lambda_handler(event, context):

    image = generate_qr_code()

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
