# tests/mock_xml.py

def get_odata_metadata_xml():
    """
    Returns the base mock OData XML metadata document for Generic Inquiries.
    """
    return '''<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx Version="4.0" xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx">
    <edmx:DataServices>
        <Schema Namespace="Default" xmlns="http://docs.oasis-open.org/odata/ns/edm">
            
            <!-- Entity Types for different inquiries -->
            <EntityType Name="AccountDetailsType">
                <Key>
                    <PropertyRef Name="AccountID"/>
                </Key>
                <Property Name="AccountID" Type="Edm.String" MaxLength="50"/>
                <Property Name="AccountName" Type="Edm.String" MaxLength="200"/>
                <Property Name="Balance" Type="Edm.Decimal" Precision="19" Scale="4"/>
                <Property Name="IsActive" Type="Edm.Boolean"/>
                <Property Name="CreatedDate" Type="Edm.DateTimeOffset"/>
            </EntityType>
            
            <EntityType Name="CustomerListType">
                <Key>
                    <PropertyRef Name="CustomerID"/>
                </Key>
                <Property Name="CustomerID" Type="Edm.String" MaxLength="50"/>
                <Property Name="CustomerName" Type="Edm.String" MaxLength="200"/>
                <Property Name="City" Type="Edm.String" MaxLength="100"/>
                <Property Name="Country" Type="Edm.String" MaxLength="100"/>
                <Property Name="Phone" Type="Edm.String" MaxLength="50"/>
                <Property Name="Email" Type="Edm.String" MaxLength="200"/>
            </EntityType>
            
            <EntityType Name="InventoryItemType">
                <Key>
                    <PropertyRef Name="InventoryID"/>
                </Key>
                <Property Name="InventoryID" Type="Edm.String" MaxLength="50"/>
                <Property Name="Description" Type="Edm.String" MaxLength="500"/>
                <Property Name="UnitPrice" Type="Edm.Decimal" Precision="19" Scale="4"/>
                <Property Name="QtyOnHand" Type="Edm.Decimal" Precision="19" Scale="4"/>
                <Property Name="ItemClass" Type="Edm.String" MaxLength="50"/>
                <Property Name="BaseUnit" Type="Edm.String" MaxLength="10"/>
                <Property Name="LastModified" Type="Edm.DateTimeOffset"/>
            </EntityType>
            
            <!-- Container with EntitySets -->
            <EntityContainer Name="Default">
                <EntitySet Name="Account Details" EntityType="Default.AccountDetailsType"/>
                <EntitySet Name="Customer List" EntityType="Default.CustomerListType"/>
                <EntitySet Name="Inventory Items" EntityType="Default.InventoryItemType"/>
                <EntitySet Name="GL-Trial Balance" EntityType="Default.AccountDetailsType"/>
                <EntitySet Name="AR-Customer Balance Summary" EntityType="Default.CustomerListType"/>
                <EntitySet Name="IN-Inventory Summary" EntityType="Default.InventoryItemType"/>
            </EntityContainer>
            
        </Schema>
    </edmx:DataServices>
</edmx:Edmx>'''


def get_modified_odata_metadata_xml():
    """
    Returns a modified version of the OData XML metadata to test differential inquiry caching.
    This version adds new inquiries and modifies existing ones.
    """
    return '''<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx Version="4.0" xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx">
    <edmx:DataServices>
        <Schema Namespace="Default" xmlns="http://docs.oasis-open.org/odata/ns/edm">
            
            <!-- Original Entity Types -->
            <EntityType Name="AccountDetailsType">
                <Key>
                    <PropertyRef Name="AccountID"/>
                </Key>
                <Property Name="AccountID" Type="Edm.String" MaxLength="50"/>
                <Property Name="AccountName" Type="Edm.String" MaxLength="200"/>
                <Property Name="Balance" Type="Edm.Decimal" Precision="19" Scale="4"/>
                <Property Name="IsActive" Type="Edm.Boolean"/>
                <Property Name="CreatedDate" Type="Edm.DateTimeOffset"/>
                <!-- Added new property to existing type -->
                <Property Name="LastActivity" Type="Edm.DateTimeOffset"/>
            </EntityType>
            
            <EntityType Name="CustomerListType">
                <Key>
                    <PropertyRef Name="CustomerID"/>
                </Key>
                <Property Name="CustomerID" Type="Edm.String" MaxLength="50"/>
                <Property Name="CustomerName" Type="Edm.String" MaxLength="200"/>
                <Property Name="City" Type="Edm.String" MaxLength="100"/>
                <Property Name="Country" Type="Edm.String" MaxLength="100"/>
                <Property Name="Phone" Type="Edm.String" MaxLength="50"/>
                <Property Name="Email" Type="Edm.String" MaxLength="200"/>
                <!-- Added new properties -->
                <Property Name="CreditLimit" Type="Edm.Decimal" Precision="19" Scale="4"/>
                <Property Name="PaymentTerms" Type="Edm.String" MaxLength="50"/>
            </EntityType>
            
            <EntityType Name="InventoryItemType">
                <Key>
                    <PropertyRef Name="InventoryID"/>
                </Key>
                <Property Name="InventoryID" Type="Edm.String" MaxLength="50"/>
                <Property Name="Description" Type="Edm.String" MaxLength="500"/>
                <Property Name="UnitPrice" Type="Edm.Decimal" Precision="19" Scale="4"/>
                <Property Name="QtyOnHand" Type="Edm.Decimal" Precision="19" Scale="4"/>
                <Property Name="ItemClass" Type="Edm.String" MaxLength="50"/>
                <Property Name="BaseUnit" Type="Edm.String" MaxLength="10"/>
                <Property Name="LastModified" Type="Edm.DateTimeOffset"/>
            </EntityType>
            
            <!-- NEW Entity Type for new inquiries -->
            <EntityType Name="VendorListType">
                <Key>
                    <PropertyRef Name="VendorID"/>
                </Key>
                <Property Name="VendorID" Type="Edm.String" MaxLength="50"/>
                <Property Name="VendorName" Type="Edm.String" MaxLength="200"/>
                <Property Name="City" Type="Edm.String" MaxLength="100"/>
                <Property Name="Country" Type="Edm.String" MaxLength="100"/>
                <Property Name="Phone" Type="Edm.String" MaxLength="50"/>
                <Property Name="Email" Type="Edm.String" MaxLength="200"/>
                <Property Name="PaymentTerms" Type="Edm.String" MaxLength="50"/>
            </EntityType>
            
            <EntityType Name="ProjectListType">
                <Key>
                    <PropertyRef Name="ProjectID"/>
                </Key>
                <Property Name="ProjectID" Type="Edm.String" MaxLength="50"/>
                <Property Name="ProjectName" Type="Edm.String" MaxLength="200"/>
                <Property Name="Status" Type="Edm.String" MaxLength="50"/>
                <Property Name="StartDate" Type="Edm.DateTimeOffset"/>
                <Property Name="EndDate" Type="Edm.DateTimeOffset"/>
                <Property Name="Manager" Type="Edm.String" MaxLength="100"/>
            </EntityType>
            
            <!-- Container with EntitySets - includes original + new + removed one -->
            <EntityContainer Name="Default">
                <!-- Existing inquiries -->
                <EntitySet Name="Account Details" EntityType="Default.AccountDetailsType"/>
                <EntitySet Name="Customer List" EntityType="Default.CustomerListType"/>
                <EntitySet Name="Inventory Items" EntityType="Default.InventoryItemType"/>
                
                <!-- Modified existing inquiries (same name, potentially different structure) -->
                <EntitySet Name="GL-Trial Balance" EntityType="Default.AccountDetailsType"/>
                <EntitySet Name="AR-Customer Balance Summary" EntityType="Default.CustomerListType"/>
                
                <!-- Removed: IN-Inventory Summary to test removal -->
                
                <!-- NEW inquiries to test addition -->
                <EntitySet Name="Vendor List" EntityType="Default.VendorListType"/>
                <EntitySet Name="AP-Vendor Balance Summary" EntityType="Default.VendorListType"/>
                <EntitySet Name="PM-Project List" EntityType="Default.ProjectListType"/>
                <EntitySet Name="Time-Project Summary" EntityType="Default.ProjectListType"/>
            </EntityContainer>
            
        </Schema>
    </edmx:DataServices>
</edmx:Edmx>'''