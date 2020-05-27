import base64

from io import BytesIO

from qr_generator import generate_qr_code


def lambda_handler(event, context):
    image = generate_qr_code()
    with BytesIO() as buffer:
        image.save(buffer, 'png')
        base64qrCode = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return {
        'source_name': event.get('name'),
        'name': 'UPN QR code generator',
        'author': 'urgas9',
        'url': 'https://github.com/urgas9/py-upn-qr',
        'qr_code': base64qrCode,
    }
