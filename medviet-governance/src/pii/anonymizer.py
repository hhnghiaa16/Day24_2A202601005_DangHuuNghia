import pandas as pd
from faker import Faker
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from .detector import SUPPORTED_ENTITIES, build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")


def fake_cccd() -> str:
    return fake.numerify("############")


def fake_phone() -> str:
    prefix = fake.random_element(elements=("03", "05", "07", "08", "09"))
    return f"{prefix}{fake.numerify('########')}"


class MedVietAnonymizer:
    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()
        self.anonymizer = AnonymizerEngine()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        text = "" if text is None else str(text)
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        if strategy == "replace":
            operators = {
                "PERSON": OperatorConfig("replace", {"new_value": fake.name()}),
                "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": fake.email()}),
                "VN_CCCD": OperatorConfig("replace", {"new_value": fake_cccd()}),
                "VN_PHONE": OperatorConfig("replace", {"new_value": fake_phone()}),
            }
        elif strategy == "mask":
            operators = {
                entity: OperatorConfig(
                    "mask",
                    {"masking_char": "*", "chars_to_mask": 100, "from_end": False},
                )
                for entity in SUPPORTED_ENTITIES
            }
        elif strategy == "hash":
            operators = {
                entity: OperatorConfig("hash", {"hash_type": "sha256"})
                for entity in SUPPORTED_ENTITIES
            }
        else:
            raise ValueError(f"Unknown anonymization strategy: {strategy}")

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators,
        )
        return anonymized.text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df_anon = df.copy()
        row_count = len(df_anon)

        if "ho_ten" in df_anon.columns:
            df_anon["ho_ten"] = [fake.name() for _ in range(row_count)]
        if "cccd" in df_anon.columns:
            df_anon["cccd"] = [fake_cccd() for _ in range(row_count)]
        if "so_dien_thoai" in df_anon.columns:
            df_anon["so_dien_thoai"] = [fake_phone() for _ in range(row_count)]
        if "email" in df_anon.columns:
            df_anon["email"] = [fake.email() for _ in range(row_count)]
        if "dia_chi" in df_anon.columns:
            df_anon["dia_chi"] = [
                fake.address().replace("\n", ", ") for _ in range(row_count)
            ]
        if "bac_si_phu_trach" in df_anon.columns:
            df_anon["bac_si_phu_trach"] = [fake.name() for _ in range(row_count)]

        return df_anon

    def calculate_detection_rate(
        self,
        original_df: pd.DataFrame,
        pii_columns: list,
    ) -> float:
        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col].astype(str):
                total += 1
                results = detect_pii(value, self.analyzer)
                if len(results) > 0:
                    detected += 1

        return detected / total if total > 0 else 0.0
