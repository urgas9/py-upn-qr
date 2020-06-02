import json
from datetime import datetime
from typing import Any, Generator

import qrcode
from jsonschema import Draft7Validator, FormatChecker, ValidationError, validators
from qrcode.image.pil import PilImage


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
    _source_dict: dict = None
    placnik_ime: str = None
    placnik_ulica: str = None
    placnik_kraj: str = None
    znesek: str = None
    koda_namena: str = None
    namen_placila: str = None
    rok_placila: str = None
    prejemnik_iban: str = None
    prejemnik_referenca: str = None
    prejemnik_ime: str = None
    prejemnik_ulica: str = None
    prejemnik_kraj: str = None

    def __init__(self, **kwargs) -> None:
        for k in kwargs:
            setattr(self, k, kwargs[k])

    @staticmethod
    def from_dict(source: dict) -> "UPNQR":
        upnqr = UPNQR(**source)
        upnqr._source_dict = source
        return upnqr

    def validate_fields(self) -> Generator[ValidationError, Any, None]:
        with open("upn_qr_schema.json") as f:
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
            validators=Draft7Validator.VALIDATORS,
        )
        # Create a new instance of your custom validator. Add a custom type.
        my_validator = custom_validator(
            json_schema, format_checker=format_checker,
        )
        return my_validator.iter_errors(self._source_dict)

    def make_qr_code(self) -> PilImage:
        qr = qrcode.QRCode(
            version=15,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(self._qr_data_string())
        qr.make(fit=True)

        return qr.make_image(fill_color="black", back_color="white")

    def _qr_data_string(self) -> str:

        def formatted_znesek() -> str:
            result = f"{self.znesek}00" if "," not in self.znesek else self.znesek
            cleaned_result = result.replace(",", "").replace(".", "")
            return cleaned_result.zfill(11)

        def remove_whitespaces(value: str) -> str:
            return value.replace(" ", "")

        # 19 fields, control sum and reserve fields get populated/calculated automatically
        values = [
            "UPNQR",
            "",
            "",
            "",
            "",
            self.placnik_ime,
            self.placnik_ulica,
            self.placnik_kraj,
            formatted_znesek(),
            "",
            "",
            self.koda_namena,
            self.namen_placila,
            self.rok_placila,
            remove_whitespaces(self.prejemnik_iban),
            remove_whitespaces(self.prejemnik_referenca),
            self.prejemnik_ime,
            self.prejemnik_ulica,
            self.prejemnik_kraj,
        ]
        # Keep all values as strings - replace Nones with empty string
        values = [v if v is not None else "" for v in values]
        s = "\n".join(values)
        s = f"{s}\n"
        contr_sum = len(s)

        return f"{s}{contr_sum:03d}\n"
