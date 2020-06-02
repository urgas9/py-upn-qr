import base64
import http
import json
from io import BytesIO

from upn_qr import UPNQR


def lambda_handler(event, context):
    request_payload = event.get('body')
    request_headers = event.get('headers')

    upnqr = UPNQR.from_dict(json.loads(request_payload))
    errors = [e for e in upnqr.validate_fields()]

    response_headers = {"Content-Type": "application/json"}
    is_base64_encoded_body = False
    # There are validation errors, return them in a dict, keyed by field name
    if len(errors) > 0:
        status_code = http.HTTPStatus.BAD_REQUEST
        body = json.dumps({
            "errors": [f"{e.path}: {e.message}" if e.path else e.message for e in errors],
        })
    # No validation errors, return QR code in response
    else:
        # generate base64 encoded QR code image
        image = upnqr.make_qr_code()
        with BytesIO() as buffer:
            image.save(buffer, "png")
            base64_qr_code = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # Based on passed HTTP header, decide on the output
        status_code = http.HTTPStatus.OK
        if request_headers is not None and request_headers.get("Accept", "") == "image/png":
            body = base64_qr_code
            response_headers = {
                "Content-Type": "image/png"
            }
            is_base64_encoded_body = True
        else:
            body = json.dumps({
                "source_data": request_payload,
                "qr_code": base64_qr_code,
            })

    return {
        "statusCode": status_code,
        "body": body,
        "headers": response_headers,
        "isBase64Encoded": is_base64_encoded_body,
    }
