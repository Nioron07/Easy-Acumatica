# src/easy_acumatica/models/contact.py

from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import datetime
from ..core import BaseDataClassModel # Import the new base model

__all__ = ["Attribute", "Address", "Contact"]

# ---------------------------------------------------------------------------
# Helper Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class Attribute(BaseDataClassModel):
    """Represents a single custom attribute for a contact."""
    AttributeID: str
    Value: str

@dataclass
class Address(BaseDataClassModel):
    """Represents a physical address."""
    AddressLine1: Optional[str] = None
    AddressLine2: Optional[str] = None
    City: Optional[str] = None
    State: Optional[str] = None
    PostalCode: Optional[str] = None
    Country: Optional[str] = None

# ---------------------------------------------------------------------------
# The Main Contact Dataclass
# ---------------------------------------------------------------------------
@dataclass
class Contact(BaseDataClassModel):
    """
    A comprehensive dataclass for a Contact payload. Inherits payload
    generation logic from BaseDataClassModel.
    """
    # --- Required Fields ---
    LastName: str

    # --- Core Identity & Details ---
    FirstName: Optional[str] = None
    MiddleName: Optional[str] = None
    JobTitle: Optional[str] = None
    Email: Optional[str] = None
    WebSite: Optional[str] = None
    ParentAccount: Optional[str] = None
    BusinessAccount: Optional[str] = None
    
    # --- Phone and Fax ---
    Phone1: Optional[str] = None
    Phone1Type: str = "Business 1"
    Phone2: Optional[str] = None
    Phone2Type: str = "Cell"
    Phone3: Optional[str] = None
    Phone3Type: str = "Home"
    Fax: Optional[str] = None
    FaxType: str = "Fax"
    
    # --- Classification and Status ---
    Type: str = "Contact"
    Status: str = "Active"
    ContactClass: Optional[str] = None
    Source: Optional[str] = None
    Reason: Optional[str] = None
    
    # --- Address Information ---
    Address: Optional[Address] = None
    OverrideAccountAddress: bool = False
    
    # --- Personal Information ---
    Gender: Optional[str] = None
    MaritalStatus: Optional[str] = None
    SpouseOrPartnerName: Optional[str] = None
    DateOfBirth: Optional[datetime.date] = None

    # --- Communication Preferences ---
    DoNotCall: bool = False
    DoNotEmail: bool = False
    DoNotFax: bool = False
    DoNotMail: bool = False
    NoMarketing: bool = False
    NoMassMail: bool = False
    
    # --- Nested Lists ---
    Attributes: List[Attribute] = field(default_factory=list)
    
    # --- System and Other Fields ---
    ContactID: Optional[int] = None
    Owner: Optional[str] = None
    Workgroup: Optional[str] = None