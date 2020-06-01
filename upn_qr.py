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

    def __init__(self, placnik_ime: str, placnik_ulica: str, placnik_kraj: str, znesek: str, koda_namena: str,
                 namen_placila: str, rok_placila: str, prejemnik_iban: str, prejemnik_referenca: str,
                 prejemnik_ime: str, prejemnik_ulica: str, prejemnik_kraj: str):
        self.placnik_ime = placnik_ime
        self.placnik_ulica = placnik_ulica
        self.placnik_kraj = placnik_kraj
        self.znesek = znesek
        self.koda_namena = koda_namena
        self.namen_placila = namen_placila
        self.rok_placila = rok_placila
        self.prejemnik_iban = prejemnik_iban
        self.prejemnik_referenca = prejemnik_referenca
        self.prejemnik_ime = prejemnik_ime
        self.prejemnik_ulica = prejemnik_ulica
        self.prejemnik_kraj = prejemnik_kraj

    @staticmethod
    def from_dict(source: dict) -> "UPNQR":
        return UPNQR(
            placnik_ime=source.get("placnik_ime"),
            placnik_ulica=source.get("placnik_ulica"),
            placnik_kraj=source.get("placnik_kraj"),
            znesek=source.get("znesek"),
            koda_namena=source.get("koda_namena"),
            namen_placila=source.get("namen_placila"),
            rok_placila=source.get("rok_placila"),
            prejemnik_iban=source.get("prejemnik_iban"),
            prejemnik_referenca=source.get("prejemnik_referenca"),
            prejemnik_ime=source.get("prejemnik_ime"),
            prejemnik_ulica=source.get("prejemnik_ulica"),
            prejemnik_kraj=source.get("prejemnik_kraj"),
        )
        znesek

    @staticmethod
    def validate_fields(source: dict) -> Generator[ValidationError, Any, None]:
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
        return my_validator.iter_errors(source)

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

    def _qr_data_string(self):

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
