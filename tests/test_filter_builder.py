# tests/test_filter_builder.py
"""
Unit tests for easy_acumatica.models.filter_builder, using the
operator-overloaded Filter class and F factory.
"""

from easy_acumatica.models.filter_builder import F

# ---------------------------------------------------------------------------
# Basic Comparison and Logical Operators
# ---------------------------------------------------------------------------
def test_comparison_operators():
    """Tests eq, ne, gt, ge, lt, le operators."""
    assert (F.Name == "O'Neil").build() == "(Name eq 'O''Neil')"
    assert (F.Status != "Inactive").build() == "(Status ne 'Inactive')"
    assert (F.Amount > 100).build() == "(Amount gt 100)"
    assert (F.Amount >= 100).build() == "(Amount ge 100)"
    assert (F.Amount < 200).build() == "(Amount lt 200)"
    assert (F.Amount <= 200).build() == "(Amount le 200)"

def test_logical_operators():
    """Tests and, or, not operators using &, |, ~."""
    f1 = F.Status == "Active"
    f2 = F.IsBillable == True

    # Test AND operator
    assert (f1 & f2).build() == "((Status eq 'Active') and (IsBillable eq true))"

    # Test OR operator
    assert (f1 | f2).build() == "((Status eq 'Active') or (IsBillable eq true))"

    # Test NOT operator
    assert (~f1).build() == "not ((Status eq 'Active'))"

    # Test complex combination with parentheses
    f3 = F.Amount > 1000
    complex_filter = (f1 & f2) | ~f3
    assert complex_filter.build() == "(((Status eq 'Active') and (IsBillable eq true)) or not ((Amount gt 1000)))"

# ---------------------------------------------------------------------------
# Arithmetic and Math Functions
# ---------------------------------------------------------------------------
def test_arithmetic_operators():
    """Tests add, sub, mul, div, mod operators using +, -, *, /, %."""
    # Test a chain of operations, respecting parentheses for precedence
    expr = ((((F.Price + 5) - 2) * 3) / 4) % 2
    expected = "(((((Price add 5) sub 2) mul 3) div 4) mod 2)"
    assert expr.build() == expected

    # Test right-hand-side operations
    expr = 100 - F.Price
    assert expr.build() == "(100 sub Price)"

def test_math_functions():
    """Tests round, floor, and ceiling functions."""
    assert F.Freight.round().build() == "round(Freight)"
    assert F.Freight.floor().build() == "floor(Freight)"
    assert F.Freight.ceiling().build() == "ceiling(Freight)"

# ---------------------------------------------------------------------------
# Date Functions
# ---------------------------------------------------------------------------
def test_date_functions():
    """Tests day, month, year, hour, minute, and second functions."""
    assert F.BirthDate.day().build() == "day(BirthDate)"
    assert F.BirthDate.month().build() == "month(BirthDate)"
    assert F.BirthDate.year().build() == "year(BirthDate)"
    assert F.BirthDate.hour().build() == "hour(BirthDate)"
    assert F.BirthDate.minute().build() == "minute(BirthDate)"
    assert F.BirthDate.second().build() == "second(BirthDate)"


# ---------------------------------------------------------------------------
# String Functions
# ---------------------------------------------------------------------------
def test_string_functions():
    """Tests all OData string manipulation functions."""
    # Basic functions
    assert F.Description.contains("sale").build() == "substringof('sale', Description)"
    assert F.SKU.startswith("PRO").build() == "startswith(SKU,'PRO')"
    assert F.FileName.endswith(".pdf").build() == "endswith(FileName,'.pdf')"
    assert F.Name.tolower().build() == "tolower(Name)"
    assert F.Name.toupper().build() == "toupper(Name)"
    assert F.Comment.trim().build() == "trim(Comment)"
    assert F.Description.length().build() == "length(Description)"

    # Functions with arguments
    assert F.Path.indexof("/").build() == "indexof(Path,'/')"
    assert F.Name.replace(" ", "_").build() == "replace(Name,' ','_')"
    assert F.City.concat(", USA").build() == "concat(City,', USA')"

    # Substring
    assert F.Title.substring(5).build() == "substring(Title,5)"
    assert F.Title.substring(0, 10).build() == "substring(Title,0,10)"

# ---------------------------------------------------------------------------
# Composition and Advanced Usage
# ---------------------------------------------------------------------------
def test_filter_composition():
    """Tests creating filters from other filter expressions."""
    unit_cost = F.ExtendedCost / F.Quantity
    is_profitable = F.SalePrice > unit_cost
    assert is_profitable.build() == "(SalePrice gt (ExtendedCost div Quantity))"

def test_custom_field_helper():
    """Tests the F.cf() helper for custom fields."""
    custom_field_filter = F.cf("String", "ItemSettings", "UsrRepairType") == "Battery"
    expected = "(cf.String(f='ItemSettings.UsrRepairType') eq 'Battery')"
    assert custom_field_filter.build() == expected
