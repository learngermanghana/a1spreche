from datetime import UTC
import pandas as pd

from datetime import UTC
import pandas as pd

from src.services.contracts import contract_active


def test_contract_inactive_when_expired():
    df = pd.DataFrame([{"StudentCode": "abc", "ContractEnd": "2020-01-01"}])
    assert contract_active("abc", df) is False


def test_contract_lookup_ignores_case_and_whitespace():
    df = pd.DataFrame(
        [
            {
                "StudentCode": " AbC ",
                "ContractEnd": "2020-01-01",
            }
        ]
    )
    assert contract_active("abc", df) is False


def test_contract_inactive_when_balance_over_30_days():
    start = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=40)).strftime("%Y-%m-%d")
    end = (pd.Timestamp.now(tz="UTC") + pd.Timedelta(days=20)).strftime("%Y-%m-%d")
    df = pd.DataFrame(
        [
            {
                "StudentCode": "abc",
                "ContractStart": start,
                "ContractEnd": end,
                "Balance": 10,
            }
        ]
    )
    assert contract_active("abc", df) is False


def test_balance_string_with_comma_blocks_login():
    start = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=35)).strftime("%Y-%m-%d")
    end = (pd.Timestamp.now(tz="UTC") + pd.Timedelta(days=10)).strftime("%Y-%m-%d")
    df = pd.DataFrame(
        [
            {
                "StudentCode": "abc",
                "ContractStart": start,
                "ContractEnd": end,
                "Balance": "1,000",
            }
        ]
    )
    assert contract_active("abc", df) is False
