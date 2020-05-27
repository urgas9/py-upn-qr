import qrcode
from qrcode.image.pil import PilImage


def generate_data_string():
    # 19 fields, control sum and reserve fields get populated/calculated automatically
    values = [
        "UPNQR",
        "",
        "",
        "",
        "",
        "Ime plačnika",
        "Ulica in št. plačnika",
        "Kraj plačnika",
        "11.23",  # znesek, 11 znakov
        "",
        "",
        "OTHR",  # Koda namena, 4 znaki
        "Namen plačila ",  # 42 znakov
        "26.7.2020",  # Rok placila, 10 znakov
        "IBAN",  # 34 znakov
        "Referenca prejemnika",  # 26 znakov
        "Ime prejemnika",  # 33 znakov
        "Ulica in št. prejemnika",  # 33 znakov
        "Kraj prejemnika",  # 33 znakov
    ]

    s = "\n".join(values)
    s = f"{s}\n"
    contr_sum = len(s)

    return f"{s}{contr_sum:03d}\n"


def generate_qr_code() -> PilImage:
    qr = qrcode.QRCode(
        version=15,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(generate_data_string())
    qr.make(fit=True)

    return qr.make_image(fill_color="black", back_color="white")
