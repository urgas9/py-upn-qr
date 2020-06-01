import json
import locale
from datetime import datetime
from typing import Generator, List

from jsonschema import Draft4Validator, Draft7Validator, FormatChecker, ValidationError, validate, validators

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


class UPNQR:
    """
    Ime polja               |   Dolžina        |    Izpolnjevanje
    Ime plačnika            |   Max. 33        |    Obvezno, razen za plačila za humanitarne namene.
    Ulica in št. plačnika   |   Max. 33        |    Obvezno, razen za plačila za humanitarne namene.
    Kraj plačnika           |   Max. 33        |    Obvezno, razen za plačila za humanitarne namene.
    Znesek                  |   1 milijarda -1 |    Obvezno, razen za plačila za humanitarne namene.
                                                    Format »***#.##0,00«.
    Koda namena             |   Obvezno 4      |    Obvezno. Iz šifranta kod namena.
    Namen plačila           |   Max. 42        |    Obvezno.
    Rok plačila             |                  |    Poljubno. Format »DD.MM.LLLL« ali prazno.
    IBAN prejemnika         |                  |    Obvezno s pravilno kontrolno številko.
                                                    Format »SI56 9999 9999 9999 999«.
    Referenca prejemnika    |   Max 4 + 22     |    Obvezno (Model in Sklic).
                                                    Model in sklic sta vsak v svojem polju.
                                                    Dovoljen je model SI ali RF.
                                                    Formatiranje sklica po pravilih za formatiranje SI ali RF.
                                                    Pravilna kontrolna številka.
    Ime prejemnika          |   Max. 33        |    Obvezno.
    Ulica in št. prejemnika |   Max. 33        |    Obvezno.
    Kraj prejemnika         |   Max. 33        |    Obvezno.
    """

    placnik_ime: str
    placnik_ulica: str
    placnik_kraj: str
    znesek: str  # Format »***#.##0,00«.
    koda_namena: str
    namen_placila: str
    rok_placila: datetime  # Format »DD.MM.LLLL«
    prejemnik_iban: str
    prejemnik_referenca: str
    prejemnik_ime: str
    prejemnik_ulica: str
    prejemnik_kraj: str

    def from_dict(source: dict) -> "UPNQR":
        u = UPNQR()
        u.placnik_ime = source.get("placnik_ime")
        u.placnik_ulica = source.get("placnik_ulica")
        u.placnik_kraj = source.get("placnik_kraj")
        u.znesek = source.get("znesek")
        u.koda_namena = source.get("koda_namena")
        u.namen_placila = source.get("namen_placila")
        u.rok_placila = source.get("rok_placila")
        u.prejemnik_iban = source.get("prejemnik_iban")
        u.prejemnik_referenca = source.get("prejemnik_referenca")
        u.prejemnik_ime = source.get("prejemnik_ime")
        u.prejemnik_ulica = source.get("prejemnik_ulica")
        u.prejemnik_kraj = source.get("prejemnik_kraj")
        return u

    def validate_fields(self, source: dict) -> Generator[ValidationError]:
        with open("upn-qr-schema.json") as f:
            json_schema = json.load(f)

        # Create a new format checker instance.
        format_checker = FormatChecker()

        # Register a new format checker method for format ‘date-slo’
        @format_checker.checks("date-slo")
        def date_slo_formatter(value: str) -> bool:
            try:
                datetime.strptime(value, '%d.%m.%Y')
                return True
            except ValueError:
                return False

        # Register a new format checker method for format ‘amount-slo’
        @format_checker.checks("amount-slo")
        def amount_slo_formatter(value: str) -> bool:
            if value is None:
                return False

            split_num = value.split(",")
            # There are more than 2 decimal commas
            if len(split_num) > 2:
                return False
            # Check that the number of decimal places equals to 2 and are all digits
            if len(split_num) == 2 and (len(split_num[1]) != 2 or not split_num[1].isdigit()):
                return False

            # Check that the whole part of the number does not contain any non-digit chars
            return split_num[0].replace(".", "").isdigit()

        # Create a new validator class
        custom_validator = validators.create(
            meta_schema=Draft7Validator.META_SCHEMA,
        )
        # Create a new instance of your custom validator. Add a custom type.
        my_validator = custom_validator(
            json_schema, format_checker=format_checker,
        )
        return my_validator.iter_errors(source)


js = {
    "namen_placila": "2",
    "prejemnik_kraj": "123",
    "prejemnik_ime": "Ala",
    "prejemnik_ulica": "Bla",
    "prejemnik_iban": "Bla",
    "prejemnik_referenca": "Bla",
    "rok_placila": "12.12.2020",
    "znesek": "213.123,23",
    "koda_namena": "2345",
}
u = UPNQR.from_dict(js)
print(js)
print(u.validate_fields(js))
