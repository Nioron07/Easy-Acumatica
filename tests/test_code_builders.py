# tests/test_code_builders.py

from easy_acumatica.models.code_builder import (
    DeductionBenefitCodeBuilder,
    EarningTypeCodeBuilder,
    PayrollWCCCodeBuilder,
)


# ---------------------------------------------------------------------------
# DeductionBenefitCodeBuilder
# ---------------------------------------------------------------------------
def test_deduction_builder_all_fields():
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
    payload = builder.build()
    assert payload == {
        "DeductionBenefitCodeID": {"value": "TST"},
        "Description": {"value": "Test deduction"},
        "ContributionType": {"value": "DED"},
        "Active": {"value": False},
        "AssociatedWith": {"value": "Employee Settings"},
        "EmployeeDeduction": {
            "CalculationMethod": {"value": "GRS"},
            "Percent": {"value": 20},
            "ApplicableEarnings": {"value": "TOT"},
        },
        "GLAccounts": {
            "DeductionLiabilityAccount": {"value": "20000"},
            "DeductionLiabilitySub": {"value": "000000"},
        },
    }


def test_deduction_builder_partial_optional_fields():
    # only set some optional sub-fields
    builder = (
        DeductionBenefitCodeBuilder()
        .code_id("X")
        .employee_deduction(percent=5)
        .gl_accounts(deduction_liability_account="30000")
    )
    payload = builder.build()
    # Required code_id must appear
    assert payload["DeductionBenefitCodeID"] == {"value": "X"}
    # employee_deduction only contains Percent
    assert payload["EmployeeDeduction"] == {"Percent": {"value": 5}}
    # GLAccounts only contains DeductionLiabilityAccount
    assert payload["GLAccounts"] == {"DeductionLiabilityAccount": {"value": "30000"}}


def test_deduction_builder_build_returns_fresh_copy():
    builder = DeductionBenefitCodeBuilder().code_id("A")
    first = builder.build()
    # mutate returned payload
    first["DeductionBenefitCodeID"]["value"] = "mutated"
    second = builder.build()
    # original builder state must not have been changed
    assert second["DeductionBenefitCodeID"]["value"] == "A"


# ---------------------------------------------------------------------------
# EarningTypeCodeBuilder
# ---------------------------------------------------------------------------
def test_earning_type_builder_and_payload():
    builder = (
        EarningTypeCodeBuilder()
        .code_id("E1")
        .description("Earn code")
        .category("Wage")
        .accrue_time_off(True)
        .active(True)
    )
    payload = builder.build()
    assert payload == {
        "EarningTypeCodeID": {"value": "E1"},
        "Description": {"value": "Earn code"},
        "Category": {"value": "Wage"},
        "AccrueTimeOff": {"value": True},
        "Active": {"value": True},
    }


def test_earning_type_builder_build_returns_fresh_copy():
    builder = EarningTypeCodeBuilder().code_id("Z")
    first = builder.build()
    first["EarningTypeCodeID"]["value"] = "changed"
    second = builder.build()
    assert second["EarningTypeCodeID"]["value"] == "Z"


# ---------------------------------------------------------------------------
# PayrollWCCCodeBuilder
# ---------------------------------------------------------------------------
def test_payroll_wcc_builder_single_entry():
    builder = (
        PayrollWCCCodeBuilder()
        .country("US")
        .add_wcc_code("2222", "Test Code", active=False)
    )
    payload = builder.build()
    assert payload == {
        "Country": {"value": "US"},
        "WCCCodes": [
            {
                "WCCCode": {"value": "2222"},
                "Description": {"value": "Test Code"},
                "Active": {"value": False},
            }
        ],
    }


def test_payroll_wcc_builder_multiple_entries():
    builder = (
        PayrollWCCCodeBuilder()
        .country("CA")
        .add_wcc_code("1111", "Code One", active=True)
        .add_wcc_code("2222", "Code Two", active=False)
    )
    payload = builder.build()
    assert payload["Country"] == {"value": "CA"}
    assert len(payload["WCCCodes"]) == 2
    # verify entries individually
    assert payload["WCCCodes"][0] == {
        "WCCCode": {"value": "1111"},
        "Description": {"value": "Code One"},
        "Active": {"value": True},
    }
    assert payload["WCCCodes"][1] == {
        "WCCCode": {"value": "2222"},
        "Description": {"value": "Code Two"},
        "Active": {"value": False},
    }


def test_payroll_wcc_builder_build_returns_fresh_copy():
    builder = PayrollWCCCodeBuilder().country("MX").add_wcc_code("3333", "CopyTest")
    first = builder.build()
    # mutate nested list entry
    first["WCCCodes"][0]["Description"]["value"] = "Mutated"
    second = builder.build()
    # second build must preserve original
    assert second["WCCCodes"][0]["Description"]["value"] == "CopyTest"
