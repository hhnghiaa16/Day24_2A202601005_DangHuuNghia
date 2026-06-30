from pathlib import Path
from typing import Any

import great_expectations as gx
import pandas as pd
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.expectations.expectation_configuration import (
    ExpectationConfiguration,
)

RAW_DATA_PATH = Path("data/raw/patients_raw.csv")
VALID_CONDITIONS = ["Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"]


def build_patient_expectation_suite() -> ExpectationSuite:
    """Create a Great Expectations suite for patient data."""
    context = gx.get_context()
    suite_name = "patient_data_suite"
    suite = ExpectationSuite(name=suite_name)

    expectations = [
        ("expect_column_values_to_not_be_null", {"column": "patient_id"}),
        ("expect_column_value_lengths_to_equal", {"column": "cccd", "value": 12}),
        (
            "expect_column_values_to_be_between",
            {"column": "ket_qua_xet_nghiem", "min_value": 0, "max_value": 50},
        ),
        (
            "expect_column_values_to_be_in_set",
            {"column": "benh", "value_set": VALID_CONDITIONS},
        ),
        (
            "expect_column_values_to_match_regex",
            {"column": "email", "regex": r"^[^@\s]+@[^@\s]+\.[^@\s]+$"},
        ),
        ("expect_column_values_to_be_unique", {"column": "patient_id"}),
    ]

    for expectation_type, kwargs in expectations:
        suite.add_expectation_configuration(
            ExpectationConfiguration(type=expectation_type, kwargs=kwargs)
        )

    if hasattr(context, "suites"):
        context.suites.add_or_update(suite)
    elif hasattr(context, "save_expectation_suite"):
        context.save_expectation_suite(suite)

    return suite


def _fail(results: dict[str, Any], message: str) -> None:
    results["success"] = False
    results["failed_checks"].append(message)


def validate_anonymized_data(filepath: str) -> dict:
    df = pd.read_csv(filepath, dtype={"cccd": str, "so_dien_thoai": str})
    results: dict[str, Any] = {
        "success": True,
        "failed_checks": [],
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns),
        },
    }

    if RAW_DATA_PATH.exists():
        raw_df = pd.read_csv(RAW_DATA_PATH, dtype={"cccd": str, "so_dien_thoai": str})

        if len(df) != len(raw_df):
            _fail(
                results,
                f"Row count mismatch: anonymized={len(df)}, raw={len(raw_df)}",
            )

        if "cccd" in df.columns and "cccd" in raw_df.columns:
            leaked_cccd = set(df["cccd"].astype(str)) & set(raw_df["cccd"].astype(str))
            if leaked_cccd:
                _fail(
                    results,
                    f"Found {len(leaked_cccd)} original CCCD values in anonymized data",
                )

        if "so_dien_thoai" in df.columns and "so_dien_thoai" in raw_df.columns:
            leaked_phone = set(df["so_dien_thoai"].astype(str)) & set(
                raw_df["so_dien_thoai"].astype(str)
            )
            if leaked_phone:
                _fail(
                    results,
                    f"Found {len(leaked_phone)} original phone values in anonymized data",
                )

    important_columns = ["patient_id", "benh", "ket_qua_xet_nghiem"]
    for column in important_columns:
        if column not in df.columns:
            _fail(results, f"Missing column: {column}")
        elif df[column].isna().any():
            _fail(results, f"Column has null values: {column}")

    if "patient_id" in df.columns and df["patient_id"].duplicated().any():
        _fail(results, "Duplicate patient_id values found")

    if "ket_qua_xet_nghiem" in df.columns:
        out_of_range = ~df["ket_qua_xet_nghiem"].between(0, 50)
        if out_of_range.any():
            _fail(results, "ket_qua_xet_nghiem contains values outside [0, 50]")

    if "benh" in df.columns:
        invalid_conditions = set(df["benh"].dropna()) - set(VALID_CONDITIONS)
        if invalid_conditions:
            _fail(results, f"Invalid benh values: {sorted(invalid_conditions)}")

    return results
