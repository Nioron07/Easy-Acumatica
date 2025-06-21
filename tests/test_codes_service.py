# tests/test_codes_service.py

import pytest

from easy_acumatica import AcumaticaClient
from easy_acumatica.models.code_builder import (
    DeductionBenefitCodeBuilder,
    EarningTypeCodeBuilder,
    PayrollWCCCodeBuilder,
)

API_VERSION = "24.200.001"
BASE = "https://fake"
LOGIN_URL = f"{BASE}/entity/auth/login"
LOGOUT_URL = f"{BASE}/entity/auth/logout"
DEDUCTION_URL = f"{BASE}/entity/Default/{API_VERSION}/DeductionBenefitCode"
EARNING_URL   = f"{BASE}/entity/Default/{API_VERSION}/EarningTypeCode"
WCC_URL       = f"{BASE}/entity/Default/{API_VERSION}/PayrollWCCCode"


@pytest.fixture
def client(requests_mock):
    # stub login/logout per call
    requests_mock.post(LOGIN_URL, status_code=204)
    requests_mock.post(LOGOUT_URL, status_code=204)
    return AcumaticaClient(
        base_url=BASE,
        username="user",
        password="pass",
        tenant="T",
        branch="B",
        verify_ssl=False,
        persistent_login=False,
    )


# ---------------------------------------------------------------------------
# DeductionBenefitCode
# ---------------------------------------------------------------------------

def test_create_deduction_benefit_code_success(requests_mock, client):
    builder = (
        DeductionBenefitCodeBuilder()
        .code_id("TST")
        .description("Test deduction")
        .contribution_type("DED")
        .active(False)
        .associated_with("Employee Settings")
        .employee_deduction(calculation_method="GRS", percent=20, applicable_earnings="TOT")
        .gl_accounts(deduction_liability_account="20000", deduction_liability_sub="000000")
    )
    expected = {"DeductionBenefitCodeID": {"value": "TST"}}
    requests_mock.put(DEDUCTION_URL, status_code=200, json=expected)

    result = client.codes.create_deduction_benefit_code(API_VERSION, builder)
    assert result == expected

    # find only the PUT to our endpoint (ignore login/logout)
    puts = [
        req for req in requests_mock.request_history
        if req.method == "PUT" and req.url == DEDUCTION_URL
    ]
    assert puts, "No PUT to DeductionBenefitCode endpoint"
    last = puts[-1]
    assert last.json() == builder.build()


@pytest.mark.parametrize("status_code", [400, 422, 500])
def test_create_deduction_benefit_code_error(requests_mock, client, status_code):
    builder = DeductionBenefitCodeBuilder().code_id("X")
    requests_mock.put(DEDUCTION_URL, status_code=status_code, json={"error": "oops"})

    with pytest.raises(RuntimeError) as exc:
        client.codes.create_deduction_benefit_code(API_VERSION, builder)
    assert "oops" in str(exc.value)


# ---------------------------------------------------------------------------
# EarningTypeCode
# ---------------------------------------------------------------------------

def test_create_earning_type_code_success(requests_mock, client):
    builder = (
        EarningTypeCodeBuilder()
        .code_id("ET1")
        .description("Overtime")
        .category("Wage")
        .accrue_time_off(True)
        .active(True)
    )
    expected = {"EarningTypeCodeID": {"value": "ET1"}}
    requests_mock.put(EARNING_URL, status_code=200, json=expected)

    result = client.codes.create_earning_type_code(API_VERSION, builder)
    assert result == expected

    puts = [
        req for req in requests_mock.request_history
        if req.method == "PUT" and req.url == EARNING_URL
    ]
    assert puts, "No PUT to EarningTypeCode endpoint"
    last = puts[-1]
    assert last.json() == builder.build()


@pytest.mark.parametrize("status_code", [400, 422, 500])
def test_create_earning_type_code_error(requests_mock, client, status_code):
    builder = EarningTypeCodeBuilder().code_id("E")
    requests_mock.put(EARNING_URL, status_code=status_code, json={"message": "bad"})

    with pytest.raises(RuntimeError) as exc:
        client.codes.create_earning_type_code(API_VERSION, builder)
    assert "bad" in str(exc.value)


# ---------------------------------------------------------------------------
# PayrollWCCCode
# ---------------------------------------------------------------------------

def test_create_payroll_wcc_code_success(requests_mock, client):
    builder = (
        PayrollWCCCodeBuilder()
        .country("US")
        .add_wcc_code("2222", "Test Code", active=True)
    )
    expected = {"Country": {"value": "US"}, "WCCCodes": [{"WCCCode": {"value": "2222"}, "Description": {"value": "Test Code"}, "Active": {"value": True}}]}
    requests_mock.put(WCC_URL, status_code=200, json=expected)

    result = client.codes.create_payroll_wcc_code(API_VERSION, builder)
    assert result == expected

    puts = [
        req for req in requests_mock.request_history
        if req.method == "PUT" and req.url == WCC_URL
    ]
    assert puts, "No PUT to PayrollWCCCode endpoint"
    last = puts[-1]
    assert last.json() == builder.build()


@pytest.mark.parametrize("status_code", [400, 422, 500])
def test_create_payroll_wcc_code_error(requests_mock, client, status_code):
    builder = PayrollWCCCodeBuilder().country("CA").add_wcc_code("1111", "Desc")
    requests_mock.put(WCC_URL, status_code=status_code, json={"error": "fail"})

    with pytest.raises(RuntimeError) as exc:
        client.codes.create_payroll_wcc_code(API_VERSION, builder)
    assert "fail" in str(exc.value)
