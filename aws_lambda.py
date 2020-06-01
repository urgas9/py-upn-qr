import base64
from io import BytesIO

from upn_qr import UPNQR


def lambda_handler(event, context):
    upnqr = UPNQR.from_dict(event)
    errors = [e for e in upnqr.validate_fields(event)]
    # There are validation errors, return them in a dict, keyed by field name
    if len(errors) > 0:
        return {
            "errors": {".".join(e.path): e.message for e in errors}
        }

    image = upnqr.make_qr_code()

    with BytesIO() as buffer:
        image.save(buffer, "png")
        base64_qr_code = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return {
        "name": "UPN QR code generator",
        "author": "urgas9",
        "url": "https://github.com/urgas9/py-upn-qr",
        "source": event,
        "qr_code": base64_qr_code,
    }
