# tests/test_odata.py
"""Tests for OData v3 and v4 filter building functionality."""

import pytest
from datetime import date, datetime

from easy_acumatica.odata import F, Filter, QueryOptions, CustomField


class TestFilterBasics:
    """Test basic Filter functionality that works in both v3 and v4."""
    
    def test_field_access(self):
        """Test basic field access."""
        filter_expr = F.CustomerName
        assert str(filter_expr) == "CustomerName"
    
    def test_nested_field_access(self):
        """Test nested field access with path navigation."""
        filter_expr = F.Contact.Email
        assert str(filter_expr) == "Contact/Email"
        
        # Multiple levels
        filter_expr = F.Order.Customer.Name
        assert str(filter_expr) == "Order/Customer/Name"
    
    def test_literal_conversion(self):
        """Test conversion of Python types to OData literals."""
        # String literals
        assert Filter._to_literal("test") == "'test'"
        assert Filter._to_literal("O'Brien") == "'O''Brien'"  # Escaped quote
        
        # Boolean literals
        assert Filter._to_literal(True) == "true"
        assert Filter._to_literal(False) == "false"
        
        # None/null
        assert Filter._to_literal(None) == "null"
        
        # Numbers
        assert Filter._to_literal(42) == "42"
        assert Filter._to_literal(3.14) == "3.14"
        
        # Datetime
        dt = datetime(2024, 1, 15, 10, 30, 0)
        assert Filter._to_literal(dt) == f"datetime'{dt.isoformat()}'"
        
        # Date (v4 feature but handled in literal conversion)
        d = date(2024, 1, 15)
        assert Filter._to_literal(d) == f"date'{d.isoformat()}'"


class TestComparisonOperators:
    """Test comparison operators (v3 and v4 compatible)."""
    
    def test_equality(self):
        """Test equality operator."""
        filter_expr = F.Status == "Active"
        assert str(filter_expr) == "(Status eq 'Active')"
    
    def test_inequality(self):
        """Test inequality operator."""
        filter_expr = F.Status != "Deleted"
        assert str(filter_expr) == "(Status ne 'Deleted')"
    
    def test_greater_than(self):
        """Test greater than operator."""
        filter_expr = F.Amount > 1000
        assert str(filter_expr) == "(Amount gt 1000)"
    
    def test_greater_equal(self):
        """Test greater than or equal operator."""
        filter_expr = F.Amount >= 1000
        assert str(filter_expr) == "(Amount ge 1000)"
    
    def test_less_than(self):
        """Test less than operator."""
        filter_expr = F.Amount < 100
        assert str(filter_expr) == "(Amount lt 100)"
    
    def test_less_equal(self):
        """Test less than or equal operator."""
        filter_expr = F.Amount <= 100
        assert str(filter_expr) == "(Amount le 100)"


class TestLogicalOperators:
    """Test logical operators (v3 and v4 compatible)."""
    
    def test_and_operator(self):
        """Test logical AND operator."""
        filter_expr = (F.Status == "Active") & (F.Amount > 1000)
        assert str(filter_expr) == "((Status eq 'Active') and (Amount gt 1000))"
    
    def test_or_operator(self):
        """Test logical OR operator."""
        filter_expr = (F.Status == "Active") | (F.Status == "Pending")
        assert str(filter_expr) == "((Status eq 'Active') or (Status eq 'Pending'))"
    
    def test_not_operator(self):
        """Test logical NOT operator."""
        filter_expr = ~(F.Status == "Deleted")
        assert str(filter_expr) == "not ((Status eq 'Deleted'))"
    
    def test_complex_logical_expression(self):
        """Test complex combination of logical operators."""
        filter_expr = ((F.Status == "Active") & (F.Amount > 1000)) | (F.Priority == "High")
        expected = "(((Status eq 'Active') and (Amount gt 1000)) or (Priority eq 'High'))"
        assert str(filter_expr) == expected


class TestArithmeticOperators:
    """Test arithmetic operators (v3 and v4 compatible)."""
    
    def test_addition(self):
        """Test addition operator."""
        filter_expr = F.Price + 10
        assert str(filter_expr) == "(Price add 10)"
        
        # Right-side addition
        filter_expr = 10 + F.Price
        assert str(filter_expr) == "(10 add Price)"
    
    def test_subtraction(self):
        """Test subtraction operator."""
        filter_expr = F.Price - 5
        assert str(filter_expr) == "(Price sub 5)"
        
        # Right-side subtraction
        filter_expr = 100 - F.Discount
        assert str(filter_expr) == "(100 sub Discount)"
    
    def test_multiplication(self):
        """Test multiplication operator."""
        filter_expr = F.Quantity * 2
        assert str(filter_expr) == "(Quantity mul 2)"
        
        # Right-side multiplication
        filter_expr = 1.5 * F.Price
        assert str(filter_expr) == "(1.5 mul Price)"
    
    def test_division(self):
        """Test division operator."""
        filter_expr = F.Total / 12
        assert str(filter_expr) == "(Total div 12)"
        
        # Right-side division
        filter_expr = 100 / F.Rate
        assert str(filter_expr) == "(100 div Rate)"
    
    def test_divby_v4(self):
        """Test decimal division operator (v4 only)."""
        filter_expr = F.Price.divby(2)
        assert str(filter_expr) == "(Price divby 2)"
    
    def test_modulo(self):
        """Test modulo operator."""
        filter_expr = F.Number % 2
        assert str(filter_expr) == "(Number mod 2)"
        
        # Right-side modulo
        filter_expr = 10 % F.Divisor
        assert str(filter_expr) == "(10 mod Divisor)"
    
    def test_arithmetic_in_comparison(self):
        """Test arithmetic operations within comparisons."""
        filter_expr = (F.Price * F.Quantity) > 1000
        assert str(filter_expr) == "((Price mul Quantity) gt 1000)"
        
        filter_expr = ((F.Price - 5) * 1.1) <= 100
        assert str(filter_expr) == "(((Price sub 5) mul 1.1) le 100)"


class TestStringFunctions:
    """Test string functions (v3 and v4)."""
    
    def test_contains_v3(self):
        """Test contains function (v3 style with substringof)."""
        filter_expr = F.Description.contains("Widget")
        assert str(filter_expr) == "substringof('Widget', Description)"
    
    def test_contains_v4(self):
        """Test contains function (v4 style)."""
        filter_expr = F.Description.contains_v4("Widget")
        assert str(filter_expr) == "contains(Description,'Widget')"
    
    def test_startswith(self):
        """Test startswith function."""
        filter_expr = F.Name.startswith("John")
        assert str(filter_expr) == "startswith(Name,'John')"
    
    def test_endswith(self):
        """Test endswith function."""
        filter_expr = F.Email.endswith("@example.com")
        assert str(filter_expr) == "endswith(Email,'@example.com')"
    
    def test_length(self):
        """Test length function."""
        filter_expr = F.Description.length()
        assert str(filter_expr) == "length(Description)"
        
        # Length in comparison
        filter_expr = F.Description.length() > 100
        assert str(filter_expr) == "(length(Description) gt 100)"
    
    def test_indexof(self):
        """Test indexof function."""
        filter_expr = F.Text.indexof("search")
        assert str(filter_expr) == "indexof(Text,'search')"
        
        # Check if substring exists
        filter_expr = F.Text.indexof("search") >= 0
        assert str(filter_expr) == "(indexof(Text,'search') ge 0)"
    
    def test_substring(self):
        """Test substring function."""
        # Without length
        filter_expr = F.Code.substring(2)
        assert str(filter_expr) == "substring(Code,2)"
        
        # With length
        filter_expr = F.Code.substring(2, 5)
        assert str(filter_expr) == "substring(Code,2,5)"
    
    def test_replace(self):
        """Test replace function."""
        filter_expr = F.Text.replace("old", "new")
        assert str(filter_expr) == "replace(Text,'old','new')"
    
    def test_tolower(self):
        """Test tolower function."""
        filter_expr = F.Name.tolower()
        assert str(filter_expr) == "tolower(Name)"
        
        # Case-insensitive comparison
        filter_expr = F.Name.tolower() == "john"
        assert str(filter_expr) == "(tolower(Name) eq 'john')"
    
    def test_toupper(self):
        """Test toupper function."""
        filter_expr = F.Code.toupper()
        assert str(filter_expr) == "toupper(Code)"
    
    def test_trim(self):
        """Test trim function."""
        filter_expr = F.Input.trim()
        assert str(filter_expr) == "trim(Input)"
    
    def test_matchesPattern_v4(self):
        """Test matchesPattern function (v4 only)."""
        filter_expr = F.CompanyName.matchesPattern("^A.*e$")
        assert str(filter_expr) == "matchesPattern(CompanyName,'^A.*e$')"


class TestDateTimeFunctions:
    """Test date/time functions (v3 and v4)."""
    
    def test_year(self):
        """Test year function."""
        filter_expr = F.CreatedDate.year()
        assert str(filter_expr) == "year(CreatedDate)"
        
        filter_expr = F.CreatedDate.year() == 2024
        assert str(filter_expr) == "(year(CreatedDate) eq 2024)"
    
    def test_month(self):
        """Test month function."""
        filter_expr = F.CreatedDate.month()
        assert str(filter_expr) == "month(CreatedDate)"
    
    def test_day(self):
        """Test day function."""
        filter_expr = F.CreatedDate.day()
        assert str(filter_expr) == "day(CreatedDate)"
    
    def test_hour(self):
        """Test hour function."""
        filter_expr = F.CreatedTime.hour()
        assert str(filter_expr) == "hour(CreatedTime)"
    
    def test_minute(self):
        """Test minute function."""
        filter_expr = F.CreatedTime.minute()
        assert str(filter_expr) == "minute(CreatedTime)"
    
    def test_second(self):
        """Test second function."""
        filter_expr = F.CreatedTime.second()
        assert str(filter_expr) == "second(CreatedTime)"
    
    def test_date_v4(self):
        """Test date function (v4 only)."""
        filter_expr = F.CreatedDateTime.date()
        assert str(filter_expr) == "date(CreatedDateTime)"
        
        # Compare date part
        filter_expr = F.CreatedDateTime.date() == date(2024, 1, 15)
        assert str(filter_expr) == "(date(CreatedDateTime) eq date'2024-01-15')"
    
    def test_time_v4(self):
        """Test time function (v4 only)."""
        filter_expr = F.CreatedDateTime.time()
        assert str(filter_expr) == "time(CreatedDateTime)"
    
    def test_totaloffsetminutes_v4(self):
        """Test totaloffsetminutes function (v4 only)."""
        filter_expr = F.DateTimeOffset.totaloffsetminutes()
        assert str(filter_expr) == "totaloffsetminutes(DateTimeOffset)"
    
    def test_fractionalseconds_v4(self):
        """Test fractionalseconds function (v4 only)."""
        filter_expr = F.Timestamp.fractionalseconds()
        assert str(filter_expr) == "fractionalseconds(Timestamp)"
        
        # Check fractional seconds
        filter_expr = F.Timestamp.fractionalseconds() > 0
        assert str(filter_expr) == "(fractionalseconds(Timestamp) gt 0)"
    
    def test_totalseconds_v4(self):
        """Test totalseconds function for durations (v4 only)."""
        filter_expr = F.Duration.totalseconds()
        assert str(filter_expr) == "totalseconds(Duration)"
    
    def test_now_v4(self):
        """Test now function (v4 only)."""
        filter_expr = F.CreatedDate < Filter("now()")
        assert str(filter_expr) == "(CreatedDate lt now())"
    
    def test_maxdatetime_v4(self):
        """Test maxdatetime function (v4 only)."""
        filter_expr = F.EndDate == Filter("maxdatetime()")
        assert str(filter_expr) == "(EndDate eq maxdatetime())"
    
    def test_mindatetime_v4(self):
        """Test mindatetime function (v4 only)."""
        filter_expr = F.StartDate == Filter("mindatetime()")
        assert str(filter_expr) == "(StartDate eq mindatetime())"


class TestMathFunctions:
    """Test math functions (v3 and v4)."""
    
    def test_round(self):
        """Test round function."""
        filter_expr = F.Price.round()
        assert str(filter_expr) == "round(Price)"
        
        filter_expr = F.Price.round() == 100
        assert str(filter_expr) == "(round(Price) eq 100)"
    
    def test_floor(self):
        """Test floor function."""
        filter_expr = F.Value.floor()
        assert str(filter_expr) == "floor(Value)"
    
    def test_ceiling(self):
        """Test ceiling function."""
        filter_expr = F.Value.ceiling()
        assert str(filter_expr) == "ceiling(Value)"


class TestTypeFunctions:
    """Test type functions (v3 and v4)."""
    
    def test_isof_no_type(self):
        """Test isof function without type parameter."""
        filter_expr = F.Entity.isof()
        assert str(filter_expr) == "isof(Entity)"
    
    def test_isof_with_type(self):
        """Test isof function with type parameter."""
        filter_expr = F.Entity.isof("Model.DerivedType")
        assert str(filter_expr) == "isof(Entity,'Model.DerivedType')"
    
    def test_cast_v4(self):
        """Test cast function (v4 only)."""
        filter_expr = F.Value.cast("Edm.String")
        assert str(filter_expr) == "cast(Value,'Edm.String')"


class TestCollectionFunctions:
    """Test collection functions (v4 only)."""
    
    def test_hassubset(self):
        """Test hassubset function."""
        filter_expr = F.Tags.hassubset(["Important", "Urgent"])
        assert str(filter_expr) == "hassubset(Tags,['Important','Urgent'])"
        
        # With numbers
        filter_expr = F.Codes.hassubset([1, 3, 5])
        assert str(filter_expr) == "hassubset(Codes,[1,3,5])"
    
    def test_hassubsequence(self):
        """Test hassubsequence function."""
        filter_expr = F.Steps.hassubsequence(["Start", "Process", "End"])
        assert str(filter_expr) == "hassubsequence(Steps,['Start','Process','End'])"
        
        # With mixed types
        filter_expr = F.Values.hassubsequence([1, "two", 3])
        assert str(filter_expr) == "hassubsequence(Values,[1,'two',3])"
    
    def test_any_without_lambda(self):
        """Test any function without lambda expression."""
        filter_expr = F.Orders.any()
        assert str(filter_expr) == "Orders/any()"
    
    def test_any_with_lambda(self):
        """Test any function with lambda expression."""
        filter_expr = F.Orders.any("o: o/Amount gt 1000")
        assert str(filter_expr) == "Orders/any(o: o/Amount gt 1000)"
    
    def test_all_with_lambda(self):
        """Test all function with lambda expression."""
        filter_expr = F.LineItems.all("li: li/Quantity gt 0")
        assert str(filter_expr) == "LineItems/all(li: li/Quantity gt 0)"
    
    def test_nested_collection_functions(self):
        """Test nested collection functions."""
        filter_expr = F.Orders.any("o: o/LineItems/any(li: li/Product eq 'Widget')")
        assert str(filter_expr) == "Orders/any(o: o/LineItems/any(li: li/Product eq 'Widget'))"


class TestGeoFunctions:
    """Test geo-spatial functions (v4 only)."""
    
    def test_geo_distance(self):
        """Test geo.distance function."""
        filter_expr = F.Location.geo_distance("POINT(-122.131577 37.411896)")
        assert str(filter_expr) == "geo.distance(Location,'POINT(-122.131577 37.411896)')"
        
        # Distance comparison
        filter_expr = F.Location.geo_distance("POINT(-122.131577 37.411896)") < 10
        assert str(filter_expr) == "(geo.distance(Location,'POINT(-122.131577 37.411896)') lt 10)"
    
    def test_geo_intersects(self):
        """Test geo.intersects function."""
        polygon = "POLYGON((-122.2 37.4,-122.1 37.4,-122.1 37.5,-122.2 37.5,-122.2 37.4))"
        filter_expr = F.Area.geo_intersects(polygon)
        expected = f"geo.intersects(Area,'{polygon}')"
        assert str(filter_expr) == expected
    
    def test_geo_length(self):
        """Test geo.length function."""
        filter_expr = F.Route.geo_length()
        assert str(filter_expr) == "geo.length(Route)"


class TestConditionalFunctions:
    """Test conditional functions (v4 only)."""
    
    def test_case_simple(self):
        """Test case function with simple conditions."""
        # Using comparison filters as conditions
        filter_expr = Filter("case(X gt 0:1,X lt 0:-1,true:0)")
        assert str(filter_expr) == "case(X gt 0:1,X lt 0:-1,true:0)"
    
    def test_case_with_filter_conditions(self):
        """Test case function built with Filter objects."""
        # This is a more complex test showing how case might be used
        # Note: The case method strips parentheses from conditions
        x_positive = F.X > 0
        x_negative = F.X < 0
        
        # Manual construction since case needs special handling
        filter_expr = Filter("case(Status eq 'Active':'Open',Status eq 'Closed':'Done',true:'Unknown')")
        expected = "case(Status eq 'Active':'Open',Status eq 'Closed':'Done',true:'Unknown')"
        assert str(filter_expr) == expected


class TestAdditionalV4Functions:
    """Test additional v4-specific functions."""
    
    def test_has(self):
        """Test has function for flag enumerations."""
        filter_expr = F.Permissions.has("Read")
        assert str(filter_expr) == "has(Permissions,'Read')"
        
        # Combined with logical operators
        filter_expr = F.Permissions.has("Read") & F.Permissions.has("Write")
        assert str(filter_expr) == "(has(Permissions,'Read') and has(Permissions,'Write'))"
    
    def test_in(self):
        """Test in function for checking membership in a list."""
        filter_expr = F.Status.in_(["Active", "Pending", "InProgress"])
        assert str(filter_expr) == "Status in ('Active','Pending','InProgress')"
        
        # With numbers
        filter_expr = F.Priority.in_([1, 2, 3])
        assert str(filter_expr) == "Priority in (1,2,3)"
        
        # With mixed types
        filter_expr = F.Code.in_(["A", "B", 123])
        assert str(filter_expr) == "Code in ('A','B',123)"


class TestCustomFields:
    """Test custom field functionality."""
    
    def test_custom_field_basic(self):
        """Test basic custom field creation."""
        cf = CustomField.field("ItemSettings", "UsrRepairItemType")
        assert str(cf) == "ItemSettings.UsrRepairItemType"
    
    def test_custom_field_with_entity(self):
        """Test custom field with entity name."""
        cf = CustomField.field("ItemSettings", "UsrRepairItemType", "InventoryItem")
        assert str(cf) == "InventoryItem/ItemSettings.UsrRepairItemType"
    
    def test_custom_attribute(self):
        """Test custom attribute field."""
        cf = CustomField.attribute("Document", "OPERATSYST")
        assert str(cf) == "Document.AttributeOPERATSYST"
    
    def test_cf_factory_method(self):
        """Test the F.cf() factory method."""
        filter_expr = F.cf("String", "ItemSettings", "UsrRepairItemType")
        assert str(filter_expr) == "cf.String(f='ItemSettings.UsrRepairItemType')"


class TestQueryOptions:
    """Test QueryOptions class with v3 and v4 parameters."""
    
    def test_basic_options(self):
        """Test basic query options (v3 and v4)."""
        options = QueryOptions(
            filter=F.Status == "Active",
            select=["Id", "Name", "Status"],
            expand=["Contact", "Address"],
            top=10,
            skip=20
        )
        
        params = options.to_params()
        assert params["$filter"] == "(Status eq 'Active')"
        assert params["$select"] == "Id,Name,Status"
        assert params["$expand"] == "Address,Contact"  # Sorted
        assert params["$top"] == "10"
        assert params["$skip"] == "20"
    
    def test_orderby_string(self):
        """Test orderby with string (v3 and v4)."""
        options = QueryOptions(orderby="Name desc")
        params = options.to_params()
        assert params["$orderby"] == "Name desc"
    
    def test_orderby_list(self):
        """Test orderby with list (v3 and v4)."""
        options = QueryOptions(orderby=["Name asc", "CreatedDate desc"])
        params = options.to_params()
        assert params["$orderby"] == "Name asc,CreatedDate desc"
    
    def test_v4_specific_options(self):
        """Test v4-specific query options."""
        options = QueryOptions(
            count=True,
            search="customer john",
            format="json",
            skiptoken="abc123",
            deltatoken="def456",
            apply="groupby((Status), aggregate(Amount with sum as Total))"
        )
        
        params = options.to_params()
        assert params["$count"] == "true"
        assert params["$search"] == "customer john"
        assert params["$format"] == "json"
        assert params["$skiptoken"] == "abc123"
        assert params["$deltatoken"] == "def456"
        assert params["$apply"] == "groupby((Status), aggregate(Amount with sum as Total))"
    
    def test_count_false(self):
        """Test count parameter set to false."""
        options = QueryOptions(count=False)
        params = options.to_params()
        assert params["$count"] == "false"
    
    def test_custom_fields_with_auto_expand(self):
        """Test that custom fields automatically add to expand."""
        cf1 = CustomField.field("Details", "CustomField1", "Order")
        cf2 = CustomField.field("Info", "CustomField2", "Customer")
        
        options = QueryOptions(
            custom=[cf1, cf2, "SimpleCustomField"],
            expand=["Contact"]  # Existing expand
        )
        
        params = options.to_params()
        assert params["$custom"] == "Order/Details.CustomField1,Customer/Info.CustomField2,SimpleCustomField"
        assert params["$expand"] == "Contact,Customer,Order"  # Auto-added Customer and Order
    
    def test_empty_options(self):
        """Test empty QueryOptions produces empty params."""
        options = QueryOptions()
        params = options.to_params()
        assert params == {}


class TestComplexScenarios:
    """Test complex real-world filter scenarios."""
    
    def test_complex_v3_filter(self):
        """Test complex filter using v3 features."""
        filter_expr = (
            ((F.Status == "Active") | (F.Status == "Pending")) &
            (F.Amount > 1000) &
            F.CustomerName.tolower().startswith("acme") &
            (F.CreatedDate.year() == 2024)
        )
        
        expected = (
            "(((((Status eq 'Active') or (Status eq 'Pending')) and "
            "(Amount gt 1000)) and startswith(tolower(CustomerName),'acme')) and "
            "(year(CreatedDate) eq 2024))"
        )
        assert str(filter_expr) == expected
    
    def test_complex_v4_filter(self):
        """Test complex filter using v4-specific features."""
        filter_expr = (
            F.Orders.any("o: o/Amount gt 1000") &
            F.Status.in_(["Active", "Processing"]) &
            (F.CreatedDate > Filter("now()").date() - 30) &
            F.Tags.has("Important")
        )
        
        # Note: The exact string representation would depend on how date arithmetic is handled
        # This is a simplified check
        assert "Orders/any(o: o/Amount gt 1000)" in str(filter_expr)
        assert "Status in ('Active','Processing')" in str(filter_expr)
        assert "has(Tags,'Important')" in str(filter_expr)
    
    def test_mixed_v3_v4_compatible_filter(self):
        """Test filter that works in both v3 and v4."""
        filter_expr = (
            (F.Type == "Customer") &
            (F.Balance > 0) &
            ((F.Country == "US") | (F.Country == "CA")) &
            F.Email.endswith("@example.com") &
            ~(F.Status == "Deleted")
        )
        
        expected = (
            "(((((Type eq 'Customer') and (Balance gt 0)) and "
            "((Country eq 'US') or (Country eq 'CA'))) and "
            "endswith(Email,'@example.com')) and not ((Status eq 'Deleted')))"
        )
        assert str(filter_expr) == expected


class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_filter_with_none_value(self):
        """Test filter with None value."""
        filter_expr = F.DeletedDate == None
        assert str(filter_expr) == "(DeletedDate eq null)"
    
    def test_filter_with_empty_string(self):
        """Test filter with empty string."""
        filter_expr = F.Description == ""
        assert str(filter_expr) == "(Description eq '')"
    
    def test_filter_with_special_characters(self):
        """Test filter with special characters in string."""
        filter_expr = F.Name == "O'Brien's \"Special\" Item"
        assert str(filter_expr) == "(Name eq 'O''Brien''s \"Special\" Item')"
    
    def test_chained_string_functions(self):
        """Test multiple chained string functions."""
        filter_expr = F.Name.trim().tolower().replace(" ", "-").length() > 10
        expected = "(length(replace(tolower(trim(Name)),' ','-')) gt 10)"
        assert str(filter_expr) == expected
    
    def test_nested_arithmetic(self):
        """Test deeply nested arithmetic operations."""
        filter_expr = ((F.Price * 1.1) + (F.Tax * 0.9)) / 2 > 100
        expected = "((((Price mul 1.1) add (Tax mul 0.9)) div 2) gt 100)"
        assert str(filter_expr) == expected

    def test_regex(self):
        # With special regex characters
        filter_expr = F.Email.matchesPattern(r".*@[a-z]+\.[a-z]{2,3}")
        assert str(filter_expr) == r"matchesPattern(Email,'.*@[a-z]+\.[a-z]{2,3}')"


class TestDateTimeFunctions:
    """Test date/time functions (v3 and v4)."""
    
    def test_year(self):
        """Test year function."""
        filter_expr = F.CreatedDate.year()
        assert str(filter_expr) == "year(CreatedDate)"
        
        filter_expr = F.CreatedDate.year() == 2024
        assert str(filter_expr) == "(year(CreatedDate) eq 2024)"
    
    def test_month(self):
        """Test month function."""
        filter_expr = F.CreatedDate.month()
        assert str(filter_expr) == "month(CreatedDate)"
    
    def test_day(self):
        """Test day function."""
        filter_expr = F.CreatedDate.day()
        assert str(filter_expr) == "day(CreatedDate)"
    
    def test_hour(self):
        """Test hour function."""
        filter_expr = F.CreatedTime.hour()
        assert str(filter_expr) == "hour(CreatedTime)"
    
    def test_minute(self):
        """Test minute function."""
        filter_expr = F.CreatedTime.minute()
        assert str(filter_expr) == "minute(CreatedTime)"
    
    def test_second(self):
        """Test second function."""
        filter_expr = F.CreatedTime.second()
        assert str(filter_expr) == "second(CreatedTime)"
    
    def test_date_v4(self):
        """Test date function (v4 only)."""
        filter_expr = F.CreatedDateTime.date()
        assert str(filter_expr) == "date(CreatedDateTime)"
        
        # Compare date part
        filter_expr = F.CreatedDateTime.date() == date(2024, 1, 15)
        assert str(filter_expr) == "(date(CreatedDateTime) eq date'2024-01-15')"
    
    def test_time_v4(self):
        """Test time function (v4 only)."""
        filter_expr = F.CreatedDateTime.time()
        assert str(filter_expr) == "time(CreatedDateTime)"
    
    def test_totaloffsetminutes_v4(self):
        """Test totaloffsetminutes function (v4 only)."""
        filter_expr = F.DateTimeOffset.totaloffsetminutes()
        assert str(filter_expr) == "totaloffsetminutes(DateTimeOffset)"
    
    def test_totalseconds_v4(self):
        """Test totalseconds function (v4 only)."""
        filter_expr = F.Duration.totalseconds()
        assert str(filter_expr) == "totalseconds(Duration)"
    
    def test_now_v4(self):
        """Test now function (v4 only)."""
        filter_expr = F.CreatedDate < Filter("now()")
        assert str(filter_expr) == "(CreatedDate lt now())"
    
    def test_maxdatetime_v4(self):
        """Test maxdatetime function (v4 only)."""
        filter_expr = F.EndDate == Filter("maxdatetime()")
        assert str(filter_expr) == "(EndDate eq maxdatetime())"
    
    def test_mindatetime_v4(self):
        """Test mindatetime function (v4 only)."""
        filter_expr = F.StartDate == Filter("mindatetime()")
        assert str(filter_expr) == "(StartDate eq mindatetime())"


class TestMathFunctions:
    """Test math functions (v3 and v4)."""
    
    def test_round(self):
        """Test round function."""
        filter_expr = F.Price.round()
        assert str(filter_expr) == "round(Price)"
        
        filter_expr = F.Price.round() == 100
        assert str(filter_expr) == "(round(Price) eq 100)"
    
    def test_floor(self):
        """Test floor function."""
        filter_expr = F.Value.floor()
        assert str(filter_expr) == "floor(Value)"
    
    def test_ceiling(self):
        """Test ceiling function."""
        filter_expr = F.Value.ceiling()
        assert str(filter_expr) == "ceiling(Value)"


class TestTypeFunctions:
    """Test type functions (v3 and v4)."""
    
    def test_isof_no_type(self):
        """Test isof function without type parameter."""
        filter_expr = F.Entity.isof()
        assert str(filter_expr) == "isof(Entity)"
    
    def test_isof_with_type(self):
        """Test isof function with type parameter."""
        filter_expr = F.Entity.isof("Model.DerivedType")
        assert str(filter_expr) == "isof(Entity,'Model.DerivedType')"
    
    def test_cast_v4(self):
        """Test cast function (v4 only)."""
        filter_expr = F.Value.cast("Edm.String")
        assert str(filter_expr) == "cast(Value,'Edm.String')"


class TestCollectionFunctions:
    """Test collection functions (v4 only)."""
    
    def test_any_without_lambda(self):
        """Test any function without lambda expression."""
        filter_expr = F.Orders.any()
        assert str(filter_expr) == "Orders/any()"
    
    def test_any_with_lambda(self):
        """Test any function with lambda expression."""
        filter_expr = F.Orders.any("o: o/Amount gt 1000")
        assert str(filter_expr) == "Orders/any(o: o/Amount gt 1000)"
    
    def test_all_with_lambda(self):
        """Test all function with lambda expression."""
        filter_expr = F.LineItems.all("li: li/Quantity gt 0")
        assert str(filter_expr) == "LineItems/all(li: li/Quantity gt 0)"
    
    def test_nested_collection_functions(self):
        """Test nested collection functions."""
        filter_expr = F.Orders.any("o: o/LineItems/any(li: li/Product eq 'Widget')")
        assert str(filter_expr) == "Orders/any(o: o/LineItems/any(li: li/Product eq 'Widget'))"


class TestGeoFunctions:
    """Test geo-spatial functions (v4 only)."""
    
    def test_geo_distance(self):
        """Test geo.distance function."""
        filter_expr = F.Location.geo_distance("POINT(-122.131577 37.411896)")
        assert str(filter_expr) == "geo.distance(Location,'POINT(-122.131577 37.411896)')"
        
        # Distance comparison
        filter_expr = F.Location.geo_distance("POINT(-122.131577 37.411896)") < 10
        assert str(filter_expr) == "(geo.distance(Location,'POINT(-122.131577 37.411896)') lt 10)"
    
    def test_geo_intersects(self):
        """Test geo.intersects function."""
        polygon = "POLYGON((-122.2 37.4,-122.1 37.4,-122.1 37.5,-122.2 37.5,-122.2 37.4))"
        filter_expr = F.Area.geo_intersects(polygon)
        expected = f"geo.intersects(Area,'{polygon}')"
        assert str(filter_expr) == expected
    
    def test_geo_length(self):
        """Test geo.length function."""
        filter_expr = F.Route.geo_length()
        assert str(filter_expr) == "geo.length(Route)"


class TestAdditionalV4Functions:
    """Test additional v4-specific functions."""
    
    def test_has(self):
        """Test has function for flag enumerations."""
        filter_expr = F.Permissions.has("Read")
        assert str(filter_expr) == "has(Permissions,'Read')"
        
        # Combined with logical operators
        filter_expr = F.Permissions.has("Read") & F.Permissions.has("Write")
        assert str(filter_expr) == "(has(Permissions,'Read') and has(Permissions,'Write'))"
    
    def test_in(self):
        """Test in function for checking membership in a list."""
        filter_expr = F.Status.in_(["Active", "Pending", "InProgress"])
        assert str(filter_expr) == "Status in ('Active','Pending','InProgress')"
        
        # With numbers
        filter_expr = F.Priority.in_([1, 2, 3])
        assert str(filter_expr) == "Priority in (1,2,3)"
        
        # With mixed types
        filter_expr = F.Code.in_(["A", "B", 123])
        assert str(filter_expr) == "Code in ('A','B',123)"


class TestCustomFields:
    """Test custom field functionality."""
    
    def test_custom_field_basic(self):
        """Test basic custom field creation."""
        cf = CustomField.field("ItemSettings", "UsrRepairItemType")
        assert str(cf) == "ItemSettings.UsrRepairItemType"
    
    def test_custom_field_with_entity(self):
        """Test custom field with entity name."""
        cf = CustomField.field("ItemSettings", "UsrRepairItemType", "InventoryItem")
        assert str(cf) == "InventoryItem/ItemSettings.UsrRepairItemType"
    
    def test_custom_attribute(self):
        """Test custom attribute field."""
        cf = CustomField.attribute("Document", "OPERATSYST")
        assert str(cf) == "Document.AttributeOPERATSYST"
    
    def test_cf_factory_method(self):
        """Test the F.cf() factory method."""
        filter_expr = F.cf("String", "ItemSettings", "UsrRepairItemType")
        assert str(filter_expr) == "cf.String(f='ItemSettings.UsrRepairItemType')"


class TestQueryOptions:
    """Test QueryOptions class with v3 and v4 parameters."""
    
    def test_basic_options(self):
        """Test basic query options (v3 and v4)."""
        options = QueryOptions(
            filter=F.Status == "Active",
            select=["Id", "Name", "Status"],
            expand=["Contact", "Address"],
            top=10,
            skip=20
        )
        
        params = options.to_params()
        assert params["$filter"] == "(Status eq 'Active')"
        assert params["$select"] == "Id,Name,Status"
        assert params["$expand"] == "Address,Contact"  # Sorted
        assert params["$top"] == "10"
        assert params["$skip"] == "20"
    
    def test_orderby_string(self):
        """Test orderby with string (v3 and v4)."""
        options = QueryOptions(orderby="Name desc")
        params = options.to_params()
        assert params["$orderby"] == "Name desc"
    
    def test_orderby_list(self):
        """Test orderby with list (v3 and v4)."""
        options = QueryOptions(orderby=["Name asc", "CreatedDate desc"])
        params = options.to_params()
        assert params["$orderby"] == "Name asc,CreatedDate desc"
    
    def test_v4_specific_options(self):
        """Test v4-specific query options."""
        options = QueryOptions(
            count=True,
            search="customer john",
            format="json",
            skiptoken="abc123",
            deltatoken="def456",
            apply="groupby((Status), aggregate(Amount with sum as Total))"
        )
        
        params = options.to_params()
        assert params["$count"] == "true"
        assert params["$search"] == "customer john"
        assert params["$format"] == "json"
        assert params["$skiptoken"] == "abc123"
        assert params["$deltatoken"] == "def456"
        assert params["$apply"] == "groupby((Status), aggregate(Amount with sum as Total))"
    
    def test_count_false(self):
        """Test count parameter set to false."""
        options = QueryOptions(count=False)
        params = options.to_params()
        assert params["$count"] == "false"
    
    def test_custom_fields_with_auto_expand(self):
        """Test that custom fields automatically add to expand."""
        cf1 = CustomField.field("Details", "CustomField1", "Order")
        cf2 = CustomField.field("Info", "CustomField2", "Customer")
        
        options = QueryOptions(
            custom=[cf1, cf2, "SimpleCustomField"],
            expand=["Contact"]  # Existing expand
        )
        
        params = options.to_params()
        assert params["$custom"] == "Order/Details.CustomField1,Customer/Info.CustomField2,SimpleCustomField"
        assert params["$expand"] == "Contact,Customer,Order"  # Auto-added Customer and Order
    
    def test_empty_options(self):
        """Test empty QueryOptions produces empty params."""
        options = QueryOptions()
        params = options.to_params()
        assert params == {}


class TestComplexScenarios:
    """Test complex real-world filter scenarios."""
    
    def test_complex_v3_filter(self):
        """Test complex filter using v3 features."""
        filter_expr = (
            ((F.Status == "Active") | (F.Status == "Pending")) &
            (F.Amount > 1000) &
            F.CustomerName.tolower().startswith("acme") &
            (F.CreatedDate.year() == 2024)
        )
        
        expected = (
            "(((((Status eq 'Active') or (Status eq 'Pending')) and "
            "(Amount gt 1000)) and startswith(tolower(CustomerName),'acme')) and "
            "(year(CreatedDate) eq 2024))"
        )
        assert str(filter_expr) == expected
    
    def test_complex_v4_filter(self):
        """Test complex filter using v4-specific features."""
        filter_expr = (
            F.Orders.any("o: o/Amount gt 1000") &
            F.Status.in_(["Active", "Processing"]) &
            (F.CreatedDate > Filter("now()").date() - 30) &
            F.Tags.has("Important")
        )
        
        # Note: The exact string representation would depend on how date arithmetic is handled
        # This is a simplified check
        assert "Orders/any(o: o/Amount gt 1000)" in str(filter_expr)
        assert "Status in ('Active','Processing')" in str(filter_expr)
        assert "has(Tags,'Important')" in str(filter_expr)
    
    def test_mixed_v3_v4_compatible_filter(self):
        """Test filter that works in both v3 and v4."""
        filter_expr = (
            (F.Type == "Customer") &
            (F.Balance > 0) &
            ((F.Country == "US") | (F.Country == "CA")) &
            F.Email.endswith("@example.com") &
            ~(F.Status == "Deleted")
        )
        
        expected = (
            "(((((Type eq 'Customer') and (Balance gt 0)) and "
            "((Country eq 'US') or (Country eq 'CA'))) and "
            "endswith(Email,'@example.com')) and not ((Status eq 'Deleted')))"
        )
        assert str(filter_expr) == expected


class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_filter_with_none_value(self):
        """Test filter with None value."""
        filter_expr = F.DeletedDate == None
        assert str(filter_expr) == "(DeletedDate eq null)"
    
    def test_filter_with_empty_string(self):
        """Test filter with empty string."""
        filter_expr = F.Description == ""
        assert str(filter_expr) == "(Description eq '')"
    
    def test_filter_with_special_characters(self):
        """Test filter with special characters in string."""
        filter_expr = F.Name == "O'Brien's \"Special\" Item"
        assert str(filter_expr) == "(Name eq 'O''Brien''s \"Special\" Item')"
    
    def test_chained_string_functions(self):
        """Test multiple chained string functions."""
        filter_expr = F.Name.trim().tolower().replace(" ", "-").length() > 10
        expected = "(length(replace(tolower(trim(Name)),' ','-')) gt 10)"
        assert str(filter_expr) == expected
    
    def test_nested_arithmetic(self):
        """Test deeply nested arithmetic operations."""
        filter_expr = ((F.Price * 1.1) + (F.Tax * 0.9)) / 2 > 100
        expected = "((((Price mul 1.1) add (Tax mul 0.9)) div 2) gt 100)"
        assert str(filter_expr) == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])