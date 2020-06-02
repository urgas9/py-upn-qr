import base64
import http
import json
from io import BytesIO

from upn_qr import UPNQR


def lambda_handler(event, context):
    request_payload = event.get('body')
    request_headers = event.get('headers')

    if request_payload is None or request_payload == "":
        return _lambda_proxy_response(
            status_code=http.HTTPStatus.BAD_REQUEST,
            body=json.dumps({
                "errors": ["missing payload body"],
            }))

    request_payload_dict = json.loads(request_payload)

    upnqr = UPNQR.from_dict(request_payload_dict)
    errors = [e for e in upnqr.validate_fields()]

    # There are validation errors, return them in a dict, keyed by field name
    if len(errors) > 0:
        return _lambda_proxy_response(
            status_code=http.HTTPStatus.BAD_REQUEST,
            body=json.dumps({
                "errors": [f"{e.path}: {e.message}" if e.path else e.message for e in errors],
            }))
    else:
        # No validation errors, generate base64 encoded QR code image
        image = upnqr.make_qr_code()
        with BytesIO() as buffer:
            image.save(buffer, "png")
            base64_qr_code = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # Based on passed HTTP header, decide on the output
        if request_headers is not None and request_headers.get("Accept", "") == "image/png":
            return _lambda_proxy_response(
                status_code=http.HTTPStatus.OK,
                body=base64_qr_code,
                is_base64_encoded=True,
                headers={
                    "Content-Type": "image/png"
                })
        else:
            return _lambda_proxy_response(
                status_code=http.HTTPStatus.OK,
                body=json.dumps({
                    "source_data": request_payload_dict,
                    "qr_code": base64_qr_code,
                }))


def _lambda_proxy_response(status_code: int, body: str, headers: dict = None, is_base64_encoded: bool = False) -> dict:
    return {
        "statusCode": status_code,
        "body": body,
        "headers": headers,
        "isBase64Encoded": is_base64_encoded,
    }
