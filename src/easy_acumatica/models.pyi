from __future__ import annotations
from typing import Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from easy_acumatica.core import BaseDataClassModel


@dataclass
class ACAInfoDetail(BaseDataClassModel):
    CoverageType: Optional['StringValue']
    HealthPlanType: Optional['StringValue']


@dataclass
class ACAInformation(BaseDataClassModel):
    ACAInfoDetails: List[Optional['ACAInfoDetail']]
    MinIndividualContribution: Optional['DecimalValue']


@dataclass
class AcceptInvitationEvent(BaseDataClassModel):
    entity: Optional['Event']


@dataclass
class Account(BaseDataClassModel):
    AccountCD: Optional['StringValue']
    AccountClass: Optional['StringValue']
    AccountGroup: Optional['StringValue']
    AccountID: Optional['IntValue']
    Active: Optional['BooleanValue']
    CashAccount: Optional['BooleanValue']
    ChartOfAccountsOrder: Optional['IntValue']
    ConsolidationAccount: Optional['StringValue']
    CreatedDateTime: Optional['DateTimeValue']
    CurrencyID: Optional['StringValue']
    Description: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    PostOption: Optional['StringValue']
    RequireUnits: Optional['BooleanValue']
    RevaluationRateType: Optional['StringValue']
    Secured: Optional['BooleanValue']
    TaxCategory: Optional['StringValue']
    Type: Optional['StringValue']
    UseDefaultSubaccount: Optional['BooleanValue']


@dataclass
class AccountCustomAction(BaseDataClassModel):
    entity: Optional['Account']
    parameters: Optional[Any]


@dataclass
class AccountDetailsForPeriodInquiry(BaseDataClassModel):
    FromPeriod: Optional['StringValue']
    Ledger: Optional['StringValue']
    Results: List[Optional['AccountDetailsForPeriodInquiryDetail']]
    ToPeriod: Optional['StringValue']
    IncludeUnposted: Optional['BooleanValue']
    IncludeUnreleased: Optional['BooleanValue']


@dataclass
class AccountDetailsForPeriodInquiryCustomAction(BaseDataClassModel):
    entity: Optional['AccountDetailsForPeriodInquiry']
    parameters: Optional[Any]


@dataclass
class AccountDetailsForPeriodInquiryDetail(BaseDataClassModel):
    Account: Optional['StringValue']
    BatchNumber: Optional['StringValue']
    Branch: Optional['StringValue']
    CreditAmount: Optional['DecimalValue']
    CreditAmountInBaseCurrency: Optional['DecimalValue']
    Currency: Optional['StringValue']
    CustomerVendor: Optional['StringValue']
    DebitAmount: Optional['DecimalValue']
    DebitAmountInBaseCurrency: Optional['DecimalValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Ledger: Optional['StringValue']
    Module: Optional['StringValue']
    PeriodID: Optional['StringValue']
    Project: Optional['StringValue']
    ProjectTask: Optional['StringValue']
    RefNumber: Optional['StringValue']
    Subaccount: Optional['StringValue']
    TransactionDate: Optional['DateTimeValue']
    TransactionDescription: Optional['StringValue']
    TransactionType: Optional['StringValue']
    Posted: Optional['BooleanValue']
    Released: Optional['BooleanValue']


@dataclass
class AccountGroup(BaseDataClassModel):
    AccountGroupID: Optional['StringValue']
    Active: Optional['BooleanValue']
    Attributes: List[Optional['AttributeValue']]
    DefaultAccountID: Optional['StringValue']
    Description: Optional['StringValue']
    Expense: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    SortOrder: Optional['ShortValue']
    Type: Optional['StringValue']


@dataclass
class AccountGroupCustomAction(BaseDataClassModel):
    entity: Optional['AccountGroup']
    parameters: Optional[Any]


@dataclass
class AccountSummaryInquiry(BaseDataClassModel):
    AccountClass: Optional['StringValue']
    Branch: Optional['StringValue']
    Ledger: Optional['StringValue']
    Period: Optional['StringValue']
    Results: List[Optional['AccountSummaryRow']]
    Subaccount: Optional['StringValue']


@dataclass
class AccountSummaryInquiryCustomAction(BaseDataClassModel):
    entity: Optional['AccountSummaryInquiry']
    parameters: Optional[Any]


@dataclass
class AccountSummaryRow(BaseDataClassModel):
    Account: Optional['StringValue']
    AccountClass: Optional['StringValue']
    BeginningBalance: Optional['DecimalValue']
    Branch: Optional['StringValue']
    ConsolidationAccount: Optional['StringValue']
    CreditTotal: Optional['DecimalValue']
    CurrencyBeginningBalance: Optional['DecimalValue']
    CurrencyCreditTotal: Optional['DecimalValue']
    CurrencyDebitTotal: Optional['DecimalValue']
    CurrencyEndingBalance: Optional['DecimalValue']
    CurrencyID: Optional['StringValue']
    CurrencyPtdTotal: Optional['DecimalValue']
    DebitTotal: Optional['DecimalValue']
    Description: Optional['StringValue']
    EndingBalance: Optional['DecimalValue']
    LastActivity: Optional['StringValue']
    LedgerID: Optional['IntValue']
    PtdTotal: Optional['DecimalValue']
    Subaccount: Optional['StringValue']
    Type: Optional['StringValue']


@dataclass
class ActivateProject(BaseDataClassModel):
    entity: Optional['Project']


@dataclass
class ActivateProjectTask(BaseDataClassModel):
    entity: Optional['ProjectTask']


@dataclass
class ActivateProjectTemplate(BaseDataClassModel):
    entity: Optional['ProjectTemplate']


@dataclass
class Activity(BaseDataClassModel):
    Body: Optional['StringValue']
    Date: Optional['DateTimeValue']
    Internal: Optional['BooleanValue']
    NoteID: Optional['GuidValue']
    Owner: Optional['StringValue']
    Status: Optional['StringValue']
    Summary: Optional['StringValue']
    Task: Optional['StringValue']
    TimeActivity: Optional['TimeActivity']
    Type: Optional['StringValue']
    Workgroup: Optional['StringValue']
    CreatedByID: Optional['StringValue']
    CreatedDateTime: Optional['DateTimeValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    RelatedEntityType: Optional['StringValue']
    RelatedEntityNoteID: Optional['GuidValue']
    RelatedEntityDescription: Optional['StringValue']


@dataclass
class ActivityCustomAction(BaseDataClassModel):
    entity: Optional['Activity']
    parameters: Optional[Any]


@dataclass
class ActivityDetail(BaseDataClassModel):
    Billable: Optional['BooleanValue']
    Overtime: Optional['StringValue']
    BillableOvertime: Optional['StringValue']
    BillableTime: Optional['StringValue']
    Category: Optional['StringValue']
    CostCode: Optional['StringValue']
    CreatedDateTime: Optional['DateTimeValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    CreatedByID: Optional['StringValue']
    NoteID: Optional['GuidValue']
    Owner: Optional['StringValue']
    Project: Optional['StringValue']
    ProjectTask: Optional['StringValue']
    RefNoteID: Optional['GuidValue']
    Released: Optional['BooleanValue']
    StartDate: Optional['DateTimeValue']
    Status: Optional['StringValue']
    Summary: Optional['StringValue']
    TimeSpent: Optional['StringValue']
    Type: Optional['StringValue']
    WorkgroupID: Optional['StringValue']


@dataclass
class Address(BaseDataClassModel):
    AddressLine1: Optional['StringValue']
    AddressLine2: Optional['StringValue']
    City: Optional['StringValue']
    Country: Optional['StringValue']
    PostalCode: Optional['StringValue']
    State: Optional['StringValue']
    Validated: Optional['BooleanValue']


@dataclass
class AllowBilling(BaseDataClassModel):
    entity: Optional['ServiceOrder']


@dataclass
class AmazonStore(BaseDataClassModel):
    BindingName: Optional['StringValue']
    LocaleName: Optional['StringValue']
    Marketplace: Optional['StringValue']
    RefreshToken: Optional['StringValue']
    Region: Optional['StringValue']
    SellerPartnerId: Optional['StringValue']
    Active: Optional['BooleanValue']
    Default: Optional['BooleanValue']


@dataclass
class AmazonStoreCustomAction(BaseDataClassModel):
    entity: Optional['AmazonStore']
    parameters: Optional[Any]


@dataclass
class AppAttributes(BaseDataClassModel):
    Attribute: Optional['StringValue']
    RefNoteID: Optional['GuidValue']
    Required: Optional['BooleanValue']
    Value: Optional['StringValue']


@dataclass
class AppDetails(BaseDataClassModel):
    Account: Optional['StringValue']
    ActualAmount: Optional['DecimalValue']
    ActualDuration: Optional['StringValue']
    ActualQty: Optional['DecimalValue']
    AppointmentNbr: Optional['StringValue']
    Billable: Optional['BooleanValue']
    BillableAmount: Optional['DecimalValue']
    BillableQty: Optional['DecimalValue']
    BillingRule: Optional['StringValue']
    Branch: Optional['StringValue']
    ComponentID: Optional['StringValue']
    ComponentLineRef: Optional['StringValue']
    CostCode: Optional['StringValue']
    CoveredQty: Optional['DecimalValue']
    CuryUnitCost: Optional['DecimalValue']
    Description: Optional['StringValue']
    DiscountAmount: Optional['DecimalValue']
    DiscountPercent: Optional['DecimalValue']
    EquipmentAction: Optional['StringValue']
    EquipmentActionComment: Optional['StringValue']
    EstimatedAmount: Optional['DecimalValue']
    EstimatedDuration: Optional['StringValue']
    EstimatedQty: Optional['DecimalValue']
    ExtPrice: Optional['DecimalValue']
    InventoryID: Optional['StringValue']
    LineNbr: Optional['IntValue']
    LineRef: Optional['StringValue']
    LineStatus: Optional['StringValue']
    LineType: Optional['StringValue']
    Location: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    ManualPrice: Optional['BooleanValue']
    MarkforPO: Optional['BooleanValue']
    ModelEquipmentLineRef: Optional['StringValue']
    OverageQty: Optional['DecimalValue']
    OverageUnitPrice: Optional['DecimalValue']
    PickupDeliveryAction: Optional['StringValue']
    PickupDeliveryLineRef: Optional['StringValue']
    PickupDeliveryServiceID: Optional['StringValue']
    POCompleted: Optional['BooleanValue']
    PONbr: Optional['StringValue']
    POStatus: Optional['StringValue']
    PrepaidItem: Optional['BooleanValue']
    ProjectTask: Optional['StringValue']
    RelatedDocNbr: Optional['StringValue']
    ServiceContractItem: Optional['BooleanValue']
    ServiceOrderLineRef: Optional['StringValue']
    ServiceOrderType: Optional['StringValue']
    SortOrder: Optional['IntValue']
    StaffMemberID: Optional['StringValue']
    Subaccount: Optional['StringValue']
    Subitem: Optional['StringValue']
    TargetEquipmentID: Optional['StringValue']
    TaxCategory: Optional['StringValue']
    UnitPrice: Optional['DecimalValue']
    UOM: Optional['StringValue']
    Warehouse: Optional['StringValue']
    Warranty: Optional['BooleanValue']


@dataclass
class AppFinancialSettings(BaseDataClassModel):
    BillingCustomer: Optional['StringValue']
    BillingCycle: Optional['StringValue']
    BillingLocation: Optional['StringValue']
    Branch: Optional['StringValue']
    Commissionable: Optional['BooleanValue']
    CustomerTaxZone: Optional['StringValue']
    RunBillingFor: Optional['StringValue']
    Salesperson: Optional['StringValue']
    TaxCalculationMode: Optional['StringValue']


@dataclass
class AppLogs(BaseDataClassModel):
    AddtoActualDuration: Optional['BooleanValue']
    AppointmentNbr: Optional['StringValue']
    Approved: Optional['BooleanValue']
    BillableAmount: Optional['DecimalValue']
    BillableLabor: Optional['BooleanValue']
    BillableTime: Optional['StringValue']
    CostCode: Optional['StringValue']
    Description: Optional['StringValue']
    DetailLineRef: Optional['StringValue']
    Duration: Optional['StringValue']
    EarningType: Optional['StringValue']
    EndDate: Optional['DateTimeValue']
    EndTime: Optional['DateTimeValue']
    InventoryID: Optional['StringValue']
    LaborItemID: Optional['StringValue']
    LineNbr: Optional['IntValue']
    LogLineRef: Optional['StringValue']
    LogLineStatus: Optional['StringValue']
    ManageTimeManually: Optional['BooleanValue']
    ProjectTask: Optional['StringValue']
    ServiceOrderType: Optional['StringValue']
    StaffMember: Optional['StringValue']
    StartDate: Optional['DateTimeValue']
    StartTime: Optional['DateTimeValue']
    TimeCardRefNbr: Optional['StringValue']
    TrackTime: Optional['BooleanValue']
    Travel: Optional['BooleanValue']


@dataclass
class AppOtherInformation(BaseDataClassModel):
    BatchNbr: Optional['StringValue']
    Description: Optional['StringValue']
    DocumentType: Optional['StringValue']
    InvoiceNbr: Optional['StringValue']
    IssueReferenceNbr: Optional['StringValue']
    RecurrenceDescription: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    RouteID: Optional['StringValue']
    RouteNbr: Optional['StringValue']
    SourceScheduleID: Optional['StringValue']
    SourceServiceContractID: Optional['StringValue']


@dataclass
class AppPrepayments(BaseDataClassModel):
    ApplicationDate: Optional['DateTimeValue']
    AppliedtoOrders: Optional['DecimalValue']
    AvailableBalance: Optional['DecimalValue']
    CashAccount: Optional['IntValue']
    Currency: Optional['StringValue']
    PaymentAmount: Optional['DecimalValue']
    PaymentMethod: Optional['StringValue']
    PaymentRef: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    SourceAppointmentNbr: Optional['StringValue']
    Status: Optional['StringValue']
    Type: Optional['StringValue']


@dataclass
class AppProfitability(BaseDataClassModel):
    ActualAmount: Optional['DecimalValue']
    ActualDuration: Optional['StringValue']
    ActualQuantity: Optional['DecimalValue']
    BillableAmount: Optional['DecimalValue']
    BillableQuantity: Optional['DecimalValue']
    ExtCost: Optional['DecimalValue']
    Description: Optional['StringValue']
    EstimatedAmount: Optional['DecimalValue']
    EstimatedQty: Optional['DecimalValue']
    InventoryID: Optional['StringValue']
    LineRef: Optional['StringValue']
    LineType: Optional['StringValue']
    Profit: Optional['DecimalValue']
    ProfitPercent: Optional['DecimalValue']
    StaffMember: Optional['StringValue']
    UnitCost: Optional['DecimalValue']
    UnitPrice: Optional['DecimalValue']


@dataclass
class AppRecalcExternalTax(BaseDataClassModel):
    entity: Optional['Appointment']


@dataclass
class AppResourceEquipment(BaseDataClassModel):
    AppointmentNbr: Optional['StringValue']
    Comment: Optional['StringValue']
    Description: Optional['StringValue']
    EquipmentID: Optional['StringValue']
    ServiceOrderType: Optional['StringValue']


@dataclass
class AppStaff(BaseDataClassModel):
    AppointmentNbr: Optional['StringValue']
    CostCode: Optional['StringValue']
    Description: Optional['StringValue']
    DetailLineRef: Optional['StringValue']
    EarningType: Optional['StringValue']
    InventoryID: Optional['StringValue']
    LaborItem: Optional['StringValue']
    LineNbr: Optional['IntValue']
    LineRef: Optional['StringValue']
    PrimaryDriver: Optional['BooleanValue']
    Project: Optional['StringValue']
    ProjectTask: Optional['StringValue']
    RouteDriver: Optional['BooleanValue']
    ServiceOrderType: Optional['StringValue']
    StaffMember: Optional['StringValue']
    StaffType: Optional['StringValue']
    TrackTime: Optional['BooleanValue']


@dataclass
class AppTaxDetails(BaseDataClassModel):
    AppointmentNbr: Optional['StringValue']
    IncludeinVATExemptTotal: Optional['BooleanValue']
    PendingVAT: Optional['BooleanValue']
    RecordID: Optional['IntValue']
    ReverseVAT: Optional['BooleanValue']
    ServiceOrderType: Optional['StringValue']
    StatisticalVAT: Optional['BooleanValue']
    TaxableAmount: Optional['DecimalValue']
    TaxAmount: Optional['DecimalValue']
    TaxID: Optional['StringValue']
    TaxRate: Optional['DecimalValue']
    TaxType: Optional['StringValue']


@dataclass
class AppTotals(BaseDataClassModel):
    ActualTotal: Optional['DecimalValue']
    AppointmentBillableTotal: Optional['DecimalValue']
    AppointmentTotal: Optional['DecimalValue']
    BillableLaborTotal: Optional['DecimalValue']
    BillableTotal: Optional['DecimalValue']
    EstimatedTotal: Optional['DecimalValue']
    LineTotal: Optional['DecimalValue']
    PrepaymentApplied: Optional['DecimalValue']
    PrepaymentReceived: Optional['DecimalValue']
    PrepaymentRemaining: Optional['DecimalValue']
    ServiceOrderBillableUnpaidBalance: Optional['DecimalValue']
    ServiceOrderTotal: Optional['DecimalValue']
    ServiceOrderUnpaidBalance: Optional['DecimalValue']
    TaxTotal: Optional['DecimalValue']
    VATExemptTotal: Optional['DecimalValue']
    VATTaxableTotal: Optional['DecimalValue']


@dataclass
class ApplicableWage(BaseDataClassModel):
    BenefitIncreasingApplWage: Optional['BenefitIncreasingApplWage']
    DeductionsDecreasingApplWage: Optional['DeductionDecreasingApplWage']
    EarningIncreasingApplWage: Optional['EarningIncreasingApplWage']
    EmployeeTaxesDecreasingApplWage: Optional['TaxesDecreasingApplWage']
    EmployerTaxesIncreasingApplWage: Optional['EmployerTaxesIncreasingApplWage']


@dataclass
class Appointment(BaseDataClassModel):
    ActualDuration: Optional['StringValue']
    ActualEndDate: Optional['DateTimeValue']
    ActualEndTime: Optional['DateTimeValue']
    ActualHandleManually: Optional['BooleanValue']
    ActualServiceDuration: Optional['StringValue']
    ActualStartDate: Optional['DateTimeValue']
    ActualStartTime: Optional['DateTimeValue']
    AppointmentNbr: Optional['StringValue']
    AppointmentTotal: Optional['DecimalValue']
    Attributes: List[Optional['AppAttributes']]
    BranchLocation: Optional['StringValue']
    Confirmed: Optional['BooleanValue']
    CostTotal: Optional['DecimalValue']
    Customer: Optional['StringValue']
    DefaultProjectTask: Optional['StringValue']
    Description: Optional['StringValue']
    Details: List[Optional['AppDetails']]
    EstimatedServiceDuration: Optional['StringValue']
    FinancialSettings: Optional['AppFinancialSettings']
    Finished: Optional['BooleanValue']
    Hold: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Location: Optional['StringValue']
    Logs: List[Optional['AppLogs']]
    OptimizationResult: Optional['StringValue']
    OtherInformation: Optional['AppOtherInformation']
    Override: Optional['BooleanValue']
    Prepayments: List[Optional['AppPrepayments']]
    Profit: Optional['DecimalValue']
    Profitability: List[Optional['AppProfitability']]
    Project: Optional['StringValue']
    ResourceEquipment: List[Optional['AppResourceEquipment']]
    ScheduledDuration: Optional['StringValue']
    ScheduledEndDate: Optional['DateTimeValue']
    ScheduledEndTime: Optional['DateTimeValue']
    ScheduledHandleManually: Optional['BooleanValue']
    ScheduledStartDate: Optional['DateTimeValue']
    ScheduledStartTime: Optional['DateTimeValue']
    ServiceOrderNbr: Optional['StringValue']
    ServiceOrderType: Optional['StringValue']
    Staff: List[Optional['AppStaff']]
    Status: Optional['StringValue']
    TaxDetails: List[Optional['AppTaxDetails']]
    TaxTotal: Optional['DecimalValue']
    Totals: Optional['AppTotals']
    UnreachedCustomer: Optional['BooleanValue']
    ValidatedbyDispatcher: Optional['BooleanValue']
    WaitingforPurchasedItems: Optional['BooleanValue']
    WorkflowStage: Optional['StringValue']


@dataclass
class AppointmentCustomAction(BaseDataClassModel):
    entity: Optional['Appointment']
    parameters: Optional[Any]


@dataclass
class Approval(BaseDataClassModel):
    ApprovedBy: Optional['StringValue']
    ApprovedByName: Optional['StringValue']
    Approver: Optional['StringValue']
    ApproverName: Optional['StringValue']
    Date: Optional['DateTimeValue']
    Status: Optional['StringValue']
    Workgroup: Optional['StringValue']


@dataclass
class ApproveChangeOrder(BaseDataClassModel):
    entity: Optional['ChangeOrder']


@dataclass
class ApproveExpenseClaim(BaseDataClassModel):
    entity: Optional['ExpenseClaim']


@dataclass
class ApproveExpenseReceipt(BaseDataClassModel):
    entity: Optional['ExpenseReceipt']


@dataclass
class ApproveProFormaInvoice(BaseDataClassModel):
    entity: Optional['ProFormaInvoice']


@dataclass
class ApproveProject(BaseDataClassModel):
    entity: Optional['Project']


@dataclass
class ArchiveEmail(BaseDataClassModel):
    entity: Optional['Email']


@dataclass
class AssignCase(BaseDataClassModel):
    entity: Optional['Case']


@dataclass
class AttributeDefinition(BaseDataClassModel):
    AttributeID: Optional['StringValue']
    ControlType: Optional['StringValue']
    CreatedDateTime: Optional['DateTimeValue']
    Description: Optional['StringValue']
    EntryMask: Optional['StringValue']
    Internal: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    RegExp: Optional['StringValue']
    Values: List[Optional['AttributeDefinitionValue']]


@dataclass
class AttributeDefinitionCustomAction(BaseDataClassModel):
    entity: Optional['AttributeDefinition']
    parameters: Optional[Any]


@dataclass
class AttributeDefinitionValue(BaseDataClassModel):
    Description: Optional['StringValue']
    Disabled: Optional['BooleanValue']
    SortOrder: Optional['ShortValue']
    ValueID: Optional['StringValue']


@dataclass
class AttributeValue(BaseDataClassModel):
    AttributeID: Optional['StringValue']
    AttributeDescription: Optional['StringValue']
    IsActive: Optional['BooleanValue']
    RefNoteID: Optional['GuidValue']
    Required: Optional['BooleanValue']
    Value: Optional['StringValue']
    ValueDescription: Optional['StringValue']


@dataclass
class AutoRecalculateDiscounts(BaseDataClassModel):
    entity: Optional['SalesOrder']


@dataclass
class BCRoleAssignment(BaseDataClassModel):
    RoleAssignmentID: Optional['IntValue']
    BAccountID: Optional['IntValue']
    ContactID: Optional['IntValue']
    LocationCD: Optional['StringValue']
    Role: Optional['StringValue']
    CreatedDateTime: Optional['DateTimeValue']
    LastModifiedDateTime: Optional['DateTimeValue']


@dataclass
class BatchDeductionOrBenefitDetail(BaseDataClassModel):
    BatchNumber: Optional['StringValue']
    BenefitAmount: Optional['DecimalValue']
    BenefitCalculationMethod: Optional['StringValue']
    BenefitPercent: Optional['DecimalValue']
    ContributionType: Optional['StringValue']
    DeductionAmount: Optional['DecimalValue']
    DeductionCalculationMethod: Optional['StringValue']
    DeductionCode: Optional['StringValue']
    DeductionPercent: Optional['DecimalValue']
    Description: Optional['StringValue']
    Enabled: Optional['BooleanValue']
    IsGarnishment: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']


@dataclass
class BatchEarningDetail(BaseDataClassModel):
    Account: Optional['StringValue']
    AllowCopy: Optional['BooleanValue']
    Amount: Optional['DecimalValue']
    Branch: Optional['StringValue']
    CertifiedJob: Optional['BooleanValue']
    Code: Optional['StringValue']
    CostCode: Optional['StringValue']
    Date: Optional['DateTimeValue']
    Description: Optional['StringValue']
    Employee: Optional['StringValue']
    EmployeeName: Optional['StringValue']
    Hours: Optional['DecimalValue']
    LaborItem: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Location: Optional['StringValue']
    ManualRate: Optional['BooleanValue']
    Project: Optional['StringValue']
    Rate: Optional['DecimalValue']
    ExcelRecordID: Optional['StringValue']
    ShiftCode: Optional['StringValue']
    Subaccount: Optional['StringValue']
    Task: Optional['StringValue']
    TimeActivity: Optional['StringValue']
    UnionLocal: Optional['StringValue']
    Units: Optional['DecimalValue']
    UnitType: Optional['StringValue']
    WCCCode: Optional['StringValue']


@dataclass
class BatchOvertimeRules(BaseDataClassModel):
    ApplyOvertimeRulesfortheDocument: Optional['BooleanValue']
    OvertimeRulesDetails: List[Optional['BatchOvertimeRulesDetail']]


@dataclass
class BatchOvertimeRulesDetail(BaseDataClassModel):
    DayofWeek: Optional['StringValue']
    Description: Optional['StringValue']
    DisbursingEarningType: Optional['StringValue']
    Enabled: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Multiplier: Optional['DecimalValue']
    OvertimeRule: Optional['StringValue']
    Project: Optional['StringValue']
    State: Optional['StringValue']
    ThresholdforOvertimehours: Optional['DecimalValue']
    Type: Optional['StringValue']
    UnionLocal: Optional['StringValue']


@dataclass
class BenefitIncreasingApplWage(BaseDataClassModel):
    BenefitIncreasingApplWageDetails: List[Optional['BenefitIncreasingApplWageDetail']]
    InclusionType: Optional['StringValue']


@dataclass
class BenefitIncreasingApplWageDetail(BaseDataClassModel):
    BenefitCode: Optional['StringValue']
    Description: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']


@dataclass
class BigCommerceStores(BaseDataClassModel):
    AccessToken: Optional['StringValue']
    Active: Optional['BooleanValue']
    APIPath: Optional['StringValue']
    ClientID: Optional['StringValue']
    Connector: Optional['StringValue']
    Default: Optional['BooleanValue']
    StoreAdminPath: Optional['StringValue']
    StoreName: Optional['StringValue']
    WebDAVPassword: Optional['StringValue']
    WebDAVPath: Optional['StringValue']
    WebDAVUsername: Optional['StringValue']


@dataclass
class BigCommerceStoresCustomAction(BaseDataClassModel):
    entity: Optional['BigCommerceStores']
    parameters: Optional[Any]


@dataclass
class Bill(BaseDataClassModel):
    Amount: Optional['DecimalValue']
    Applications: List[Optional['BillApplicationDetail']]
    ApprovedForPayment: Optional['BooleanValue']
    Balance: Optional['DecimalValue']
    BranchID: Optional['StringValue']
    CashAccount: Optional['StringValue']
    CurrencyID: Optional['StringValue']
    Date: Optional['DateTimeValue']
    Description: Optional['StringValue']
    Details: List[Optional['BillDetail']]
    DueDate: Optional['DateTimeValue']
    Hold: Optional['BooleanValue']
    LocationID: Optional['StringValue']
    PostPeriod: Optional['StringValue']
    Project: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    Status: Optional['StringValue']
    TaxDetails: List[Optional['BillTaxDetail']]
    TaxTotal: Optional['DecimalValue']
    Terms: Optional['StringValue']
    Type: Optional['StringValue']
    Vendor: Optional['StringValue']
    VendorRef: Optional['StringValue']
    IsTaxValid: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']


@dataclass
class BillApplicationDetail(BaseDataClassModel):
    AmountPaid: Optional['DecimalValue']
    Balance: Optional['DecimalValue']
    DocType: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    Status: Optional['StringValue']


@dataclass
class BillCustomAction(BaseDataClassModel):
    entity: Optional['Bill']
    parameters: Optional[Any]


@dataclass
class BillDetail(BaseDataClassModel):
    Account: Optional['StringValue']
    Amount: Optional['DecimalValue']
    Branch: Optional['StringValue']
    CalculateDiscountsOnImport: Optional['BooleanValue']
    CostCode: Optional['StringValue']
    Description: Optional['StringValue']
    ExtendedCost: Optional['DecimalValue']
    InventoryID: Optional['StringValue']
    LCLineNbr: Optional['IntValue']
    LCNbr: Optional['StringValue']
    LCType: Optional['StringValue']
    NonBillable: Optional['BooleanValue']
    POLine: Optional['IntValue']
    POOrderNbr: Optional['StringValue']
    POOrderType: Optional['StringValue']
    POReceiptLine: Optional['IntValue']
    POReceiptType: Optional['StringValue']
    POReceiptNbr: Optional['StringValue']
    Project: Optional['StringValue']
    ProjectTask: Optional['StringValue']
    Qty: Optional['DecimalValue']
    Subaccount: Optional['StringValue']
    TaxCategory: Optional['StringValue']
    TransactionDescription: Optional['StringValue']
    UnitCost: Optional['DecimalValue']
    UOM: Optional['StringValue']


@dataclass
class BillTaxDetail(BaseDataClassModel):
    TaxableAmount: Optional['DecimalValue']
    TaxAmount: Optional['DecimalValue']
    TaxID: Optional['StringValue']
    TaxRate: Optional['DecimalValue']


@dataclass
class BillToSettings(BaseDataClassModel):
    BillToAddress: Optional['Address']
    BillToAddressOverride: Optional['BooleanValue']
    BillToContact: Optional['DocContact']
    BillToContactOverride: Optional['BooleanValue']
    CustomerLocation: Optional['StringValue']


@dataclass
class BooleanValue(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class BoxStockItem(BaseDataClassModel):
    BoxID: Optional['StringValue']
    Description: Optional['StringValue']
    MaxQty: Optional['DecimalValue']
    MaxVolume: Optional['DecimalValue']
    MaxWeight: Optional['DecimalValue']
    Qty: Optional['DecimalValue']
    UOM: Optional['StringValue']


@dataclass
class Budget(BaseDataClassModel):
    Branch: Optional['StringValue']
    ComparetoBranch: Optional['StringValue']
    ComparetoLedger: Optional['StringValue']
    ComparetoYear: Optional['StringValue']
    Details: List[Optional['BudgetDetail']]
    FinancialYear: Optional['StringValue']
    Ledger: Optional['StringValue']
    SubaccountFilter: Optional['StringValue']
    TreeNodeFilter: Optional['StringValue']


@dataclass
class BudgetCustomAction(BaseDataClassModel):
    entity: Optional['Budget']
    parameters: Optional[Any]


@dataclass
class BudgetDetail(BaseDataClassModel):
    Account: Optional['StringValue']
    Amount: Optional['DecimalValue']
    Branch: Optional['StringValue']
    CreatedBy: Optional['StringValue']
    Description: Optional['StringValue']
    DistributedAmount: Optional['DecimalValue']
    FinancialYear: Optional['StringValue']
    GroupID: Optional['GuidValue']
    LastModifiedBy: Optional['StringValue']
    LedgerID: Optional['StringValue']
    Node: Optional['BooleanValue']
    Period01: Optional['DecimalValue']
    Period02: Optional['DecimalValue']
    Period03: Optional['DecimalValue']
    Period04: Optional['DecimalValue']
    Period05: Optional['DecimalValue']
    Period06: Optional['DecimalValue']
    Period07: Optional['DecimalValue']
    Period08: Optional['DecimalValue']
    Period09: Optional['DecimalValue']
    Period10: Optional['DecimalValue']
    Period11: Optional['DecimalValue']
    Period12: Optional['DecimalValue']
    Period13: Optional['DecimalValue']
    Released: Optional['BooleanValue']
    Subaccount: Optional['StringValue']


@dataclass
class BusinessAccount(BaseDataClassModel):
    AccountRef: Optional['StringValue']
    Activities: List[Optional['ActivityDetail']]
    Attributes: List[Optional['AttributeValue']]
    BusinessAccountID: Optional['StringValue']
    Campaigns: List[Optional['CampaignDetail']]
    Cases: List[Optional['BusinessAccountCaseDetail']]
    ClassID: Optional['StringValue']
    Contacts: List[Optional['BusinessAccountContact']]
    Contracts: List[Optional['BusinessAccountContract']]
    DefaultLocationSettings: Optional['BusinessAccountDefaultLocationSetting']
    Duplicate: Optional['StringValue']
    Duplicates: List[Optional['DuplicateDetail']]
    LastIncomingActivity: Optional['DateTimeValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    LastOutgoingActivity: Optional['DateTimeValue']
    Locations: List[Optional['BusinessAccountLocation']]
    MainAddress: Optional['Address']
    MainAddressValidated: Optional['BooleanValue']
    MainContact: Optional['BusinessAccountMainContact']
    MarketingLists: List[Optional['MarketingListDetail']]
    Name: Optional['StringValue']
    Opportunities: List[Optional['BusinessAccountOpportunityDetail']]
    Orders: List[Optional['BusinessAccountOrder']]
    Owner: Optional['StringValue']
    OwnerEmployeeName: Optional['StringValue']
    ParentAccount: Optional['StringValue']
    PrimaryContact: Optional['Contact']
    Relations: List[Optional['RelationDetail']]
    ShippingAddress: Optional['Address']
    ShippingAddressOverride: Optional['BooleanValue']
    ShippingAddressValidated: Optional['BooleanValue']
    ShippingContact: Optional['BusinessAccountShippingContact']
    SourceCampaign: Optional['StringValue']
    Status: Optional['StringValue']
    Type: Optional['StringValue']
    Workgroup: Optional['StringValue']
    WorkgroupDescription: Optional['StringValue']
    NoteID: Optional['GuidValue']
    CurrencyID: Optional['StringValue']
    EnableCurrencyOverride: Optional['BooleanValue']


@dataclass
class BusinessAccountCaseDetail(BaseDataClassModel):
    CaseID: Optional['StringValue']
    ClassID: Optional['StringValue']
    ClosingDate: Optional['DateTimeValue']
    Contract: Optional['StringValue']
    DateReported: Optional['DateTimeValue']
    Estimation: Optional['StringValue']
    InitialResponse: Optional['StringValue']
    Owner: Optional['StringValue']
    Reason: Optional['StringValue']
    Severity: Optional['StringValue']
    Status: Optional['StringValue']
    Subject: Optional['StringValue']
    Workgroup: Optional['StringValue']


@dataclass
class BusinessAccountClassAttributeDetail(BaseDataClassModel):
    Active: Optional['BooleanValue']
    AttributeID: Optional['StringValue']
    DefaultValue: Optional['StringValue']
    Description: Optional['StringValue']
    Required: Optional['BooleanValue']
    SortOrder: Optional['ShortValue']


@dataclass
class BusinessAccountContact(BaseDataClassModel):
    Active: Optional['BooleanValue']
    City: Optional['StringValue']
    ContactID: Optional['IntValue']
    DisplayName: Optional['StringValue']
    Email: Optional['StringValue']
    JobTitle: Optional['StringValue']
    Owner: Optional['StringValue']
    Phone1: Optional['StringValue']
    Type: Optional['StringValue']
    Workgroup: Optional['StringValue']


@dataclass
class BusinessAccountContract(BaseDataClassModel):
    BusinessAccountID: Optional['StringValue']
    BusinessAccountName: Optional['StringValue']
    ContractID: Optional['StringValue']
    Description: Optional['StringValue']
    ExpirationDate: Optional['DateTimeValue']
    Location: Optional['StringValue']
    Status: Optional['StringValue']


@dataclass
class BusinessAccountCustomAction(BaseDataClassModel):
    entity: Optional['BusinessAccount']
    parameters: Optional[Any]


@dataclass
class BusinessAccountDefaultLocationSetting(BaseDataClassModel):
    FOBPoint: Optional['StringValue']
    Insurance: Optional['BooleanValue']
    LeadTimeInDays: Optional['ShortValue']
    LocationName: Optional['StringValue']
    OrderPriority: Optional['ShortValue']
    PriceClass: Optional['StringValue']
    ResidentialDelivery: Optional['BooleanValue']
    SaturdayDelivery: Optional['BooleanValue']
    ShippingBranch: Optional['StringValue']
    ShippingRule: Optional['StringValue']
    ShippingTerms: Optional['StringValue']
    ShippingZone: Optional['StringValue']
    ShipVia: Optional['StringValue']
    TaxRegistrationID: Optional['StringValue']
    TaxZone: Optional['StringValue']
    Warehouse: Optional['StringValue']


@dataclass
class BusinessAccountLocation(BaseDataClassModel):
    Active: Optional['BooleanValue']
    City: Optional['StringValue']
    Country: Optional['StringValue']
    Default: Optional['BooleanValue']
    LocationID: Optional['StringValue']
    LocationName: Optional['StringValue']
    PriceClass: Optional['StringValue']
    SalesAccount: Optional['StringValue']
    SalesSubaccount: Optional['StringValue']
    State: Optional['StringValue']
    TaxZone: Optional['StringValue']


@dataclass
class BusinessAccountMainContact(BaseDataClassModel):
    Attention: Optional['StringValue']
    CompanyName: Optional['StringValue']
    Email: Optional['StringValue']
    Fax: Optional['StringValue']
    JobTitle: Optional['StringValue']
    LanguageOrLocale: Optional['StringValue']
    Phone1: Optional['StringValue']
    Phone2: Optional['StringValue']
    Web: Optional['StringValue']


@dataclass
class BusinessAccountOpportunityDetail(BaseDataClassModel):
    BusinessAccountID: Optional['StringValue']
    BusinessAccountName: Optional['StringValue']
    CurrencyID: Optional['StringValue']
    DisplayName: Optional['StringValue']
    Estimation: Optional['DateTimeValue']
    Owner: Optional['StringValue']
    Probability: Optional['IntValue']
    Stage: Optional['StringValue']
    Status: Optional['StringValue']
    Subject: Optional['StringValue']
    Total: Optional['DecimalValue']
    Workgroup: Optional['StringValue']


@dataclass
class BusinessAccountOrder(BaseDataClassModel):
    CurrencyID: Optional['StringValue']
    CustomerOrder: Optional['StringValue']
    Description: Optional['StringValue']
    OrderedQty: Optional['DecimalValue']
    OrderNbr: Optional['StringValue']
    OrderTotal: Optional['DecimalValue']
    OrderType: Optional['StringValue']
    OrderVolume: Optional['DecimalValue']
    OrderWeight: Optional['DecimalValue']
    RequestedOn: Optional['DateTimeValue']
    ScheduledShipment: Optional['DateTimeValue']
    ShippingZone: Optional['StringValue']
    ShipVia: Optional['StringValue']
    Status: Optional['StringValue']


@dataclass
class BusinessAccountPaymentInstructionDetail(BaseDataClassModel):
    Description: Optional['StringValue']
    LocationID: Optional['IntValue']
    PaymentInstructionsID: Optional['StringValue']
    PaymentMethod: Optional['StringValue']
    Value: Optional['StringValue']


@dataclass
class BusinessAccountShippingContact(BaseDataClassModel):
    Attention: Optional['StringValue']
    Email: Optional['StringValue']
    Fax: Optional['StringValue']
    JobTitle: Optional['StringValue']
    Phone1: Optional['StringValue']
    Phone2: Optional['StringValue']
    Override: Optional['BooleanValue']


@dataclass
class ByteValue(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class CalendarSettings(BaseDataClassModel):
    Friday: Optional['BooleanValue']
    FridayEndTime: Optional['DateTimeValue']
    FridayStartTime: Optional['DateTimeValue']
    FriUnpaidBreakTime: Optional['StringValue']
    Monday: Optional['BooleanValue']
    MondayEndTime: Optional['DateTimeValue']
    MondayStartTime: Optional['DateTimeValue']
    MonUnpaidBreakTime: Optional['StringValue']
    SatUnpaidBreakTime: Optional['StringValue']
    Saturday: Optional['BooleanValue']
    SaturdayEndTime: Optional['DateTimeValue']
    SaturdayStartTime: Optional['DateTimeValue']
    Sunday: Optional['BooleanValue']
    SundayEndTime: Optional['DateTimeValue']
    SundayStartTime: Optional['DateTimeValue']
    SunUnpaidBreakTime: Optional['StringValue']
    Thursday: Optional['BooleanValue']
    ThursdayEndTime: Optional['DateTimeValue']
    ThursdayStartTime: Optional['DateTimeValue']
    ThuUnpaidBreakTime: Optional['StringValue']
    Tuesday: Optional['BooleanValue']
    TuesdayEndTime: Optional['DateTimeValue']
    TuesdayStartTime: Optional['DateTimeValue']
    TueUnpaidBreakTime: Optional['StringValue']
    Wednesday: Optional['BooleanValue']
    WednesdayEndTime: Optional['DateTimeValue']
    WednesdayStartTime: Optional['DateTimeValue']
    WedUnpaidBreakTime: Optional['StringValue']


@dataclass
class CampaignDetail(BaseDataClassModel):
    CampaignID: Optional['StringValue']
    CampaignName: Optional['StringValue']
    ContactID: Optional['IntValue']
    Stage: Optional['StringValue']


@dataclass
class CancelActivityEvent(BaseDataClassModel):
    entity: Optional['Event']


@dataclass
class CancelActivityTask(BaseDataClassModel):
    entity: Optional['Task']


@dataclass
class CancelAppointment(BaseDataClassModel):
    entity: Optional['Appointment']


@dataclass
class CancelOrder(BaseDataClassModel):
    entity: Optional['ServiceOrder']


@dataclass
class CancelPhysicalInventory(BaseDataClassModel):
    entity: Optional['PhysicalInventoryReview']


@dataclass
class CancelProject(BaseDataClassModel):
    entity: Optional['Project']


@dataclass
class CancelProjectTask(BaseDataClassModel):
    entity: Optional['ProjectTask']


@dataclass
class CancelSalesOrder(BaseDataClassModel):
    entity: Optional['SalesOrder']


@dataclass
class CancelSendingEmail(BaseDataClassModel):
    entity: Optional['Email']


@dataclass
class CaptureCreditCardPayment(BaseDataClassModel):
    entity: Optional['Payment']


@dataclass
class CardOperation(BaseDataClassModel):
    entity: Optional['Payment']
    parameters: Optional[Any]


@dataclass
class Carrier(BaseDataClassModel):
    CarrierID: Optional['StringValue']
    CarrierUnits: Optional['StringValue']
    CreatedDateTime: Optional['DateTimeValue']
    CustomerAccounts: List[Optional['CarrierCustomerAccount']]
    Description: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    PlugInParameters: List[Optional['CarrierPluginParameter']]
    PlugInType: Optional['StringValue']
    Centimeter: Optional['StringValue']
    Inch: Optional['StringValue']
    Kilogram: Optional['StringValue']
    Pound: Optional['StringValue']
    WarehouseID: Optional['StringValue']


@dataclass
class CarrierCustomAction(BaseDataClassModel):
    entity: Optional['Carrier']
    parameters: Optional[Any]


@dataclass
class CarrierCustomerAccount(BaseDataClassModel):
    Active: Optional['BooleanValue']
    CarrierAccount: Optional['StringValue']
    CustomerID: Optional['StringValue']
    CustomerName: Optional['StringValue']
    Location: Optional['StringValue']
    PostalCode: Optional['StringValue']
    RecordID: Optional['IntValue']


@dataclass
class CarrierPluginParameter(BaseDataClassModel):
    Description: Optional['StringValue']
    PluginID: Optional['StringValue']
    Value: Optional['StringValue']


@dataclass
class Case(BaseDataClassModel):
    Activities: List[Optional['ActivityDetail']]
    Attributes: List[Optional['AttributeValue']]
    Billable: Optional['BooleanValue']
    BillableOvertime: Optional['IntValue']
    BillableTime: Optional['IntValue']
    BusinessAccount: Optional['StringValue']
    BusinessAccountName: Optional['StringValue']
    CaseID: Optional['StringValue']
    ClassID: Optional['StringValue']
    ClosingDate: Optional['DateTimeValue']
    ContactDisplayName: Optional['StringValue']
    ContactID: Optional['IntValue']
    Contract: Optional['StringValue']
    DateReported: Optional['DateTimeValue']
    Description: Optional['StringValue']
    InitialResponse: Optional['StringValue']
    LastActivityDate: Optional['DateTimeValue']
    LastIncomingActivity: Optional['DateTimeValue']
    LastOutgoingActivity: Optional['DateTimeValue']
    Location: Optional['StringValue']
    ManualOverride: Optional['BooleanValue']
    OvertimeSpent: Optional['StringValue']
    Owner: Optional['StringValue']
    OwnerEmployeeName: Optional['StringValue']
    Priority: Optional['StringValue']
    Reason: Optional['StringValue']
    RelatedCases: List[Optional['CaseRelatedCase']]
    Relations: List[Optional['RelationDetail']]
    ResolutionTime: Optional['StringValue']
    Severity: Optional['StringValue']
    SLA: Optional['DateTimeValue']
    Status: Optional['StringValue']
    Subject: Optional['StringValue']
    TimeSpent: Optional['StringValue']
    Workgroup: Optional['StringValue']
    WorkgroupDescription: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    NoteID: Optional['GuidValue']


@dataclass
class CaseCustomAction(BaseDataClassModel):
    entity: Optional['Case']
    parameters: Optional[Any]


@dataclass
class CaseDetail(BaseDataClassModel):
    CaseID: Optional['StringValue']
    ClassID: Optional['StringValue']
    ClosingDate: Optional['DateTimeValue']
    DateReported: Optional['DateTimeValue']
    Estimation: Optional['StringValue']
    InitialResponse: Optional['StringValue']
    Owner: Optional['StringValue']
    Reason: Optional['StringValue']
    Severity: Optional['StringValue']
    Status: Optional['StringValue']
    Subject: Optional['StringValue']
    Workgroup: Optional['StringValue']


@dataclass
class CaseRelatedCase(BaseDataClassModel):
    CaseID: Optional['StringValue']
    Owner: Optional['StringValue']
    ParentCaseID: Optional['StringValue']
    RelationType: Optional['StringValue']
    Status: Optional['StringValue']
    Subject: Optional['StringValue']
    Workgroup: Optional['StringValue']


@dataclass
class CashSale(BaseDataClassModel):
    Amount: Optional['DecimalValue']
    Balance: Optional['DecimalValue']
    CashAccount: Optional['StringValue']
    CreatedDateTime: Optional['DateTimeValue']
    CustomerID: Optional['StringValue']
    Date: Optional['DateTimeValue']
    Description: Optional['StringValue']
    Details: List[Optional['CashSaleDetail']]
    Hold: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    PaymentMethod: Optional['StringValue']
    PaymentRef: Optional['StringValue']
    Project: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    Status: Optional['StringValue']
    TaxTotal: Optional['DecimalValue']
    Type: Optional['StringValue']


@dataclass
class CashSaleCustomAction(BaseDataClassModel):
    entity: Optional['CashSale']
    parameters: Optional[Any]


@dataclass
class CashSaleDetail(BaseDataClassModel):
    Account: Optional['StringValue']
    Amount: Optional['DecimalValue']
    Branch: Optional['StringValue']
    CostCode: Optional['StringValue']
    ExtendedPrice: Optional['DecimalValue']
    InventoryID: Optional['StringValue']
    ProjectTask: Optional['StringValue']
    Qty: Optional['DecimalValue']
    Subaccount: Optional['StringValue']
    TaxCategory: Optional['StringValue']
    TransactionDescription: Optional['StringValue']
    UnitPrice: Optional['DecimalValue']


@dataclass
class CashTransaction(BaseDataClassModel):
    Approved: Optional['BooleanValue']
    CashAccountCD: Optional['StringValue']
    Description: Optional['StringValue']
    Details: List[Optional['CashTransactionDetail']]
    EntryTypeCD: Optional['StringValue']
    ExternalReferenceNumber: Optional['StringValue']
    PostedDate: Optional['DateTimeValue']


@dataclass
class CashTransactionCustomAction(BaseDataClassModel):
    entity: Optional['CashTransaction']
    parameters: Optional[Any]


@dataclass
class CashTransactionDetail(BaseDataClassModel):
    Amount: Optional['DecimalValue']
    AmountDescription: Optional['StringValue']


@dataclass
class CategoryStockItem(BaseDataClassModel):
    CategoryID: Optional['IntValue']


@dataclass
class ChangeBusinessAccountID(BaseDataClassModel):
    entity: Optional['BusinessAccount']
    parameters: Optional[Any]


@dataclass
class ChangeCostCodeID(BaseDataClassModel):
    entity: Optional['CostCode']
    parameters: Optional[Any]


@dataclass
class ChangeEmployeeID(BaseDataClassModel):
    entity: Optional['Employee']
    parameters: Optional[Any]


@dataclass
class ChangeOrder(BaseDataClassModel):
    ApprovalDetails: List[Optional['Approval']]
    Attributes: List[Optional['AttributeValue']]
    ChangeDate: Optional['DateTimeValue']
    Class: Optional['StringValue']
    Commitments: List[Optional['ChangeOrderCommitment']]
    CommitmentsChangeTotal: Optional['DecimalValue']
    CompletionDate: Optional['DateTimeValue']
    ContractTimeChangeDays: Optional['IntValue']
    CostBudget: List[Optional['ChangeOrderCostBudget']]
    CostBudgetChangeTotal: Optional['DecimalValue']
    Customer: Optional['StringValue']
    Description: Optional['StringValue']
    DetailedDescription: Optional['StringValue']
    ExternalRefNbr: Optional['StringValue']
    GrossMargin: Optional['DecimalValue']
    GrossMarginAmount: Optional['DecimalValue']
    Hold: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    OriginalCORefNbr: Optional['StringValue']
    ProjectID: Optional['StringValue']
    RefNbr: Optional['StringValue']
    RevenueBudget: List[Optional['ChangeOrderRevenueBudget']]
    RevenueBudgetChangeTotal: Optional['DecimalValue']
    RevenueChangeNbr: Optional['StringValue']
    ReverseStatus: Optional['StringValue']
    Status: Optional['StringValue']


@dataclass
class ChangeOrderClass(BaseDataClassModel):
    Active: Optional['BooleanValue']
    Attributes: List[Optional['BusinessAccountClassAttributeDetail']]
    ClassID: Optional['StringValue']
    Commitments: Optional['BooleanValue']
    CostBudget: Optional['BooleanValue']
    Description: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    RevenueBudget: Optional['BooleanValue']


@dataclass
class ChangeOrderClassCustomAction(BaseDataClassModel):
    entity: Optional['ChangeOrderClass']
    parameters: Optional[Any]


@dataclass
class ChangeOrderCommitment(BaseDataClassModel):
    Account: Optional['StringValue']
    Amount: Optional['DecimalValue']
    AmountinBaseCurrency: Optional['DecimalValue']
    CostCode: Optional['StringValue']
    CurrencyID: Optional['StringValue']
    Description: Optional['StringValue']
    InventoryID: Optional['StringValue']
    LineAmount: Optional['DecimalValue']
    LineDescription: Optional['StringValue']
    OpenQty: Optional['DecimalValue']
    OrderDate: Optional['DateTimeValue']
    OrderQty: Optional['DecimalValue']
    POLineNbr: Optional['IntValue']
    PONbr: Optional['StringValue']
    PotentiallyRevisedAmount: Optional['DecimalValue']
    PotentiallyRevisedQty: Optional['DecimalValue']
    ProjectTaskID: Optional['StringValue']
    Qty: Optional['DecimalValue']
    Status: Optional['StringValue']
    UnitCost: Optional['DecimalValue']
    UOM: Optional['StringValue']
    Vendor: Optional['StringValue']
    POType: Optional['StringValue']


@dataclass
class ChangeOrderCostBudget(BaseDataClassModel):
    AccountGroup: Optional['StringValue']
    ActualAmount: Optional['DecimalValue']
    ActualQty: Optional['DecimalValue']
    Amount: Optional['DecimalValue']
    CommittedCOAmount: Optional['DecimalValue']
    CommittedCOQty: Optional['DecimalValue']
    CommittedInvoicedAmount: Optional['DecimalValue']
    CommittedInvoicedQty: Optional['DecimalValue']
    CommittedOpenAmount: Optional['DecimalValue']
    CommittedOpenQty: Optional['DecimalValue']
    CommittedReceivedQty: Optional['DecimalValue']
    CostCode: Optional['StringValue']
    CurrentCommittedCOAmount: Optional['DecimalValue']
    CurrentCommittedCOQty: Optional['DecimalValue']
    Description: Optional['StringValue']
    InventoryID: Optional['StringValue']
    OriginalBudgetedAmount: Optional['DecimalValue']
    OriginalBudgetedQty: Optional['DecimalValue']
    OtherDraftCOAmount: Optional['DecimalValue']
    PreviouslyApprovedCOAmount: Optional['DecimalValue']
    PreviouslyApprovedCOQty: Optional['DecimalValue']
    ProjectTaskID: Optional['StringValue']
    Qty: Optional['DecimalValue']
    RevisedBudgetedAmount: Optional['DecimalValue']
    RevisedBudgetedQty: Optional['DecimalValue']
    RevisedCommittedAmount: Optional['DecimalValue']
    RevisedCommittedQty: Optional['DecimalValue']
    TotalPotentiallyRevisedAmount: Optional['DecimalValue']
    UnitRate: Optional['DecimalValue']
    UOM: Optional['StringValue']


@dataclass
class ChangeOrderCustomAction(BaseDataClassModel):
    entity: Optional['ChangeOrder']
    parameters: Optional[Any]


@dataclass
class ChangeOrderRevenueBudget(BaseDataClassModel):
    AccountGroup: Optional['StringValue']
    Amount: Optional['DecimalValue']
    CostCode: Optional['StringValue']
    Description: Optional['StringValue']
    InventoryID: Optional['StringValue']
    OtherDraftCOAmount: Optional['DecimalValue']
    PreviouslyApprovedCOAmount: Optional['DecimalValue']
    PreviouslyApprovedCOQty: Optional['DecimalValue']
    ProjectTaskID: Optional['StringValue']
    Qty: Optional['DecimalValue']
    RevisedBudgetedAmount: Optional['DecimalValue']
    RevisedBudgetedQty: Optional['DecimalValue']
    TotalPotentiallyRevisedAmount: Optional['DecimalValue']
    UnitRate: Optional['DecimalValue']
    UOM: Optional['StringValue']


@dataclass
class ChangeProjectID(BaseDataClassModel):
    entity: Optional['Project']
    parameters: Optional[Any]


@dataclass
class Check(BaseDataClassModel):
    ApplicationDate: Optional['DateTimeValue']
    CashAccount: Optional['StringValue']
    CurrencyID: Optional['StringValue']
    Description: Optional['StringValue']
    Details: List[Optional['CheckDetail']]
    History: List[Optional['CheckHistoryDetail']]
    Hold: Optional['BooleanValue']
    PaymentAmount: Optional['DecimalValue']
    PaymentMethod: Optional['StringValue']
    PaymentRef: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    Status: Optional['StringValue']
    Type: Optional['StringValue']
    UnappliedBalance: Optional['DecimalValue']
    Vendor: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']


@dataclass
class CheckCustomAction(BaseDataClassModel):
    entity: Optional['Check']
    parameters: Optional[Any]


@dataclass
class CheckDetail(BaseDataClassModel):
    AmountPaid: Optional['DecimalValue']
    Balance: Optional['DecimalValue']
    CashDiscountBalance: Optional['DecimalValue']
    DocLineNbr: Optional['IntValue']
    DocType: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']


@dataclass
class CheckForBusinessAccountDuplicates(BaseDataClassModel):
    entity: Optional['BusinessAccount']


@dataclass
class CheckForContactDuplicates(BaseDataClassModel):
    entity: Optional['Contact']


@dataclass
class CheckHistoryDetail(BaseDataClassModel):
    AmountPaid: Optional['DecimalValue']
    Balance: Optional['DecimalValue']
    CashDiscountBalance: Optional['DecimalValue']
    CashDiscountTaken: Optional['DecimalValue']
    DocType: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    VendorRef: Optional['StringValue']


@dataclass
class CheckLeadForDuplicates(BaseDataClassModel):
    entity: Optional['Lead']


@dataclass
class ClaimExpenseReceipt(BaseDataClassModel):
    entity: Optional['ExpenseReceipt']


@dataclass
class CloseAppointment(BaseDataClassModel):
    entity: Optional['Appointment']


@dataclass
class CloseOrder(BaseDataClassModel):
    entity: Optional['ServiceOrder']


@dataclass
class Commissions(BaseDataClassModel):
    DefaultSalesperson: Optional['StringValue']
    SalesPersons: List[Optional['SalesPersonDetail']]


@dataclass
class CompaniesStructure(BaseDataClassModel):
    Results: List[Optional['CompaniesStructureDetail']]


@dataclass
class CompaniesStructureCustomAction(BaseDataClassModel):
    entity: Optional['CompaniesStructure']
    parameters: Optional[Any]


@dataclass
class CompaniesStructureDetail(BaseDataClassModel):
    BaseCurrencyID: Optional['StringValue']
    BranchCountry: Optional['StringValue']
    BranchID: Optional['StringValue']
    BranchName: Optional['StringValue']
    BranchStatus: Optional['BooleanValue']
    CompanyID: Optional['StringValue']
    CompanyName: Optional['StringValue']
    CompanyStatus: Optional['BooleanValue']
    CompanyType: Optional['StringValue']


@dataclass
class CompanyFinancialPeriod(BaseDataClassModel):
    Company: Optional['StringValue']
    Details: List[Optional['FinancialPeriodDetail']]
    FinancialYear: Optional['StringValue']
    NbrOfPeriods: Optional['ShortValue']
    StartDate: Optional['DateTimeValue']


@dataclass
class CompanyFinancialPeriodCustomAction(BaseDataClassModel):
    entity: Optional['CompanyFinancialPeriod']
    parameters: Optional[Any]


@dataclass
class CompensationDetail(BaseDataClassModel):
    Active: Optional['BooleanValue']
    EarningCode: Optional['StringValue']
    EarningDescription: Optional['StringValue']
    EndDate: Optional['DateTimeValue']
    LastModifiedDateTime: Optional['StringValue']
    PayRate: Optional['DecimalValue']
    StartDate: Optional['DateTimeValue']
    UnitOfPay: Optional['StringValue']


@dataclass
class CompleteActivity(BaseDataClassModel):
    entity: Optional['Activity']


@dataclass
class CompleteAppointment(BaseDataClassModel):
    entity: Optional['Appointment']


@dataclass
class CompleteEvent(BaseDataClassModel):
    entity: Optional['Event']


@dataclass
class CompleteOrder(BaseDataClassModel):
    entity: Optional['ServiceOrder']


@dataclass
class CompletePhysicalInventory(BaseDataClassModel):
    entity: Optional['PhysicalInventoryReview']


@dataclass
class CompleteProject(BaseDataClassModel):
    entity: Optional['Project']


@dataclass
class CompleteProjectTask(BaseDataClassModel):
    entity: Optional['ProjectTask']


@dataclass
class CompleteTask(BaseDataClassModel):
    entity: Optional['Task']


@dataclass
class CompleteTimeEntry(BaseDataClassModel):
    entity: Optional['TimeEntry']


@dataclass
class ConfirmShipment(BaseDataClassModel):
    entity: Optional['Shipment']


@dataclass
class Contact(BaseDataClassModel):
    Active: Optional['BooleanValue']
    Activities: List[Optional['ActivityDetail']]
    Address: Optional['Address']
    OverrideAccountAddress: Optional['BooleanValue']
    AddressValidated: Optional['BooleanValue']
    Attention: Optional['StringValue']
    Attributes: List[Optional['AttributeValue']]
    BusinessAccount: Optional['StringValue']
    Campaigns: List[Optional['CampaignDetail']]
    Cases: List[Optional['CaseDetail']]
    CompanyName: Optional['StringValue']
    ContactClass: Optional['StringValue']
    ContactID: Optional['IntValue']
    ContactMethod: Optional['StringValue']
    ConvertedBy: Optional['StringValue']
    DateOfBirth: Optional['DateTimeValue']
    DisplayName: Optional['StringValue']
    DoNotCall: Optional['BooleanValue']
    DoNotEmail: Optional['BooleanValue']
    DoNotFax: Optional['BooleanValue']
    DoNotMail: Optional['BooleanValue']
    Duplicate: Optional['StringValue']
    DuplicateFound: Optional['BooleanValue']
    Duplicates: List[Optional['ContactDuplicateDetail']]
    Email: Optional['StringValue']
    Fax: Optional['StringValue']
    FaxType: Optional['StringValue']
    FirstName: Optional['StringValue']
    Gender: Optional['StringValue']
    Image: Optional['StringValue']
    JobTitle: Optional['StringValue']
    LanguageOrLocale: Optional['StringValue']
    LastIncomingActivity: Optional['DateTimeValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    LastName: Optional['StringValue']
    LastOutgoingActivity: Optional['DateTimeValue']
    MaritalStatus: Optional['StringValue']
    MarketingLists: List[Optional['MarketingListDetail']]
    MiddleName: Optional['StringValue']
    NoMarketing: Optional['BooleanValue']
    NoMassMail: Optional['BooleanValue']
    Notifications: List[Optional['ContactNotification']]
    Opportunities: List[Optional['OpportunityDetail']]
    Owner: Optional['StringValue']
    OwnerEmployeeName: Optional['StringValue']
    ParentAccount: Optional['StringValue']
    Phone1: Optional['StringValue']
    Phone1Type: Optional['StringValue']
    Phone2: Optional['StringValue']
    Phone2Type: Optional['StringValue']
    Phone3: Optional['StringValue']
    Phone3Type: Optional['StringValue']
    QualificationDate: Optional['DateTimeValue']
    Reason: Optional['StringValue']
    Relations: List[Optional['RelationDetail']]
    RoleAssignments: List[Optional['BCRoleAssignment']]
    Source: Optional['StringValue']
    SourceCampaign: Optional['StringValue']
    SpouseOrPartnerName: Optional['StringValue']
    Status: Optional['StringValue']
    Synchronize: Optional['BooleanValue']
    Title: Optional['StringValue']
    Type: Optional['StringValue']
    UserInfo: Optional['ContactUserInfo']
    WebSite: Optional['StringValue']
    Workgroup: Optional['StringValue']
    WorkgroupDescription: Optional['StringValue']
    NoteID: Optional['GuidValue']
    FullName: Optional['StringValue']
    ExtRefNbr: Optional['StringValue']


@dataclass
class ContactCustomAction(BaseDataClassModel):
    entity: Optional['Contact']
    parameters: Optional[Any]


@dataclass
class ContactDuplicateDetail(BaseDataClassModel):
    BusinessAccount: Optional['StringValue']
    BusinessAccountName: Optional['StringValue']
    BusinessAccountType: Optional['StringValue']
    DisplayName: Optional['StringValue']
    Duplicate: Optional['StringValue']
    Email: Optional['StringValue']
    LastModifiedDate: Optional['DateTimeValue']
    Type: Optional['StringValue']


@dataclass
class ContactNotification(BaseDataClassModel):
    Active: Optional['BooleanValue']
    Bcc: Optional['BooleanValue']
    ClassID: Optional['StringValue']
    Description: Optional['StringValue']
    Format: Optional['StringValue']
    MailingID: Optional['StringValue']
    Module: Optional['StringValue']
    NotificationID: Optional['IntValue']
    Report: Optional['StringValue']
    Source: Optional['StringValue']


@dataclass
class ContactRoles(BaseDataClassModel):
    RoleDescription: Optional['StringValue']
    RoleName: Optional['StringValue']
    Selected: Optional['BooleanValue']
    UserType: Optional['IntValue']


@dataclass
class ContactUserInfo(BaseDataClassModel):
    GeneratePassword: Optional['BooleanValue']
    Login: Optional['StringValue']
    Password: Optional['StringValue']
    Roles: List[Optional['ContactRoles']]
    Status: Optional['StringValue']
    UserType: Optional['StringValue']


@dataclass
class ContractUsage(BaseDataClassModel):
    BilledTransactions: List[Optional['ContractUsageTransactionDetail']]
    ContractID: Optional['StringValue']
    PostPeriod: Optional['StringValue']
    UnbilledTransactions: List[Optional['ContractUsageTransactionDetail']]


@dataclass
class ContractUsageCustomAction(BaseDataClassModel):
    entity: Optional['ContractUsage']
    parameters: Optional[Any]


@dataclass
class ContractUsageTransactionDetail(BaseDataClassModel):
    BillingDate: Optional['DateTimeValue']
    Branch: Optional['StringValue']
    CaseID: Optional['StringValue']
    Date: Optional['DateTimeValue']
    Description: Optional['StringValue']
    EndDate: Optional['DateTimeValue']
    InventoryID: Optional['StringValue']
    Qty: Optional['DecimalValue']
    ReferenceNbr: Optional['StringValue']
    StartDate: Optional['DateTimeValue']
    TransactionID: Optional['LongValue']
    Type: Optional['StringValue']
    UOM: Optional['StringValue']


@dataclass
class ConvertBusinessAccountToCustomer(BaseDataClassModel):
    entity: Optional['BusinessAccount']


@dataclass
class ConvertLeadToBAccount(BaseDataClassModel):
    entity: Optional['Lead']
    parameters: Optional[Any]


@dataclass
class ConvertLeadToContact(BaseDataClassModel):
    entity: Optional['Lead']
    parameters: Optional[Any]


@dataclass
class ConvertLeadToOpportunity(BaseDataClassModel):
    entity: Optional['Lead']
    parameters: Optional[Any]


@dataclass
class CorrectShipment(BaseDataClassModel):
    entity: Optional['Shipment']


@dataclass
class CostCode(BaseDataClassModel):
    CostCodeID: Optional['StringValue']
    Description: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']


@dataclass
class CostCodeCustomAction(BaseDataClassModel):
    entity: Optional['CostCode']
    parameters: Optional[Any]


@dataclass
class CreateAPBill(BaseDataClassModel):
    entity: Optional['PurchaseReceipt']


@dataclass
class CreateAccountFromContact(BaseDataClassModel):
    entity: Optional['Contact']
    parameters: Optional[Any]


@dataclass
class CreateAccountFromOpportunity(BaseDataClassModel):
    entity: Optional['Opportunity']
    parameters: Optional[Any]


@dataclass
class CreateCaseFromEmail(BaseDataClassModel):
    entity: Optional['Email']


@dataclass
class CreateContactFromBusinessAccount(BaseDataClassModel):
    entity: Optional['BusinessAccount']
    parameters: Optional[Any]


@dataclass
class CreateContactFromCustomer(BaseDataClassModel):
    entity: Optional['Customer']
    parameters: Optional[Any]


@dataclass
class CreateContactFromEmail(BaseDataClassModel):
    entity: Optional['Email']


@dataclass
class CreateContactFromOpportunity(BaseDataClassModel):
    entity: Optional['Opportunity']
    parameters: Optional[Any]


@dataclass
class CreateContactFromVendor(BaseDataClassModel):
    entity: Optional['Vendor']
    parameters: Optional[Any]


@dataclass
class CreateEventFromEmail(BaseDataClassModel):
    entity: Optional['Email']


@dataclass
class CreateExpenseReceiptFromEmail(BaseDataClassModel):
    entity: Optional['Email']


@dataclass
class CreateLeadFromEmail(BaseDataClassModel):
    entity: Optional['Email']


@dataclass
class CreateOpportunityFromEmail(BaseDataClassModel):
    entity: Optional['Email']


@dataclass
class CreateOpportunityInvoice(BaseDataClassModel):
    entity: Optional['Opportunity']


@dataclass
class CreateOpportunitySalesOrder(BaseDataClassModel):
    entity: Optional['Opportunity']
    parameters: Optional[Any]


@dataclass
class CreateTaskFromEmail(BaseDataClassModel):
    entity: Optional['Email']


@dataclass
class CreditCardProcessingDetail(BaseDataClassModel):
    TransactionAmount: Optional['DecimalValue']
    TransactionStatus: Optional['StringValue']


@dataclass
class CreditCardTransactionDetail(BaseDataClassModel):
    TranNbr: Optional['StringValue']
    TranType: Optional['StringValue']
    AuthNbr: Optional['StringValue']
    TranDate: Optional['DateTimeValue']
    ExtProfileId: Optional['StringValue']
    NeedValidation: Optional['BooleanValue']
    OrigTranNbr: Optional['StringValue']
    ExpirationDate: Optional['DateTimeValue']
    CardType: Optional['StringValue']


@dataclass
class CreditVerificationRules(BaseDataClassModel):
    CreditDaysPastDue: Optional['ShortValue']
    CreditLimit: Optional['DecimalValue']
    CreditVerification: Optional['StringValue']
    FirstDueDate: Optional['DateTimeValue']
    OpenOrdersBalance: Optional['DecimalValue']
    RemainingCreditLimit: Optional['DecimalValue']
    UnreleasedBalance: Optional['DecimalValue']


@dataclass
class Currency(BaseDataClassModel):
    Active: Optional['BooleanValue']
    CreatedDateTime: Optional['DateTimeValue']
    CurrencyID: Optional['StringValue']
    CurrencySymbol: Optional['StringValue']
    DecimalPrecision: Optional['ShortValue']
    Description: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    UseForAccounting: Optional['BooleanValue']


@dataclass
class CurrencyCustomAction(BaseDataClassModel):
    entity: Optional['Currency']
    parameters: Optional[Any]


@dataclass
class CustomBooleanField(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class CustomByteField(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class CustomDateTimeField(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class CustomDecimalField(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class CustomDoubleField(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class CustomField(BaseDataClassModel):
    type: Optional[Any]


@dataclass
class CustomGuidField(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class CustomIntField(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class CustomLongField(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class CustomShortField(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class CustomStringField(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class Customer(BaseDataClassModel):
    AccountRef: Optional['StringValue']
    ApplyOverdueCharges: Optional['BooleanValue']
    Attributes: List[Optional['AttributeValue']]
    AutoApplyPayments: Optional['BooleanValue']
    BAccountID: Optional['IntValue']
    BillingAddressOverride: Optional['BooleanValue']
    BillingContact: Optional['Contact']
    BillingContactOverride: Optional['BooleanValue']
    Contacts: List[Optional['CustomerContact']]
    CreatedDateTime: Optional['DateTimeValue']
    CreditVerificationRules: Optional['CreditVerificationRules']
    CurrencyID: Optional['StringValue']
    CurrencyRateType: Optional['StringValue']
    CustomerClass: Optional['StringValue']
    CustomerID: Optional['StringValue']
    CustomerCategory: Optional['StringValue']
    CustomerName: Optional['StringValue']
    Email: Optional['StringValue']
    EnableCurrencyOverride: Optional['BooleanValue']
    EnableRateOverride: Optional['BooleanValue']
    EnableWriteOffs: Optional['BooleanValue']
    FOBPoint: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    LeadTimedays: Optional['ShortValue']
    LocationName: Optional['StringValue']
    MainContact: Optional['Contact']
    MultiCurrencyStatements: Optional['BooleanValue']
    OrderPriority: Optional['ShortValue']
    ParentRecord: Optional['StringValue']
    PaymentInstructions: List[Optional['BusinessAccountPaymentInstructionDetail']]
    PriceClassID: Optional['StringValue']
    PrimaryContact: Optional['Contact']
    PrimaryContactID: Optional['IntValue']
    PrintDunningLetters: Optional['BooleanValue']
    PrintInvoices: Optional['BooleanValue']
    PrintStatements: Optional['BooleanValue']
    ResidentialDelivery: Optional['BooleanValue']
    Salespersons: List[Optional['CustomerSalesPerson']]
    SaturdayDelivery: Optional['BooleanValue']
    SendDunningLettersbyEmail: Optional['BooleanValue']
    SendInvoicesbyEmail: Optional['BooleanValue']
    SendStatementsbyEmail: Optional['BooleanValue']
    ShippingAddressOverride: Optional['BooleanValue']
    ShippingBranch: Optional['StringValue']
    ShippingContact: Optional['Contact']
    ShippingContactOverride: Optional['BooleanValue']
    ShippingRule: Optional['StringValue']
    ShippingTerms: Optional['StringValue']
    ShippingZoneID: Optional['StringValue']
    ShipVia: Optional['StringValue']
    StatementCycleID: Optional['StringValue']
    StatementType: Optional['StringValue']
    Status: Optional['StringValue']
    TaxRegistrationID: Optional['StringValue']
    TaxZone: Optional['StringValue']
    Terms: Optional['StringValue']
    WarehouseID: Optional['StringValue']
    WriteOffLimit: Optional['DecimalValue']
    RestrictVisibilityTo: Optional['StringValue']
    CreditLimit: Optional['DecimalValue']
    NoteID: Optional['GuidValue']
    EntityUsageType: Optional['StringValue']
    TaxExemptionNumber: Optional['StringValue']
    IsGuestCustomer: Optional['BooleanValue']


@dataclass
class CustomerClass(BaseDataClassModel):
    ApplyOverdueCharges: Optional['BooleanValue']
    ARAccount: Optional['StringValue']
    ARSubaccount: Optional['StringValue']
    Attributes: List[Optional['BusinessAccountClassAttributeDetail']]
    AutoApplyPayments: Optional['BooleanValue']
    CashDiscountAccount: Optional['StringValue']
    CashDiscountSubaccount: Optional['StringValue']
    ClassID: Optional['StringValue']
    COGSAccount: Optional['StringValue']
    COGSSubaccount: Optional['StringValue']
    Country: Optional['StringValue']
    CreatedDateTime: Optional['DateTimeValue']
    CreditDaysPastDue: Optional['ShortValue']
    CreditLimit: Optional['DecimalValue']
    CreditVerification: Optional['StringValue']
    CurrencyID: Optional['StringValue']
    CurrencyRateType: Optional['StringValue']
    DefaultLocationIDfromBranch: Optional['BooleanValue']
    DefaultRestrictionGroup: Optional['StringValue']
    Description: Optional['StringValue']
    DiscountAccount: Optional['StringValue']
    DiscountSubaccount: Optional['StringValue']
    EnableCurrencyOverride: Optional['BooleanValue']
    EnableRateOverride: Optional['BooleanValue']
    EnableWriteOffs: Optional['BooleanValue']
    EntityUsageType: Optional['StringValue']
    FreightAccount: Optional['StringValue']
    FreightSubaccount: Optional['StringValue']
    GroupDocumentDiscountLimit: Optional['DecimalValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    MiscAccount: Optional['StringValue']
    MiscSubaccount: Optional['StringValue']
    MultiCurrencyStatements: Optional['BooleanValue']
    OverdueChargeID: Optional['StringValue']
    OverLimitAmount: Optional['DecimalValue']
    PaymentMethod: Optional['StringValue']
    PrepaymentAccount: Optional['StringValue']
    PrepaymentSubaccount: Optional['StringValue']
    PrintDunningLetters: Optional['BooleanValue']
    PrintInvoices: Optional['BooleanValue']
    PrintStatements: Optional['BooleanValue']
    RequireEntityUsageType: Optional['BooleanValue']
    RequireTaxZone: Optional['BooleanValue']
    SalesAccount: Optional['StringValue']
    SalespersonID: Optional['StringValue']
    SalesSubaccount: Optional['StringValue']
    SendDunningLettersbyEmail: Optional['BooleanValue']
    SendInvoicesbyEmail: Optional['BooleanValue']
    SendStatementsByEmail: Optional['BooleanValue']
    ShippingRule: Optional['StringValue']
    ShippingTerms: Optional['StringValue']
    ShipVia: Optional['StringValue']
    StatementCycleID: Optional['StringValue']
    StatementType: Optional['StringValue']
    TaxZoneID: Optional['StringValue']
    Terms: Optional['StringValue']
    UnrealizedGainAccount: Optional['StringValue']
    UnrealizedGainSubaccount: Optional['StringValue']
    UnrealizedLossAccount: Optional['StringValue']
    UnrealizedLossSubaccount: Optional['StringValue']
    WriteOffLimit: Optional['DecimalValue']


@dataclass
class CustomerClassCustomAction(BaseDataClassModel):
    entity: Optional['CustomerClass']
    parameters: Optional[Any]


@dataclass
class CustomerContact(BaseDataClassModel):
    Contact: Optional['Contact']
    ContactID: Optional['IntValue']
    LastModifiedDateTime: Optional['DateTimeValue']


@dataclass
class CustomerCustomAction(BaseDataClassModel):
    entity: Optional['Customer']
    parameters: Optional[Any]


@dataclass
class CustomerLocation(BaseDataClassModel):
    Active: Optional['BooleanValue']
    AddressOverride: Optional['BooleanValue']
    Calendar: Optional['StringValue']
    ContactOverride: Optional['BooleanValue']
    CreatedDateTime: Optional['DateTimeValue']
    Customer: Optional['StringValue']
    Default: Optional['BooleanValue']
    DefaultProject: Optional['StringValue']
    EntityUsageType: Optional['StringValue']
    FedExGroundCollect: Optional['BooleanValue']
    FOBPoint: Optional['StringValue']
    Insurance: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    LeadTimeDays: Optional['ShortValue']
    LocationContact: Optional['Contact']
    LocationID: Optional['StringValue']
    LocationName: Optional['StringValue']
    OrderPriority: Optional['ShortValue']
    PriceClass: Optional['StringValue']
    ResidentialDelivery: Optional['BooleanValue']
    RoleAssignments: List[Optional['BCRoleAssignment']]
    SaturdayDelivery: Optional['BooleanValue']
    ShippingBranch: Optional['StringValue']
    ShippingRule: Optional['StringValue']
    ShippingTerms: Optional['StringValue']
    ShippingZone: Optional['StringValue']
    ShipVia: Optional['StringValue']
    Status: Optional['StringValue']
    TaxExemptionNbr: Optional['StringValue']
    TaxRegistrationID: Optional['StringValue']
    TaxZone: Optional['StringValue']
    Warehouse: Optional['StringValue']
    NoteID: Optional['GuidValue']
    ExtRefNbr: Optional['StringValue']


@dataclass
class CustomerLocationCustomAction(BaseDataClassModel):
    entity: Optional['CustomerLocation']
    parameters: Optional[Any]


@dataclass
class CustomerPaymentMethod(BaseDataClassModel):
    Active: Optional['BooleanValue']
    CardAccountNbr: Optional['StringValue']
    CashAccount: Optional['StringValue']
    CreatedDateTime: Optional['DateTimeValue']
    CustomerID: Optional['StringValue']
    CustomerProfileID: Optional['StringValue']
    Details: List[Optional['CustomerPaymentMethodDetail']]
    InstanceID: Optional['IntValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    PaymentMethod: Optional['StringValue']
    ProcCenterID: Optional['StringValue']
    CardType: Optional['StringValue']


@dataclass
class CustomerPaymentMethodCustomAction(BaseDataClassModel):
    entity: Optional['CustomerPaymentMethod']
    parameters: Optional[Any]


@dataclass
class CustomerPaymentMethodDetail(BaseDataClassModel):
    Name: Optional['StringValue']
    Value: Optional['StringValue']


@dataclass
class CustomerPriceClass(BaseDataClassModel):
    CreatedDateTime: Optional['DateTimeValue']
    Description: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    PriceClassID: Optional['StringValue']
    NoteID: Optional['GuidValue']


@dataclass
class CustomerPriceClassCustomAction(BaseDataClassModel):
    entity: Optional['CustomerPriceClass']
    parameters: Optional[Any]


@dataclass
class CustomerSalesPerson(BaseDataClassModel):
    Commission: Optional['DecimalValue']
    Default: Optional['BooleanValue']
    LocationID: Optional['StringValue']
    LocationName: Optional['StringValue']
    Name: Optional['StringValue']
    SalespersonID: Optional['StringValue']


@dataclass
class DateTimeValue(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class DecimalValue(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class DeductionBenefitCode(BaseDataClassModel):
    ACAApplicable: Optional['BooleanValue']
    ACAInformation: Optional['ACAInformation']
    Active: Optional['BooleanValue']
    AffectsTaxCalculation: Optional['BooleanValue']
    ApplicableWage: Optional['ApplicableWage']
    AssociatedWith: Optional['StringValue']
    ContributionType: Optional['StringValue']
    DeductionBenefitCodeID: Optional['StringValue']
    Description: Optional['StringValue']
    EmployeeDeduction: Optional['EmployeeDeduction']
    EmployerContribution: Optional['EmployerContribution']
    GLAccounts: Optional['DeductionOrBenefitCodeGLAccounts']
    InvoiceDescrSource: Optional['StringValue']
    IsGarnishment: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    PayableBenefit: Optional['BooleanValue']
    ShowApplicableWageTab: Optional['BooleanValue']
    TaxSettingsCA: Optional['TaxSettingsCA']
    TaxSettingsUS: Optional['TaxSettingsUS']
    Vendor: Optional['StringValue']
    VendorInvoiceDescription: Optional['StringValue']
    WCCCode: Optional['DeductionBenefitWCCCode']


@dataclass
class DeductionBenefitCodeCustomAction(BaseDataClassModel):
    entity: Optional['DeductionBenefitCode']
    parameters: Optional[Any]


@dataclass
class DeductionBenefitWCCCode(BaseDataClassModel):
    State: Optional['StringValue']
    WCCCodeRates: List[Optional['WCCCodeRateDetail']]


@dataclass
class DeductionDecreasingApplWage(BaseDataClassModel):
    DeductionIncreasingApplWageDetails: List[Optional['DeductionDecreasingApplWageDetail']]
    InclusionType: Optional['StringValue']


@dataclass
class DeductionDecreasingApplWageDetail(BaseDataClassModel):
    DeductionCode: Optional['StringValue']
    Description: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']


@dataclass
class DeductionOrBenefitCodeGLAccounts(BaseDataClassModel):
    BenefitExpenseAccount: Optional['StringValue']
    BenefitExpenseSub: Optional['StringValue']
    BenefitLiabilityAccount: Optional['StringValue']
    BenefitLiabilitySub: Optional['StringValue']
    DeductionLiabilityAccount: Optional['StringValue']
    DeductionLiabilitySub: Optional['StringValue']


@dataclass
class DeductionOrBenefitTaxDetailCA(BaseDataClassModel):
    Benefitincreasestaxablewage: Optional['BooleanValue']
    Deductiondecreasestaxablewage: Optional['BooleanValue']
    TaxCode: Optional['StringValue']
    TaxName: Optional['StringValue']


@dataclass
class DeductionOrBenefitTaxDetailUS(BaseDataClassModel):
    LastModifiedDateTime: Optional['DateTimeValue']
    TaxCode: Optional['StringValue']
    TaxName: Optional['StringValue']


@dataclass
class DeductionsAndBenefits(BaseDataClassModel):
    DeductionAndBenefitUseClassDefaults: Optional['BooleanValue']
    DeductionsAndBenefitsDetails: List[Optional['EmployeeDeductionOrBenefitDetail']]
    DeductionSplitMethod: Optional['StringValue']
    MaxPercOfNetPayForAllGarnishm: Optional['DecimalValue']


@dataclass
class DefaultTaskForGLAccount(BaseDataClassModel):
    Account: Optional['StringValue']
    DefaultTask: Optional['StringValue']


@dataclass
class DirectDepositDetail(BaseDataClassModel):
    AccountNumber: Optional['StringValue']
    AccountType: Optional['StringValue']
    Amount: Optional['DecimalValue']
    BankName: Optional['StringValue']
    BankRoutingNumber: Optional['StringValue']
    DepositSequenceNbr: Optional['IntValue']
    GetsRemainder: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Percent: Optional['DecimalValue']


@dataclass
class Discount(BaseDataClassModel):
    Active: Optional['BooleanValue']
    BreakBy: Optional['StringValue']
    CreatedDateTime: Optional['DateTimeValue']
    CustomerPriceClasses: List[Optional['DiscountCustomerPriceClassesDetail']]
    Customers: List[Optional['DiscountCustomerDetail']]
    Description: Optional['StringValue']
    DiscountBreakpoints: List[Optional['DiscountBreakpointDetail']]
    DiscountBy: Optional['StringValue']
    DiscountCode: Optional['StringValue']
    EffectiveDate: Optional['DateTimeValue']
    ExpirationDate: Optional['DateTimeValue']
    ItemPriceClasses: List[Optional['DiscountItemPriceClassesDetail']]
    Items: List[Optional['DiscountItemDetail']]
    LastModifiedDateTime: Optional['DateTimeValue']
    Promotional: Optional['BooleanValue']
    ProrateDiscount: Optional['BooleanValue']
    Sequence: Optional['StringValue']
    ShowFreeItem: Optional['BooleanValue']
    Warehouses: List[Optional['DiscountWarehouseDetail']]


@dataclass
class DiscountBreakpointDetail(BaseDataClassModel):
    BreakAmount: Optional['DecimalValue']
    BreakQty: Optional['DecimalValue']
    DiscountAmount: Optional['DecimalValue']
    DiscountDetailID: Optional['IntValue']
    DiscountPercent: Optional['DecimalValue']
    EffectiveDate: Optional['DateTimeValue']
    FreeItemQty: Optional['DecimalValue']
    LastBreakAmount: Optional['DecimalValue']
    LastBreakQty: Optional['DecimalValue']
    LastDiscountAmount: Optional['DecimalValue']
    LastDiscountPercent: Optional['DecimalValue']
    LastFreeItemQty: Optional['DecimalValue']
    PendingBreakAmount: Optional['DecimalValue']
    PendingBreakQty: Optional['DecimalValue']
    PendingDate: Optional['DateTimeValue']
    PendingDiscountAmount: Optional['DecimalValue']
    PendingDiscountPercent: Optional['DecimalValue']
    PendingFreeItemQty: Optional['DecimalValue']


@dataclass
class DiscountCode(BaseDataClassModel):
    ApplicableTo: Optional['StringValue']
    CreatedDateTime: Optional['DateTimeValue']
    Description: Optional['StringValue']
    DiscountCodeID: Optional['StringValue']
    DiscountType: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']


@dataclass
class DiscountCodeCustomAction(BaseDataClassModel):
    entity: Optional['DiscountCode']
    parameters: Optional[Any]


@dataclass
class DiscountCustomAction(BaseDataClassModel):
    entity: Optional['Discount']
    parameters: Optional[Any]


@dataclass
class DiscountCustomerDetail(BaseDataClassModel):
    CustomerID: Optional['StringValue']
    CustomerName: Optional['StringValue']


@dataclass
class DiscountCustomerPriceClassesDetail(BaseDataClassModel):
    PriceClassID: Optional['StringValue']


@dataclass
class DiscountItemDetail(BaseDataClassModel):
    Description: Optional['StringValue']
    InventoryID: Optional['StringValue']


@dataclass
class DiscountItemPriceClassesDetail(BaseDataClassModel):
    PriceClassID: Optional['StringValue']


@dataclass
class DiscountWarehouseDetail(BaseDataClassModel):
    Warehouse: Optional['StringValue']


@dataclass
class DocContact(BaseDataClassModel):
    Attention: Optional['StringValue']
    BusinessName: Optional['StringValue']
    Email: Optional['StringValue']
    Phone1: Optional['StringValue']


@dataclass
class DoubleValue(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class DuplicateDetail(BaseDataClassModel):
    AccountName: Optional['StringValue']
    BusinessAccount: Optional['StringValue']
    BusinessAccountType: Optional['StringValue']
    ContactID: Optional['IntValue']
    DisplayName: Optional['StringValue']
    Duplicate: Optional['StringValue']
    DuplicateContactID: Optional['IntValue']
    Email: Optional['StringValue']
    EntityType: Optional['StringValue']
    LastModifiedDate: Optional['DateTimeValue']
    Type: Optional['StringValue']


@dataclass
class EarningCodeGLAccounts(BaseDataClassModel):
    BenefitExpenseAccount: Optional['StringValue']
    BenefitExpenseSub: Optional['StringValue']
    EarningsAccount: Optional['StringValue']
    EarningsSub: Optional['StringValue']
    PTOExpenseAccount: Optional['StringValue']
    PTOExpenseSub: Optional['StringValue']
    TaxExpenseAccount: Optional['StringValue']
    TaxExpenseSub: Optional['StringValue']


@dataclass
class EarningCodeProjectSettings(BaseDataClassModel):
    BillableProject: Optional['BooleanValue']
    DefaultProjectCode: Optional['StringValue']
    DefaultProjectTask: Optional['StringValue']


@dataclass
class EarningCodeTaxDetailCA(BaseDataClassModel):
    Taxability: Optional['StringValue']
    TaxCode: Optional['StringValue']
    TaxName: Optional['StringValue']


@dataclass
class EarningCodeTaxDetailUS(BaseDataClassModel):
    TaxCode: Optional['StringValue']
    TaxName: Optional['StringValue']


@dataclass
class EarningIncreasingApplWage(BaseDataClassModel):
    EarningIncreasingApplWageDetails: List[Optional['EarningIncreasingApplWageDetail']]
    InclusionType: Optional['StringValue']


@dataclass
class EarningIncreasingApplWageDetail(BaseDataClassModel):
    Description: Optional['StringValue']
    EarningTypeCategory: Optional['StringValue']
    EarningTypeCode: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']


@dataclass
class EarningTypeCode(BaseDataClassModel):
    AccrueTimeOff: Optional['BooleanValue']
    Active: Optional['BooleanValue']
    Category: Optional['StringValue']
    ContributestoWCCCalculation: Optional['BooleanValue']
    Description: Optional['StringValue']
    EarningTypeCodeID: Optional['StringValue']
    GLAccounts: Optional['EarningCodeGLAccounts']
    LastModifiedDateTime: Optional['DateTimeValue']
    Multiplier: Optional['DecimalValue']
    ProjectSettings: Optional['EarningCodeProjectSettings']
    PublicHoliday: Optional['BooleanValue']
    RegularTimeTypeCode: Optional['StringValue']
    TaxAndReportingCA: Optional['TaxAndReportingCA']
    TaxAndReportingUS: Optional['TaxAndReportingUS']


@dataclass
class EarningTypeCodeCustomAction(BaseDataClassModel):
    entity: Optional['EarningTypeCode']
    parameters: Optional[Any]


@dataclass
class Email(BaseDataClassModel):
    Bcc: Optional['StringValue']
    Body: Optional['StringValue']
    Cc: Optional['StringValue']
    Description: Optional['StringValue']
    From: Optional['StringValue']
    FromEmailAccountDisplayName: Optional['StringValue']
    FromEmailAccountID: Optional['IntValue']
    Incoming: Optional['BooleanValue']
    Internal: Optional['BooleanValue']
    MailStatus: Optional['StringValue']
    Owner: Optional['StringValue']
    Parent: Optional['GuidValue']
    ParentSummary: Optional['StringValue']
    StartDate: Optional['DateTimeValue']
    Subject: Optional['StringValue']
    TimeActivity: Optional['TimeActivity']
    To: Optional['StringValue']
    Workgroup: Optional['StringValue']
    CreatedByID: Optional['StringValue']
    CreatedDateTime: Optional['DateTimeValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    NoteID: Optional['GuidValue']
    RelatedEntityType: Optional['StringValue']
    RelatedEntityNoteID: Optional['GuidValue']
    RelatedEntityDescription: Optional['StringValue']


@dataclass
class EmailChangeOrder(BaseDataClassModel):
    entity: Optional['ChangeOrder']


@dataclass
class EmailCustomAction(BaseDataClassModel):
    entity: Optional['Email']
    parameters: Optional[Any]


@dataclass
class EmailProFormaInvoice(BaseDataClassModel):
    entity: Optional['ProFormaInvoice']


@dataclass
class EmailProcessing(BaseDataClassModel):
    Account: Optional['IntValue']
    AccountEmailAccountID: Optional['StringValue']
    AssignedToMe: Optional['BooleanValue']
    AssignedToOwner: Optional['StringValue']
    IncludeFailed: Optional['BooleanValue']
    Result: List[Optional['EmailProcessingRow']]
    Type: Optional['StringValue']


@dataclass
class EmailProcessingCustomAction(BaseDataClassModel):
    entity: Optional['EmailProcessing']
    parameters: Optional[Any]


@dataclass
class EmailProcessingRow(BaseDataClassModel):
    EmailAccount: Optional['StringValue']
    From: Optional['StringValue']
    MailStatus: Optional['StringValue']
    Owner: Optional['StringValue']
    Selected: Optional['BooleanValue']
    StartDate: Optional['DateTimeValue']
    Subject: Optional['StringValue']
    To: Optional['StringValue']


@dataclass
class Employee(BaseDataClassModel):
    Attributes: List[Optional['AttributeValue']]
    ContactInfo: Optional['Contact']
    Delegates: List[Optional['EmployeeDelegate']]
    EmployeeID: Optional['StringValue']
    EmployeeName: Optional['StringValue']
    EmployeeSettings: Optional['EmployeeSettings']
    EmploymentHistory: List[Optional['EmploymentHistoryRecord']]
    FinancialSettings: Optional['EmployeeFinancialSettings']
    LastModifiedDateTime: Optional['DateTimeValue']
    Status: Optional['StringValue']


@dataclass
class EmployeeClassWorkLocation(BaseDataClassModel):
    DefaultWorkLocation: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    LocationID: Optional['StringValue']
    LocationName: Optional['StringValue']


@dataclass
class EmployeeCustomAction(BaseDataClassModel):
    entity: Optional['Employee']
    parameters: Optional[Any]


@dataclass
class EmployeeDeduction(BaseDataClassModel):
    Amount: Optional['DecimalValue']
    ApplicableEarnings: Optional['StringValue']
    CalculationMethod: Optional['StringValue']
    MaximumAmount: Optional['DecimalValue']
    MaximumFrequency: Optional['StringValue']
    Percent: Optional['DecimalValue']
    ReportingTypeCA: Optional['StringValue']
    ReportingTypeUS: Optional['StringValue']


@dataclass
class EmployeeDeductionOrBenefitDetail(BaseDataClassModel):
    Active: Optional['BooleanValue']
    ContributionAmount: Optional['DecimalValue']
    ContributionMax: Optional['DecimalValue']
    ContributionMaximumFrequency: Optional['StringValue']
    ContributionPercent: Optional['DecimalValue']
    DeductionAmount: Optional['DecimalValue']
    DeductionCode: Optional['StringValue']
    DeductionMax: Optional['DecimalValue']
    DeductionMaximumFrequency: Optional['StringValue']
    DeductionPercent: Optional['DecimalValue']
    Description: Optional['StringValue']
    EndDate: Optional['DateTimeValue']
    GarnishmentDetails: Optional['GarnishmentDetails']
    IsGarnish: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Sequence: Optional['IntValue']
    StartDate: Optional['DateTimeValue']
    UseContributionDefaults: Optional['BooleanValue']
    UseDeductionDefaults: Optional['BooleanValue']


@dataclass
class EmployeeDelegate(BaseDataClassModel):
    Delegate: Optional['StringValue']
    EmployeeName: Optional['StringValue']
    DelegationOf: Optional['StringValue']
    StartsOn: Optional['DateTimeValue']
    ExpiresOn: Optional['DateTimeValue']
    IsActive: Optional['BooleanValue']


@dataclass
class EmployeeFinancialSettings(BaseDataClassModel):
    APAccount: Optional['StringValue']
    APSubaccount: Optional['StringValue']
    CashAccount: Optional['StringValue']
    ExpenseAccount: Optional['StringValue']
    ExpenseSubaccount: Optional['StringValue']
    PaymentInstructions: List[Optional['BusinessAccountPaymentInstructionDetail']]
    PaymentMethod: Optional['StringValue']
    PrepaymentAccount: Optional['StringValue']
    PrepaymentSubaccount: Optional['StringValue']
    SalesAccount: Optional['StringValue']
    SalesSubaccount: Optional['StringValue']
    TaxZone: Optional['StringValue']
    Terms: Optional['StringValue']


@dataclass
class EmployeeGLAccounts(BaseDataClassModel):
    BenefitExpenseAccount: Optional['StringValue']
    BenefitExpenseSub: Optional['StringValue']
    BenefitLiabilityAccount: Optional['StringValue']
    BenefitLiabilitySub: Optional['StringValue']
    DeductionLiabilityAccount: Optional['StringValue']
    DeductionLiabilitySub: Optional['StringValue']
    EarningsAccount: Optional['StringValue']
    EarningsSub: Optional['StringValue']
    PTOAssetAccount: Optional['StringValue']
    PTOAssetSub: Optional['StringValue']
    PTOExpenseAccount: Optional['StringValue']
    PTOExpenseSub: Optional['StringValue']
    PTOLiabilityAccount: Optional['StringValue']
    PTOLiabilitySub: Optional['StringValue']
    TaxExpenseAccount: Optional['StringValue']
    TaxExpenseSub: Optional['StringValue']
    TaxLiabilityAccount: Optional['StringValue']
    TaxLiabilitySub: Optional['StringValue']


@dataclass
class EmployeeGeneralInfo(BaseDataClassModel):
    Calendar: Optional['StringValue']
    CalendarClassDefault: Optional['BooleanValue']
    CertifiedProjectHoursperYear: Optional['IntValue']
    DefaultUnion: Optional['StringValue']
    DefaultWCCCode: Optional['StringValue']
    ExemptFromCertReporting: Optional['BooleanValue']
    ExemptFromCertReportingClassDefault: Optional['BooleanValue']
    ExemptFromOvertimeRules: Optional['BooleanValue']
    ExemptFromOvertimeRulesClassDefault: Optional['BooleanValue']
    NetPayMinClassDefault: Optional['BooleanValue']
    NetPayMinimum: Optional['DecimalValue']
    OverrideHoursPerYearForCertClassDefault: Optional['BooleanValue']
    OverrideHrsPerYearForCertProjects: Optional['BooleanValue']
    PayGroup: Optional['StringValue']
    PayGroupClassDefault: Optional['BooleanValue']
    UnionClassDefault: Optional['BooleanValue']
    UseClassDefaultValueHoursPerYearForCertifiedUseDflt: Optional['BooleanValue']
    WCCCodeClassDefault: Optional['BooleanValue']
    WeeksPerYearClassDefault: Optional['BooleanValue']
    WorkingHoursPerWeek: Optional['DecimalValue']
    WorkingHoursPerYear: Optional['DecimalValue']
    WorkingWeeksPerYear: Optional['ByteValue']


@dataclass
class EmployeePaidTimeOff(BaseDataClassModel):
    PaidTimeOffDetails: List[Optional['EmployeePaidTimeOffDetail']]
    UseCustomSettings: Optional['BooleanValue']


@dataclass
class EmployeePaidTimeOffDetail(BaseDataClassModel):
    AccrualMethod: Optional['StringValue']
    AccrualPercent: Optional['DecimalValue']
    Active: Optional['BooleanValue']
    AllowNegativeBalance: Optional['BooleanValue']
    AllowViewAvailablePTOPaidHours: Optional['BooleanValue']
    BalanceLimit: Optional['DecimalValue']
    BandingRule: Optional['IntValue']
    CanOnlyDisbursefromCarryover: Optional['BooleanValue']
    CarryoverHours: Optional['DecimalValue']
    CarryoverType: Optional['StringValue']
    Description: Optional['StringValue']
    FrontLoadingHours: Optional['DecimalValue']
    HoursperYear: Optional['DecimalValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    OnSettlement: Optional['StringValue']
    ProbationPeriodBehaviour: Optional['StringValue']
    PTOBank: Optional['StringValue']
    StartDate: Optional['DateTimeValue']
    TransferDate: Optional['DateTimeValue']


@dataclass
class EmployeePaycheckEarningDetail(BaseDataClassModel):
    Account: Optional['StringValue']
    Amount: Optional['DecimalValue']
    Branch: Optional['StringValue']
    CertifiedJob: Optional['BooleanValue']
    Code: Optional['StringValue']
    CostCode: Optional['StringValue']
    Date: Optional['DateTimeValue']
    Description: Optional['StringValue']
    Hours: Optional['DecimalValue']
    LaborItem: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Location: Optional['StringValue']
    ManualRate: Optional['BooleanValue']
    Project: Optional['StringValue']
    Rate: Optional['DecimalValue']
    ShiftCode: Optional['StringValue']
    Subaccount: Optional['StringValue']
    Task: Optional['StringValue']
    UnionLocal: Optional['StringValue']
    Units: Optional['DecimalValue']
    UnitType: Optional['StringValue']
    WCCCode: Optional['StringValue']


@dataclass
class EmployeePaycheckEarnings(BaseDataClassModel):
    Amount: Optional['DecimalValue']
    Employee: Optional['StringValue']
    EmployeeType: Optional['StringValue']
    Hours: Optional['DecimalValue']
    ManualAmount: Optional['BooleanValue']
    RegularAmounttoBePaid: Optional['DecimalValue']


@dataclass
class EmployeePaycheckSummary(BaseDataClassModel):
    Amount: Optional['DecimalValue']
    Employee: Optional['StringValue']
    EmployeeName: Optional['StringValue']
    EmployeePaycheckEarnings: Optional['EmployeePaycheckEarnings']
    Hours: Optional['DecimalValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    PaycheckRef: Optional['StringValue']
    Rate: Optional['DecimalValue']
    VoidPaycheckRef: Optional['StringValue']


@dataclass
class EmployeePayrollClass(BaseDataClassModel):
    Description: Optional['StringValue']
    EmployeePayrollClassID: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    PayrollDefaults: Optional['EmployeePayrollClassDefaults']


@dataclass
class EmployeePayrollClassCustomAction(BaseDataClassModel):
    entity: Optional['EmployeePayrollClass']
    parameters: Optional[Any]


@dataclass
class EmployeePayrollClassDefaults(BaseDataClassModel):
    CertifiedProjectHoursperYear: Optional['IntValue']
    DefaultCalendar: Optional['StringValue']
    DefaultUnion: Optional['StringValue']
    DefaultWCCCode: Optional['StringValue']
    EmployeeType: Optional['StringValue']
    ExemptFromCertifiedReporting: Optional['BooleanValue']
    ExemptFromOvertimeRules: Optional['BooleanValue']
    HoursPerYearForCertified: Optional['StringValue']
    MaximumPercentofNetPayforallGarnishments: Optional['DecimalValue']
    NetPayMinimum: Optional['DecimalValue']
    OverrideHoursPerYearforCertProject: Optional['BooleanValue']
    PayGroup: Optional['StringValue']
    UsePayrollWorkLocationfromProject: Optional['BooleanValue']
    WorkingHoursPerWeek: Optional['DecimalValue']
    WorkingHoursPerYear: Optional['DecimalValue']
    WorkingWeeksPerYear: Optional['ByteValue']
    WorkLocations: List[Optional['EmployeeClassWorkLocation']]


@dataclass
class EmployeePayrollSettings(BaseDataClassModel):
    Active: Optional['BooleanValue']
    AddressInfo: Optional['Address']
    CashAccount: Optional['StringValue']
    ClassID: Optional['StringValue']
    Compensation: List[Optional['CompensationDetail']]
    DeductionsAndBenefits: Optional['DeductionsAndBenefits']
    DirectDepositDetails: List[Optional['DirectDepositDetail']]
    EmployeeID: Optional['StringValue']
    EmployeeName: Optional['StringValue']
    EmployeeType: Optional['StringValue']
    EmploymentDates: Optional['EmploymentDates']
    EmploymentRecords: List[Optional['EmploymentRecord']]
    GeneralInfo: Optional['EmployeeGeneralInfo']
    GLAccounts: Optional['EmployeeGLAccounts']
    LastModifiedDateTime: Optional['DateTimeValue']
    PaidTimeOff: Optional['EmployeePaidTimeOff']
    PaymentMethod: Optional['StringValue']
    Taxes: List[Optional['EmployeeTaxDetail']]
    TaxSettings: List[Optional['TaxSettingDetail']]
    EmployeeTypeClassDefault: Optional['BooleanValue']
    WorkLocations: Optional['EmployeeWorkLocations']


@dataclass
class EmployeePayrollSettingsCustomAction(BaseDataClassModel):
    entity: Optional['EmployeePayrollSettings']
    parameters: Optional[Any]


@dataclass
class EmployeeSettings(BaseDataClassModel):
    BranchID: Optional['StringValue']
    Calendar: Optional['StringValue']
    CurrencyID: Optional['StringValue']
    CurrencyRateTypeID: Optional['StringValue']
    DepartmentID: Optional['StringValue']
    EmployeeClass: Optional['StringValue']
    EmployeeRefNbr: Optional['StringValue']
    EnableCurrencyOverride: Optional['BooleanValue']
    EnableRateOverride: Optional['BooleanValue']
    LaborItem: Optional['StringValue']
    RegularHoursValidation: Optional['StringValue']
    ReportsTo: Optional['StringValue']
    RouteEmails: Optional['BooleanValue']
    Salesperson: Optional['StringValue']
    TimeCardIsRequired: Optional['BooleanValue']
    UnionLocalID: Optional['StringValue']


@dataclass
class EmployeeTaxDetail(BaseDataClassModel):
    Active: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    TaxCode: Optional['StringValue']
    TaxCodeSettings: List[Optional['TaxCodeSetting']]
    TaxDescription: Optional['StringValue']


@dataclass
class EmployeeWorkLocationDetail(BaseDataClassModel):
    DefaultWorkLocation: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    LocationID: Optional['StringValue']
    LocationName: Optional['StringValue']


@dataclass
class EmployeeWorkLocations(BaseDataClassModel):
    UseClassDefaultValueUsePayrollProjectWorkLocationUseDflt: Optional['BooleanValue']
    UsePayrollWorkLocationfromProject: Optional['BooleanValue']
    WorkLocationClassDefaults: Optional['BooleanValue']
    WorkLocationDetails: List[Optional['EmployeeWorkLocationDetail']]


@dataclass
class EmployerContribution(BaseDataClassModel):
    Amount: Optional['DecimalValue']
    ApplicableEarnings: Optional['StringValue']
    CalculationMethod: Optional['StringValue']
    CertifiedReportingType: Optional['StringValue']
    ContributestoGrossCalculation: Optional['BooleanValue']
    MaximumAmount: Optional['DecimalValue']
    MaximumFrequency: Optional['StringValue']
    NoFinancialTransaction: Optional['BooleanValue']
    Percent: Optional['DecimalValue']
    ReportingTypeCA: Optional['StringValue']
    ReportingTypeUS: Optional['StringValue']


@dataclass
class EmployerTaxesIncreasingApplWage(BaseDataClassModel):
    EmployerTaxesIncreasingApplWageDetails: List[Optional['EmployerTaxesIncreasingApplWageDetail']]
    InclusionType: Optional['StringValue']


@dataclass
class EmployerTaxesIncreasingApplWageDetail(BaseDataClassModel):
    LastModifiedDateTime: Optional['DateTimeValue']
    TaxCategory: Optional['StringValue']
    TaxCode: Optional['StringValue']
    TaxName: Optional['StringValue']


@dataclass
class EmploymentDates(BaseDataClassModel):
    HireDate: Optional['DateTimeValue']
    TerminationDate: Optional['DateTimeValue']


@dataclass
class EmploymentHistoryRecord(BaseDataClassModel):
    Active: Optional['BooleanValue']
    EndDate: Optional['DateTimeValue']
    LineNbr: Optional['IntValue']
    PositionID: Optional['StringValue']
    RehireEligible: Optional['BooleanValue']
    StartDate: Optional['DateTimeValue']
    StartReason: Optional['StringValue']
    Terminated: Optional['BooleanValue']
    TerminationReason: Optional['StringValue']


@dataclass
class EmploymentRecord(BaseDataClassModel):
    Active: Optional['BooleanValue']
    EndDate: Optional['DateTimeValue']
    FinalPayment: Optional['GuidValue']
    Position: Optional['StringValue']
    RehireEligible: Optional['BooleanValue']
    StartDate: Optional['DateTimeValue']
    StartReason: Optional['StringValue']
    ProbationPeriodEndDate: Optional['DateTimeValue']
    Terminated: Optional['BooleanValue']
    TerminationReason: Optional['StringValue']


@dataclass
class Entity(BaseDataClassModel):
    custom: Optional[Any]
    files: List[Optional['FileLink']]


@dataclass
class Event(BaseDataClassModel):
    AllDay: Optional['BooleanValue']
    Attendees: List[Optional['EventAttendee']]
    Body: Optional['StringValue']
    Category: Optional['StringValue']
    EndDate: Optional['DateTimeValue']
    EndTime: Optional['DateTimeValue']
    Internal: Optional['BooleanValue']
    Location: Optional['StringValue']
    NoteID: Optional['GuidValue']
    Priority: Optional['StringValue']
    RelatedActivities: List[Optional['ActivityDetail']]
    Reminder: Optional['ReminderDetail']
    ShowAs: Optional['StringValue']
    StartDate: Optional['DateTimeValue']
    Status: Optional['StringValue']
    Summary: Optional['StringValue']
    TimeActivity: Optional['EventTimeActivity']
    CreatedByID: Optional['StringValue']
    CreatedDateTime: Optional['DateTimeValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    RelatedEntityType: Optional['StringValue']
    RelatedEntityNoteID: Optional['GuidValue']
    RelatedEntityDescription: Optional['StringValue']


@dataclass
class EventAttendee(BaseDataClassModel):
    Comment: Optional['StringValue']
    Email: Optional['StringValue']
    EventNoteID: Optional['GuidValue']
    InvitationStatus: Optional['StringValue']
    Key: Optional['StringValue']
    Name: Optional['StringValue']
    NameAttendeeName: Optional['StringValue']
    Type: Optional['IntValue']


@dataclass
class EventCustomAction(BaseDataClassModel):
    entity: Optional['Event']
    parameters: Optional[Any]


@dataclass
class EventTimeActivity(BaseDataClassModel):
    BillableOvertime: Optional['StringValue']
    BillableTime: Optional['StringValue']
    Overtime: Optional['StringValue']
    TimeSpent: Optional['StringValue']


@dataclass
class ExpenseClaim(BaseDataClassModel):
    ApprovalDate: Optional['DateTimeValue']
    ApprovalDetails: List[Optional['Approval']]
    BaseCurrencyID: Optional['StringValue']
    ClaimedBy: Optional['StringValue']
    ClaimTotal: Optional['DecimalValue']
    CurrencyID: Optional['StringValue']
    CurrencyRate: Optional['DecimalValue']
    CustomerID: Optional['StringValue']
    Date: Optional['DateTimeValue']
    DepartmentID: Optional['StringValue']
    Description: Optional['StringValue']
    Details: List[Optional['ExpenseClaimDetails']]
    FinancialDetails: Optional['ExpenseClaimFinancialDetail']
    LastModifiedDateTime: Optional['DateTimeValue']
    LocationID: Optional['StringValue']
    ReciprocalRate: Optional['DecimalValue']
    RefNbr: Optional['StringValue']
    Status: Optional['StringValue']
    TaxDetails: List[Optional['ExpenseClaimTaxDetail']]
    TaxTotal: Optional['DecimalValue']
    VATExemptTotal: Optional['DecimalValue']
    VATTaxableTotal: Optional['DecimalValue']


@dataclass
class ExpenseClaimAPDocument(BaseDataClassModel):
    Amount: Optional['DecimalValue']
    RefNbr: Optional['StringValue']
    Status: Optional['StringValue']
    TaxZone: Optional['StringValue']
    Type: Optional['StringValue']


@dataclass
class ExpenseClaimCustomAction(BaseDataClassModel):
    entity: Optional['ExpenseClaim']
    parameters: Optional[Any]


@dataclass
class ExpenseClaimDetails(BaseDataClassModel):
    Amount: Optional['DecimalValue']
    AmountInClaimCurrency: Optional['DecimalValue']
    APRefNbr: Optional['StringValue']
    ARRefNbr: Optional['StringValue']
    Billable: Optional['BooleanValue']
    Branch: Optional['StringValue']
    ClaimAmount: Optional['DecimalValue']
    CostCode: Optional['StringValue']
    CurrencyID: Optional['StringValue']
    CustomerID: Optional['StringValue']
    Date: Optional['DateTimeValue']
    Description: Optional['StringValue']
    EmployeePart: Optional['DecimalValue']
    ExpenseAccount: Optional['StringValue']
    ExpenseItemID: Optional['StringValue']
    ExpenseSubaccount: Optional['StringValue']
    LocationID: Optional['StringValue']
    NetAmount: Optional['DecimalValue']
    ProjectID: Optional['StringValue']
    ProjectTaskID: Optional['StringValue']
    Qty: Optional['DecimalValue']
    RefNbr: Optional['StringValue']
    SalesAccount: Optional['StringValue']
    SalesSubaccount: Optional['StringValue']
    Status: Optional['StringValue']
    TaxAmount: Optional['DecimalValue']
    TaxCategory: Optional['StringValue']
    TaxZone: Optional['StringValue']
    TipAmount: Optional['DecimalValue']
    UnitCost: Optional['DecimalValue']
    UOM: Optional['StringValue']


@dataclass
class ExpenseClaimFinancialDetail(BaseDataClassModel):
    APDocuments: List[Optional['ExpenseClaimAPDocument']]
    Branch: Optional['StringValue']
    PosttoPeriod: Optional['StringValue']
    TaxZone: Optional['StringValue']


@dataclass
class ExpenseClaimTaxDetail(BaseDataClassModel):
    DeductibleTaxRate: Optional['DecimalValue']
    ExpenseAmount: Optional['DecimalValue']
    IncludeinVATExemptTotal: Optional['BooleanValue']
    PendingVAT: Optional['BooleanValue']
    ReverseVAT: Optional['BooleanValue']
    StatisticalVAT: Optional['BooleanValue']
    TaxableAmount: Optional['DecimalValue']
    TaxAmount: Optional['DecimalValue']
    TaxID: Optional['StringValue']
    TaxRate: Optional['DecimalValue']
    TaxType: Optional['StringValue']


@dataclass
class ExpenseReceipt(BaseDataClassModel):
    Branch: Optional['StringValue']
    ClaimAmount: Optional['DecimalValue']
    ClaimedBy: Optional['StringValue']
    Date: Optional['DateTimeValue']
    ExpenseItemID: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    ReceiptDetails: Optional['ExpenseReceiptDetails']
    ReceiptID: Optional['StringValue']
    Status: Optional['StringValue']
    TaxDetails: List[Optional['ExpenseReceiptTaxDetails']]
    TaxTotal: Optional['DecimalValue']


@dataclass
class ExpenseReceiptCustomAction(BaseDataClassModel):
    entity: Optional['ExpenseReceipt']
    parameters: Optional[Any]


@dataclass
class ExpenseReceiptDetails(BaseDataClassModel):
    Amount: Optional['DecimalValue']
    BaseCurrencyID: Optional['StringValue']
    Billable: Optional['BooleanValue']
    CostCode: Optional['StringValue']
    CurrancyRateTypeID: Optional['StringValue']
    CurrencyID: Optional['StringValue']
    CurrencyRate: Optional['DecimalValue']
    CustomerID: Optional['StringValue']
    Description: Optional['StringValue']
    EmployeePart: Optional['DecimalValue']
    ExpenseAccount: Optional['StringValue']
    ExpenseClaimID: Optional['StringValue']
    ExpenseClaimStatus: Optional['StringValue']
    ExpenseSubaccount: Optional['StringValue']
    LocationID: Optional['StringValue']
    ProjectID: Optional['StringValue']
    ProjectTaskID: Optional['StringValue']
    Qty: Optional['DecimalValue']
    ReciprocalRate: Optional['DecimalValue']
    RefNbr: Optional['StringValue']
    SalesAccount: Optional['StringValue']
    SalesSubaccount: Optional['StringValue']
    TaxCategory: Optional['StringValue']
    TaxZone: Optional['StringValue']
    UnitCost: Optional['DecimalValue']
    UOM: Optional['StringValue']


@dataclass
class ExpenseReceiptTaxDetails(BaseDataClassModel):
    DeductibleTaxRate: Optional['DecimalValue']
    ExpenseAmount: Optional['DecimalValue']
    IncludeInVATExemptTotal: Optional['BooleanValue']
    PendingVAT: Optional['BooleanValue']
    ReverseVAT: Optional['BooleanValue']
    StatisticalVAT: Optional['BooleanValue']
    TaxableAmount: Optional['DecimalValue']
    TaxAmount: Optional['DecimalValue']
    TaxID: Optional['StringValue']
    TaxRate: Optional['DecimalValue']
    TaxType: Optional['StringValue']


@dataclass
class ExportCardEvent(BaseDataClassModel):
    entity: Optional['Event']


@dataclass
class ExternalCommitment(BaseDataClassModel):
    AccountGroup: Optional['StringValue']
    CommittedCOAmount: Optional['DecimalValue']
    CommittedCOQty: Optional['DecimalValue']
    CommittedInvoicedAmount: Optional['DecimalValue']
    CommittedInvoicedQty: Optional['DecimalValue']
    CommittedOpenAmount: Optional['DecimalValue']
    CommittedOpenQty: Optional['DecimalValue']
    CommittedReceivedQty: Optional['DecimalValue']
    CostCode: Optional['StringValue']
    ExternalRefNbr: Optional['StringValue']
    InventoryID: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    OriginalCommittedAmount: Optional['DecimalValue']
    OriginalCommittedQty: Optional['DecimalValue']
    ProjectID: Optional['StringValue']
    ProjectTaskID: Optional['StringValue']
    RelatedDocument: Optional['StringValue']
    RevisedCommittedAmount: Optional['DecimalValue']
    RevisedCommittedQty: Optional['DecimalValue']
    Type: Optional['StringValue']
    UOM: Optional['StringValue']


@dataclass
class ExternalCommitmentCustomAction(BaseDataClassModel):
    entity: Optional['ExternalCommitment']
    parameters: Optional[Any]


@dataclass
class FOBPoint(BaseDataClassModel):
    Description: Optional['StringValue']
    FOBPointID: Optional['StringValue']


@dataclass
class FOBPointCustomAction(BaseDataClassModel):
    entity: Optional['FOBPoint']
    parameters: Optional[Any]


@dataclass
class FileLink(BaseDataClassModel):
    filename: Optional[Any]
    href: Optional[Any]
    comment: Optional[Any]


@dataclass
class FinancialPeriod(BaseDataClassModel):
    CreatedDateTime: Optional['DateTimeValue']
    Details: List[Optional['FinancialPeriodDetail']]
    FinancialYear: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    NbrOfPeriods: Optional['ShortValue']
    StartDate: Optional['DateTimeValue']
    UserDefinedPeriods: Optional['BooleanValue']


@dataclass
class FinancialPeriodCustomAction(BaseDataClassModel):
    entity: Optional['FinancialPeriod']
    parameters: Optional[Any]


@dataclass
class FinancialPeriodDetail(BaseDataClassModel):
    AdjustmentPeriod: Optional['BooleanValue']
    ClosedInAP: Optional['BooleanValue']
    ClosedInAR: Optional['BooleanValue']
    ClosedInCA: Optional['BooleanValue']
    ClosedInFA: Optional['BooleanValue']
    ClosedInIN: Optional['BooleanValue']
    Description: Optional['StringValue']
    EndDate: Optional['DateTimeValue']
    FinancialPeriodID: Optional['StringValue']
    LengthInDays: Optional['IntValue']
    PeriodNbr: Optional['StringValue']
    StartDate: Optional['DateTimeValue']
    Status: Optional['StringValue']


@dataclass
class FinancialSettings(BaseDataClassModel):
    BillSeparately: Optional['BooleanValue']
    Branch: Optional['StringValue']
    CashDiscountDate: Optional['DateTimeValue']
    CustomerTaxZone: Optional['StringValue']
    DueDate: Optional['DateTimeValue']
    EntityUsageType: Optional['StringValue']
    InvoiceDate: Optional['DateTimeValue']
    InvoiceNbr: Optional['StringValue']
    OriginalOrderNbr: Optional['StringValue']
    OriginalOrderType: Optional['StringValue']
    OverrideTaxZone: Optional['BooleanValue']
    Owner: Optional['StringValue']
    PostPeriod: Optional['StringValue']
    Terms: Optional['StringValue']


@dataclass
class FinancialYear(BaseDataClassModel):
    AdjustToPeriodStart: Optional['BooleanValue']
    BelongsToNextYear: Optional['BooleanValue']
    CreatedDateTime: Optional['DateTimeValue']
    DayOfWeek: Optional['StringValue']
    Details: List[Optional['FinancialYearPeriodDetail']]
    FinancialYearStartsOn: Optional['DateTimeValue']
    FirstFinancialYear: Optional['StringValue']
    FirstPeriodStartDate: Optional['DateTimeValue']
    HasAdjustmentPeriod: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    LengthOfFinancialPeriodInDays: Optional['ShortValue']
    NbrOfFinancialPeriods: Optional['ShortValue']
    PeriodsStartDayOfWeek: Optional['StringValue']
    PeriodType: Optional['StringValue']
    UserDefinedPeriods: Optional['BooleanValue']
    YearEndCalculationMethod: Optional['StringValue']


@dataclass
class FinancialYearCustomAction(BaseDataClassModel):
    entity: Optional['FinancialYear']
    parameters: Optional[Any]


@dataclass
class FinancialYearPeriodDetail(BaseDataClassModel):
    Description: Optional['StringValue']
    EndDate: Optional['DateTimeValue']
    PeriodNbr: Optional['StringValue']
    StartDate: Optional['DateTimeValue']


@dataclass
class FinishCountingPhysicalInventory(BaseDataClassModel):
    entity: Optional['PhysicalInventoryReview']


@dataclass
class GarnishmentDetails(BaseDataClassModel):
    GarnCourtDate: Optional['DateTimeValue']
    GarnCourtName: Optional['StringValue']
    GarnDocRefNbr: Optional['StringValue']
    GarnOrigAmount: Optional['DecimalValue']
    GarnPaidAmount: Optional['DecimalValue']
    GarnVendorID: Optional['StringValue']
    GarnVendorInvDescr: Optional['StringValue']


@dataclass
class GuidValue(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class HoldChangeOrder(BaseDataClassModel):
    entity: Optional['ChangeOrder']


@dataclass
class HoldProFormaInvoice(BaseDataClassModel):
    entity: Optional['ProFormaInvoice']


@dataclass
class HoldProject(BaseDataClassModel):
    entity: Optional['Project']


@dataclass
class HoldProjectTask(BaseDataClassModel):
    entity: Optional['ProjectTask']


@dataclass
class HoldProjectTemplate(BaseDataClassModel):
    entity: Optional['ProjectTemplate']


@dataclass
class HttpError(BaseDataClassModel):
    message: Optional[Any]
    exceptionMessage: Optional[Any]
    exceptionType: Optional[Any]
    stackTrace: Optional[Any]
    modelState: Optional[Any]
    messageDetail: Optional[Any]


@dataclass
class ImportEmployeeTaxes(BaseDataClassModel):
    entity: Optional['EmployeePayrollSettings']


@dataclass
class IntValue(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class InventoryAdjustment(BaseDataClassModel):
    Date: Optional['DateTimeValue']
    Description: Optional['StringValue']
    Details: List[Optional['InventoryAdjustmentDetail']]
    ExternalRef: Optional['StringValue']
    Hold: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    ReferenceNbr: Optional['StringValue']
    Status: Optional['StringValue']
    TotalCost: Optional['DecimalValue']
    TotalQty: Optional['DecimalValue']


@dataclass
class InventoryAdjustmentCustomAction(BaseDataClassModel):
    entity: Optional['InventoryAdjustment']
    parameters: Optional[Any]


@dataclass
class InventoryAdjustmentDetail(BaseDataClassModel):
    BranchID: Optional['StringValue']
    CostCode: Optional['StringValue']
    CostLayerType: Optional['StringValue']
    Description: Optional['StringValue']
    ExpirationDate: Optional['DateTimeValue']
    ExtendedCost: Optional['DecimalValue']
    InventoryID: Optional['StringValue']
    LocationID: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    Project: Optional['StringValue']
    ProjectTask: Optional['StringValue']
    Qty: Optional['DecimalValue']
    ReasonCode: Optional['StringValue']
    ReceiptNbr: Optional['StringValue']
    SpecialOrderNbr: Optional['StringValue']
    Subitem: Optional['StringValue']
    UOM: Optional['StringValue']
    WarehouseID: Optional['StringValue']


@dataclass
class InventoryAllocationInquiry(BaseDataClassModel):
    Available: Optional['DecimalValue']
    AvailableForIssue: Optional['DecimalValue']
    AvailableForShipping: Optional['DecimalValue']
    BaseUnit: Optional['StringValue']
    InTransit: Optional['DecimalValue']
    InTransitToSO: Optional['DecimalValue']
    InventoryID: Optional['StringValue']
    InventoryIssues: Optional['DecimalValue']
    InventoryReceipts: Optional['DecimalValue']
    KitAssemblyDemand: Optional['DecimalValue']
    KitAssemblySupply: Optional['DecimalValue']
    Location: Optional['StringValue']
    OnHand: Optional['DecimalValue']
    OnLocationNotAvailable: Optional['DecimalValue']
    PurchaseForSO: Optional['DecimalValue']
    PurchaseForSOPrepared: Optional['DecimalValue']
    PurchaseOrders: Optional['DecimalValue']
    PurchasePrepared: Optional['DecimalValue']
    PurchaseReceipts: Optional['DecimalValue']
    ReceiptsForSO: Optional['DecimalValue']
    Results: List[Optional['InventoryAllocationRow']]
    SOAllocated: Optional['DecimalValue']
    SOBackOrdered: Optional['DecimalValue']
    SOBooked: Optional['DecimalValue']
    SOPrepared: Optional['DecimalValue']
    SOShipped: Optional['DecimalValue']
    SOToPurchase: Optional['DecimalValue']
    TotalAddition: Optional['DecimalValue']
    TotalDeduction: Optional['DecimalValue']
    WarehouseID: Optional['StringValue']


@dataclass
class InventoryAllocationInquiryCustomAction(BaseDataClassModel):
    entity: Optional['InventoryAllocationInquiry']
    parameters: Optional[Any]


@dataclass
class InventoryAllocationRow(BaseDataClassModel):
    AllocationDate: Optional['DateTimeValue']
    AllocationType: Optional['StringValue']
    DocType: Optional['StringValue']
    Expired: Optional['BooleanValue']
    Location: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    Module: Optional['StringValue']
    Qty: Optional['DecimalValue']


@dataclass
class InventoryFileUrls(BaseDataClassModel):
    FileType: Optional['StringValue']
    FileURL: Optional['StringValue']
    NoteID: Optional['GuidValue']


@dataclass
class InventoryIssue(BaseDataClassModel):
    ControlAmount: Optional['DecimalValue']
    ControlQty: Optional['DecimalValue']
    Date: Optional['DateTimeValue']
    Description: Optional['StringValue']
    Details: List[Optional['InventoryIssueDetail']]
    ExternalRef: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    PostPeriod: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    Status: Optional['StringValue']
    TotalAmount: Optional['DecimalValue']
    TotalCost: Optional['DecimalValue']
    TotalQty: Optional['DecimalValue']


@dataclass
class InventoryIssueCustomAction(BaseDataClassModel):
    entity: Optional['InventoryIssue']
    parameters: Optional[Any]


@dataclass
class InventoryIssueDetail(BaseDataClassModel):
    Allocations: List[Optional['InventoryIssueDetailAllocation']]
    Branch: Optional['StringValue']
    CostCode: Optional['StringValue']
    CostLayerType: Optional['StringValue']
    Description: Optional['StringValue']
    ExpirationDate: Optional['DateTimeValue']
    ExtCost: Optional['DecimalValue']
    ExtPrice: Optional['DecimalValue']
    InventoryID: Optional['StringValue']
    LineNumber: Optional['IntValue']
    Location: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    Project: Optional['StringValue']
    ProjectTask: Optional['StringValue']
    Qty: Optional['DecimalValue']
    ReasonCode: Optional['StringValue']
    SpecialOrderNbr: Optional['StringValue']
    Subitem: Optional['StringValue']
    TranType: Optional['StringValue']
    UnitCost: Optional['DecimalValue']
    UnitPrice: Optional['DecimalValue']
    UOM: Optional['StringValue']
    WarehouseID: Optional['StringValue']


@dataclass
class InventoryIssueDetailAllocation(BaseDataClassModel):
    ExpirationDate: Optional['DateTimeValue']
    InventoryID: Optional['StringValue']
    Location: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    Qty: Optional['DecimalValue']
    SplitLineNumber: Optional['IntValue']
    Subitem: Optional['StringValue']
    UOM: Optional['StringValue']


@dataclass
class InventoryItemCrossReference(BaseDataClassModel):
    AlternateID: Optional['StringValue']
    AlternateType: Optional['StringValue']
    Description: Optional['StringValue']
    Subitem: Optional['StringValue']
    VendorOrCustomer: Optional['StringValue']
    UOM: Optional['StringValue']


@dataclass
class InventoryItemUOMConversion(BaseDataClassModel):
    ConversionFactor: Optional['DecimalValue']
    FromUOM: Optional['StringValue']
    MultiplyOrDivide: Optional['StringValue']
    ToUOM: Optional['StringValue']


@dataclass
class InventoryQuantityAvailable(BaseDataClassModel):
    InventoryID: Optional['StringValue']
    Results: List[Optional['InventoryQuantityAvailableDetail']]
    LastModifiedDateTime: Optional['DateTimeValue']


@dataclass
class InventoryQuantityAvailableCustomAction(BaseDataClassModel):
    entity: Optional['InventoryQuantityAvailable']
    parameters: Optional[Any]


@dataclass
class InventoryQuantityAvailableDetail(BaseDataClassModel):
    InventoryID: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    QtyAvailable: Optional['DecimalValue']


@dataclass
class InventoryReceipt(BaseDataClassModel):
    ControlCost: Optional['DecimalValue']
    ControlQty: Optional['DecimalValue']
    Date: Optional['DateTimeValue']
    Description: Optional['StringValue']
    Details: List[Optional['InventoryReceiptDetail']]
    Hold: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    PostPeriod: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    Status: Optional['StringValue']
    TotalCost: Optional['DecimalValue']
    TotalQty: Optional['DecimalValue']
    TransferNbr: Optional['StringValue']


@dataclass
class InventoryReceiptCustomAction(BaseDataClassModel):
    entity: Optional['InventoryReceipt']
    parameters: Optional[Any]


@dataclass
class InventoryReceiptDetail(BaseDataClassModel):
    Allocations: List[Optional['InventoryReceiptDetailAllocation']]
    CostCode: Optional['StringValue']
    CostLayerType: Optional['StringValue']
    Description: Optional['StringValue']
    ExpirationDate: Optional['DateTimeValue']
    ExtCost: Optional['DecimalValue']
    InventoryID: Optional['StringValue']
    LineNumber: Optional['IntValue']
    Location: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    POReceiptNbr: Optional['StringValue']
    Project: Optional['StringValue']
    ProjectTask: Optional['StringValue']
    ReasonCode: Optional['StringValue']
    Qty: Optional['DecimalValue']
    SpecialOrderNbr: Optional['StringValue']
    Subitem: Optional['StringValue']
    UnitCost: Optional['DecimalValue']
    UOM: Optional['StringValue']
    WarehouseID: Optional['StringValue']


@dataclass
class InventoryReceiptDetailAllocation(BaseDataClassModel):
    ExpirationDate: Optional['DateTimeValue']
    InventoryID: Optional['StringValue']
    Location: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    Qty: Optional['DecimalValue']
    SplitLineNumber: Optional['IntValue']
    Subitem: Optional['StringValue']
    UOM: Optional['StringValue']


@dataclass
class InventorySummaryInquiry(BaseDataClassModel):
    ExpandByLotSerialNbr: Optional['BooleanValue']
    InventoryID: Optional['StringValue']
    LocationID: Optional['StringValue']
    Results: List[Optional['InventorySummaryRow']]
    Subitem: Optional['StringValue']
    WarehouseID: Optional['StringValue']


@dataclass
class InventorySummaryInquiryCustomAction(BaseDataClassModel):
    entity: Optional['InventorySummaryInquiry']
    parameters: Optional[Any]


@dataclass
class InventorySummaryRow(BaseDataClassModel):
    BaseUOM: Optional['StringValue']
    EstimatedTotalCost: Optional['DecimalValue']
    EstimatedUnitCost: Optional['DecimalValue']
    ExpirationDate: Optional['DateTimeValue']
    LocationID: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    QtyAvailable: Optional['DecimalValue']
    QtyAvailableForShipment: Optional['DecimalValue']
    QtyNotAvailable: Optional['DecimalValue']
    QtyOnHand: Optional['DecimalValue']
    Subitem: Optional['StringValue']
    WarehouseID: Optional['StringValue']


@dataclass
class InviteAllEvent(BaseDataClassModel):
    entity: Optional['Event']


@dataclass
class InviteEvent(BaseDataClassModel):
    entity: Optional['Event']


@dataclass
class Invoice(BaseDataClassModel):
    Amount: Optional['DecimalValue']
    ApplicationsCreditMemo: List[Optional['InvoiceApplicationsCreditMemo']]
    ApplicationsDefault: List[Optional['InvoiceApplicationsDefault']]
    Balance: Optional['DecimalValue']
    BillingPrinted: Optional['BooleanValue']
    BillToContact: Optional['DocContact']
    BillToContactOverride: Optional['BooleanValue']
    CreatedDateTime: Optional['DateTimeValue']
    Customer: Optional['StringValue']
    CustomerOrder: Optional['StringValue']
    Date: Optional['DateTimeValue']
    Description: Optional['StringValue']
    Details: List[Optional['InvoiceDetail']]
    DiscountDetails: List[Optional['InvoiceDiscountDetail']]
    DueDate: Optional['DateTimeValue']
    Hold: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    LinkARAccount: Optional['StringValue']
    LinkBranch: Optional['StringValue']
    LocationID: Optional['StringValue']
    PostPeriod: Optional['StringValue']
    Project: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    Status: Optional['StringValue']
    ShipToContact: Optional['DocContact']
    ShipToContactOverride: Optional['BooleanValue']
    TaxDetails: List[Optional['InvoiceTaxDetail']]
    IsTaxValid: Optional['BooleanValue']
    TaxTotal: Optional['DecimalValue']
    Terms: Optional['StringValue']
    Type: Optional['StringValue']


@dataclass
class InvoiceApplicationsCreditMemo(BaseDataClassModel):
    AmountPaid: Optional['DecimalValue']
    Balance: Optional['DecimalValue']
    Customer: Optional['StringValue']
    CustomerOrder: Optional['StringValue']
    Description: Optional['StringValue']
    DocType: Optional['StringValue']
    PostPeriod: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    Status: Optional['StringValue']


@dataclass
class InvoiceApplicationsDefault(BaseDataClassModel):
    AmountPaid: Optional['DecimalValue']
    Balance: Optional['DecimalValue']
    CashDiscountTaken: Optional['DecimalValue']
    DocType: Optional['StringValue']
    PaymentDate: Optional['DateTimeValue']
    ReferenceNbr: Optional['StringValue']
    Status: Optional['StringValue']


@dataclass
class InvoiceAppointment(BaseDataClassModel):
    entity: Optional['Appointment']


@dataclass
class InvoiceCustomAction(BaseDataClassModel):
    entity: Optional['Invoice']
    parameters: Optional[Any]


@dataclass
class InvoiceDetail(BaseDataClassModel):
    Account: Optional['StringValue']
    Amount: Optional['DecimalValue']
    Branch: Optional['StringValue']
    CalculateDiscountsOnImport: Optional['BooleanValue']
    CostCode: Optional['StringValue']
    DiscountAmount: Optional['DecimalValue']
    ExtendedPrice: Optional['DecimalValue']
    InventoryID: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    LineNbr: Optional['IntValue']
    ProjectTask: Optional['StringValue']
    Qty: Optional['DecimalValue']
    Subaccount: Optional['StringValue']
    Subitem: Optional['StringValue']
    TransactionDescription: Optional['StringValue']
    UnitPrice: Optional['DecimalValue']
    UOM: Optional['StringValue']
    TaxCategory: Optional['StringValue']


@dataclass
class InvoiceDiscountDetail(BaseDataClassModel):
    Description: Optional['StringValue']
    DiscountableAmount: Optional['DecimalValue']
    DiscountableQty: Optional['DecimalValue']
    DiscountAmount: Optional['DecimalValue']
    DiscountCode: Optional['StringValue']
    DiscountPercent: Optional['DecimalValue']
    ExternalDiscountCode: Optional['StringValue']
    ManualDiscount: Optional['BooleanValue']
    OrderNbr: Optional['StringValue']
    OrderType: Optional['StringValue']
    RetainedDiscount: Optional['DecimalValue']
    SequenceID: Optional['StringValue']
    SkipDiscount: Optional['BooleanValue']
    Type: Optional['StringValue']


@dataclass
class InvoiceOrder(BaseDataClassModel):
    entity: Optional['ServiceOrder']


@dataclass
class InvoiceTaxDetail(BaseDataClassModel):
    TaxableAmount: Optional['DecimalValue']
    TaxAmount: Optional['DecimalValue']
    TaxID: Optional['StringValue']
    TaxRate: Optional['DecimalValue']


@dataclass
class ItemClass(BaseDataClassModel):
    Attributes: List[Optional['ItemClassAtrribute']]
    AvailabilityCalculationRule: Optional['StringValue']
    BaseUOM: Optional['StringValue']
    ClassID: Optional['StringValue']
    CountryOfOrigin: Optional['StringValue']
    DefaultWarehouseID: Optional['StringValue']
    Description: Optional['StringValue']
    ItemType: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    LotSerialClass: Optional['StringValue']
    PostingClass: Optional['StringValue']
    PriceClass: Optional['StringValue']
    PurchaseUOM: Optional['StringValue']
    SalesUOM: Optional['StringValue']
    StockItem: Optional['BooleanValue']
    TariffCode: Optional['StringValue']
    TaxCategoryID: Optional['StringValue']
    ValuationMethod: Optional['StringValue']


@dataclass
class ItemClassAtrribute(BaseDataClassModel):
    AttributeID: Optional['StringValue']
    Required: Optional['BooleanValue']
    SortOrder: Optional['ShortValue']


@dataclass
class ItemClassCustomAction(BaseDataClassModel):
    entity: Optional['ItemClass']
    parameters: Optional[Any]


@dataclass
class ItemPriceClassesDetails(BaseDataClassModel):
    PriceClassID: Optional['StringValue']


@dataclass
class ItemSalesCategory(BaseDataClassModel):
    CategoryID: Optional['IntValue']
    Description: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Members: List[Optional['ItemSalesCategoryMember']]
    ParentCategoryID: Optional['IntValue']
    Path: Optional['StringValue']
    SortOrder: Optional['IntValue']
    NoteID: Optional['GuidValue']


@dataclass
class ItemSalesCategoryCustomAction(BaseDataClassModel):
    entity: Optional['ItemSalesCategory']
    parameters: Optional[Any]


@dataclass
class ItemSalesCategoryMember(BaseDataClassModel):
    Description: Optional['StringValue']
    InventoryID: Optional['StringValue']
    ItemClass: Optional['StringValue']
    ItemStatus: Optional['StringValue']


@dataclass
class ItemWarehouse(BaseDataClassModel):
    CreatedDateTime: Optional['DateTimeValue']
    DefaultIssueFrom: Optional['StringValue']
    DefaultReceiptTo: Optional['StringValue']
    DefaultSubitem: Optional['StringValue']
    InventoryAccount: Optional['StringValue']
    InventoryID: Optional['StringValue']
    InventorySubaccount: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    MaxQty: Optional['DecimalValue']
    MSRP: Optional['DecimalValue']
    OverrideInventoryAccountSubaccount: Optional['BooleanValue']
    OverridePreferredVendor: Optional['BooleanValue']
    OverridePrice: Optional['BooleanValue']
    OverrideReplenishmentSettings: Optional['BooleanValue']
    OverrideServiceLevel: Optional['BooleanValue']
    OverrideStandardCost: Optional['BooleanValue']
    OverrideProductManager: Optional['BooleanValue']
    OverrideMaxQty: Optional['BooleanValue']
    OverrideReorderPoint: Optional['BooleanValue']
    OverrideSafetyStock: Optional['BooleanValue']
    PreferredLocation: Optional['StringValue']
    PreferredVendor: Optional['StringValue']
    ProductManager: Optional['StringValue']
    ProductWorkgroup: Optional['StringValue']
    ReorderPoint: Optional['DecimalValue']
    ReplenishmentClass: Optional['StringValue']
    ReplenishmentMethod: Optional['StringValue']
    ReplenishmentSource: Optional['StringValue']
    ReplenishmentWarehouse: Optional['StringValue']
    SafetyStock: Optional['DecimalValue']
    Seasonality: Optional['StringValue']
    ServiceLevel: Optional['DecimalValue']
    Status: Optional['StringValue']
    WarehouseID: Optional['StringValue']


@dataclass
class ItemWarehouseCustomAction(BaseDataClassModel):
    entity: Optional['ItemWarehouse']
    parameters: Optional[Any]


@dataclass
class ItemsDetails(BaseDataClassModel):
    Description: Optional['StringValue']
    InventoryID: Optional['StringValue']


@dataclass
class JournalTransaction(BaseDataClassModel):
    BatchNbr: Optional['StringValue']
    BranchID: Optional['StringValue']
    CreatedDateTime: Optional['DateTimeValue']
    CurrencyID: Optional['StringValue']
    Description: Optional['StringValue']
    Details: List[Optional['JournalTransactionDetail']]
    Hold: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    LedgerID: Optional['StringValue']
    Module: Optional['StringValue']
    PostPeriod: Optional['StringValue']
    Status: Optional['StringValue']
    TransactionDate: Optional['DateTimeValue']


@dataclass
class JournalTransactionCustomAction(BaseDataClassModel):
    entity: Optional['JournalTransaction']
    parameters: Optional[Any]


@dataclass
class JournalTransactionDetail(BaseDataClassModel):
    Account: Optional['StringValue']
    BranchID: Optional['StringValue']
    CostCode: Optional['StringValue']
    CreditAmount: Optional['DecimalValue']
    DebitAmount: Optional['DecimalValue']
    Description: Optional['StringValue']
    IsNonPM: Optional['BooleanValue']
    LineNbr: Optional['IntValue']
    NonBillable: Optional['BooleanValue']
    Project: Optional['StringValue']
    ProjectTask: Optional['StringValue']
    ProjectTransactionID: Optional['LongValue']
    Qty: Optional['DecimalValue']
    ReferenceNbr: Optional['StringValue']
    Subaccount: Optional['StringValue']
    TransactionDescription: Optional['StringValue']
    UOM: Optional['StringValue']
    VendorOrCustomer: Optional['StringValue']


@dataclass
class KitAssembly(BaseDataClassModel):
    Allocations: List[Optional['KitAssemblyAllocation']]
    Date: Optional['DateTimeValue']
    Description: Optional['StringValue']
    Hold: Optional['BooleanValue']
    KitInventoryID: Optional['StringValue']
    LocationID: Optional['StringValue']
    NonStockComponents: List[Optional['KitAssemblyNonStockComponent']]
    PostPeriod: Optional['StringValue']
    Qty: Optional['DecimalValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    ReasonCode: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    Revision: Optional['StringValue']
    Status: Optional['StringValue']
    StockComponents: List[Optional['KitAssemblyStockComponent']]
    Subitem: Optional['StringValue']
    Type: Optional['StringValue']
    UOM: Optional['StringValue']
    WarehouseID: Optional['StringValue']


@dataclass
class KitAssemblyAllocation(BaseDataClassModel):
    ExpirationDate: Optional['DateTimeValue']
    LineNbr: Optional['IntValue']
    LocationID: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    Qty: Optional['DecimalValue']
    SplitLineNbr: Optional['IntValue']
    Subitem: Optional['StringValue']
    UOM: Optional['StringValue']


@dataclass
class KitAssemblyCustomAction(BaseDataClassModel):
    entity: Optional['KitAssembly']
    parameters: Optional[Any]


@dataclass
class KitAssemblyNonStockComponent(BaseDataClassModel):
    ComponentQty: Optional['DecimalValue']
    LineNbr: Optional['IntValue']
    NonStockInventoryID: Optional['StringValue']
    Qty: Optional['DecimalValue']
    ReasonCode: Optional['StringValue']
    UnitCost: Optional['DecimalValue']
    UOM: Optional['StringValue']


@dataclass
class KitAssemblyStockComponent(BaseDataClassModel):
    Allocations: List[Optional['KitAssemblyStockComponentAllocation']]
    ComponentQty: Optional['DecimalValue']
    LineNbr: Optional['IntValue']
    LocationID: Optional['StringValue']
    Qty: Optional['DecimalValue']
    ReasonCode: Optional['StringValue']
    StockInventoryID: Optional['StringValue']
    Subitem: Optional['StringValue']
    UnitCost: Optional['DecimalValue']
    UOM: Optional['StringValue']


@dataclass
class KitAssemblyStockComponentAllocation(BaseDataClassModel):
    DocType: Optional['StringValue']
    ExpirationDate: Optional['DateTimeValue']
    InventoryID: Optional['StringValue']
    LineNbr: Optional['IntValue']
    LocationID: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    Qty: Optional['DecimalValue']
    ReferenceNbr: Optional['StringValue']
    SplitLineNbr: Optional['IntValue']
    Subitem: Optional['StringValue']
    UOM: Optional['StringValue']


@dataclass
class KitNonStockComponent(BaseDataClassModel):
    AllowComponentQtyVariance: Optional['BooleanValue']
    ComponentQty: Optional['DecimalValue']
    MaxComponentQty: Optional['DecimalValue']
    MinComponentQty: Optional['DecimalValue']
    NonStockInventoryID: Optional['StringValue']
    UOM: Optional['StringValue']


@dataclass
class KitSpecification(BaseDataClassModel):
    Active: Optional['BooleanValue']
    Description: Optional['StringValue']
    IsNonStock: Optional['BooleanValue']
    KitInventoryID: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    NonStockComponents: List[Optional['KitNonStockComponent']]
    RevisionID: Optional['StringValue']
    StockComponents: List[Optional['KitStockComponent']]


@dataclass
class KitSpecificationCustomAction(BaseDataClassModel):
    entity: Optional['KitSpecification']
    parameters: Optional[Any]


@dataclass
class KitStockComponent(BaseDataClassModel):
    AllowComponentQtyVariance: Optional['BooleanValue']
    ComponentQty: Optional['DecimalValue']
    MaxComponentQty: Optional['DecimalValue']
    MinComponentQty: Optional['DecimalValue']
    StockInventoryID: Optional['StringValue']
    Subitem: Optional['StringValue']
    UOM: Optional['StringValue']


@dataclass
class LaborCostRate(BaseDataClassModel):
    EffectiveDate: Optional['DateTimeValue']
    Employee: Optional['StringValue']
    LaborItem: Optional['StringValue']
    Project: Optional['StringValue']
    ProjectTask: Optional['StringValue']
    LaborRateType: Optional['StringValue']
    UnionLocal: Optional['StringValue']
    Results: List[Optional['LaborRate']]


@dataclass
class LaborCostRateCustomAction(BaseDataClassModel):
    entity: Optional['LaborCostRate']
    parameters: Optional[Any]


@dataclass
class LaborRate(BaseDataClassModel):
    AnnualRate: Optional['DecimalValue']
    CurrencyID: Optional['StringValue']
    Description: Optional['StringValue']
    EffectiveDate: Optional['DateTimeValue']
    EmployeeID: Optional['StringValue']
    EmployeeName: Optional['StringValue']
    ExternalRefNbr: Optional['StringValue']
    HourlyRate: Optional['DecimalValue']
    LaborItem: Optional['StringValue']
    LaborRateType: Optional['StringValue']
    ProjectID: Optional['StringValue']
    ProjectTaskID: Optional['StringValue']
    RecordID: Optional['IntValue']
    RegularHoursPerWeek: Optional['DecimalValue']
    TypeOfEmployment: Optional['StringValue']
    UnionLocalID: Optional['StringValue']


@dataclass
class Lead(BaseDataClassModel):
    Activities: List[Optional['ActivityDetail']]
    Address: Optional['Address']
    Attributes: List[Optional['AttributeValue']]
    BusinessAccount: Optional['StringValue']
    Campaigns: List[Optional['CampaignDetail']]
    CompanyName: Optional['StringValue']
    ContactMethod: Optional['StringValue']
    DoNotCall: Optional['BooleanValue']
    DoNotEmail: Optional['BooleanValue']
    DoNotFax: Optional['BooleanValue']
    DoNotMail: Optional['BooleanValue']
    Duplicate: Optional['StringValue']
    DuplicateFound: Optional['BooleanValue']
    Duplicates: List[Optional['DuplicateDetail']]
    Email: Optional['StringValue']
    Fax: Optional['StringValue']
    FaxType: Optional['StringValue']
    FirstName: Optional['StringValue']
    JobTitle: Optional['StringValue']
    LanguageOrLocale: Optional['StringValue']
    LastIncomingActivity: Optional['DateTimeValue']
    LastName: Optional['StringValue']
    LastOutgoingActivity: Optional['DateTimeValue']
    LeadClass: Optional['StringValue']
    LeadDisplayName: Optional['StringValue']
    LeadID: Optional['IntValue']
    MarketingLists: List[Optional['MarketingListDetail']]
    NoMarketing: Optional['BooleanValue']
    NoMassMail: Optional['BooleanValue']
    Owner: Optional['StringValue']
    OwnerEmployeeName: Optional['StringValue']
    ParentAccount: Optional['StringValue']
    Phone1: Optional['StringValue']
    Phone1Type: Optional['StringValue']
    Phone2: Optional['StringValue']
    Phone2Type: Optional['StringValue']
    Phone3: Optional['StringValue']
    Phone3Type: Optional['StringValue']
    Reason: Optional['StringValue']
    Relations: List[Optional['RelationDetail']]
    Source: Optional['StringValue']
    SourceCampaign: Optional['StringValue']
    Status: Optional['StringValue']
    Title: Optional['StringValue']
    WebSite: Optional['StringValue']
    Workgroup: Optional['StringValue']
    WorkgroupDescription: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    NoteID: Optional['GuidValue']
    Active: Optional['BooleanValue']
    Description: Optional['StringValue']
    RefContactID: Optional['IntValue']
    ConvertedBy: Optional['StringValue']
    QualificationDate: Optional['DateTimeValue']


@dataclass
class LeadCustomAction(BaseDataClassModel):
    entity: Optional['Lead']
    parameters: Optional[Any]


@dataclass
class Ledger(BaseDataClassModel):
    Branches: List[Optional['LedgerBranches']]
    Companies: List[Optional['LedgerCompanies']]
    ConsolidationSource: Optional['BooleanValue']
    Currency: Optional['StringValue']
    Description: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    LedgerID: Optional['StringValue']
    Type: Optional['StringValue']


@dataclass
class LedgerBranches(BaseDataClassModel):
    Active: Optional['BooleanValue']
    BranchID: Optional['StringValue']
    BranchName: Optional['StringValue']
    CompanyName: Optional['StringValue']


@dataclass
class LedgerCompanies(BaseDataClassModel):
    Active: Optional['BooleanValue']
    Company: Optional['StringValue']
    CompanyName: Optional['StringValue']
    CompanyType: Optional['StringValue']


@dataclass
class LedgerCustomAction(BaseDataClassModel):
    entity: Optional['Ledger']
    parameters: Optional[Any]


@dataclass
class LockProjectBudget(BaseDataClassModel):
    entity: Optional['Project']


@dataclass
class LockProjectCommitments(BaseDataClassModel):
    entity: Optional['Project']


@dataclass
class LongValue(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class LotSerialClass(BaseDataClassModel):
    AssignmentMethod: Optional['StringValue']
    ClassID: Optional['StringValue']
    Description: Optional['StringValue']
    IssueMethod: Optional['StringValue']
    Segments: List[Optional['LotSerialClassSegment']]
    TrackExpirationDate: Optional['BooleanValue']
    TrackingMethod: Optional['StringValue']


@dataclass
class LotSerialClassCustomAction(BaseDataClassModel):
    entity: Optional['LotSerialClass']
    parameters: Optional[Any]


@dataclass
class LotSerialClassSegment(BaseDataClassModel):
    SegmentNbr: Optional['ShortValue']
    Type: Optional['StringValue']
    Value: Optional['StringValue']


@dataclass
class MarkBusinessAccountAsValidated(BaseDataClassModel):
    entity: Optional['BusinessAccount']


@dataclass
class MarkContactAsValidated(BaseDataClassModel):
    entity: Optional['Contact']


@dataclass
class MarkLeadAsValidated(BaseDataClassModel):
    entity: Optional['Lead']


@dataclass
class MarketingListDetail(BaseDataClassModel):
    ContactID: Optional['IntValue']
    DynamicList: Optional['BooleanValue']
    Format: Optional['StringValue']
    ListName: Optional['StringValue']
    MarketingListID: Optional['IntValue']
    Subscribed: Optional['BooleanValue']


@dataclass
class MatrixItems(BaseDataClassModel):
    DefaultPrice: Optional['DecimalValue']
    Description: Optional['StringValue']
    InventoryID: Optional['StringValue']
    MSRP: Optional['DecimalValue']
    ItemStatus: Optional['StringValue']
    ExportToExternal: Optional['BooleanValue']


@dataclass
class NonStockItem(BaseDataClassModel):
    Attributes: List[Optional['AttributeValue']]
    BaseUnit: Optional['StringValue']
    CrossReferences: List[Optional['InventoryItemCrossReference']]
    CurrentCost: Optional['DecimalValue']
    DefaultPrice: Optional['DecimalValue']
    DeferralAccount: Optional['StringValue']
    DeferralSubaccount: Optional['StringValue']
    Description: Optional['StringValue']
    EffectiveDate: Optional['DateTimeValue']
    ExpenseAccount: Optional['StringValue']
    ExpenseAccrualAccount: Optional['StringValue']
    ExpenseAccrualSubaccount: Optional['StringValue']
    ExpenseSubaccount: Optional['StringValue']
    InventoryID: Optional['StringValue']
    IsKit: Optional['BooleanValue']
    IsAKit: Optional['BooleanValue']
    ItemClass: Optional['StringValue']
    ItemStatus: Optional['StringValue']
    ItemType: Optional['StringValue']
    LastCost: Optional['DecimalValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    PendingCost: Optional['DecimalValue']
    PendingCostDate: Optional['DateTimeValue']
    POAccrualAccount: Optional['StringValue']
    POAccrualSubaccount: Optional['StringValue']
    PostingClass: Optional['StringValue']
    PriceClass: Optional['StringValue']
    PurchasePriceVarianceAccount: Optional['StringValue']
    PurchasePriceVarianceSubaccount: Optional['StringValue']
    PurchaseUnit: Optional['StringValue']
    ReasonCodeSubaccount: Optional['StringValue']
    RequireReceipt: Optional['BooleanValue']
    RequireShipment: Optional['BooleanValue']
    SalesAccount: Optional['StringValue']
    SalesCategories: List[Optional['NonStockItemSalesCategory']]
    SalesSubaccount: Optional['StringValue']
    SalesUnit: Optional['StringValue']
    TaxCategory: Optional['StringValue']
    VendorDetails: List[Optional['NonStockItemVendorDetail']]
    Volume: Optional['DecimalValue']
    VolumeUOM: Optional['StringValue']
    Weight: Optional['DecimalValue']
    WeightUOM: Optional['StringValue']
    CurySpecificMSRP: Optional['DecimalValue']
    CurySpecificPrice: Optional['DecimalValue']
    Availability: Optional['StringValue']
    ExportToExternal: Optional['BooleanValue']
    Categories: List[Optional['CategoryStockItem']]
    Content: Optional['StringValue']
    CurrentStdCost: Optional['DecimalValue']
    CustomURL: Optional['StringValue']
    DimensionWeight: Optional['DecimalValue']
    FileUrls: List[Optional['InventoryFileUrls']]
    MetaDescription: Optional['StringValue']
    MetaKeywords: Optional['StringValue']
    MSRP: Optional['DecimalValue']
    NoteID: Optional['GuidValue']
    PageTitle: Optional['StringValue']
    SearchKeywords: Optional['StringValue']
    TemplateItemID: Optional['StringValue']
    Visibility: Optional['StringValue']


@dataclass
class NonStockItemCustomAction(BaseDataClassModel):
    entity: Optional['NonStockItem']
    parameters: Optional[Any]


@dataclass
class NonStockItemSalesCategory(BaseDataClassModel):
    CategoryID: Optional['IntValue']


@dataclass
class NonStockItemVendorDetail(BaseDataClassModel):
    RecordID: Optional['IntValue']
    VendorID: Optional['StringValue']
    VendorName: Optional['StringValue']
    Default: Optional['BooleanValue']


@dataclass
class OpenSalesOrder(BaseDataClassModel):
    entity: Optional['SalesOrder']


@dataclass
class OpenTimeEntry(BaseDataClassModel):
    entity: Optional['TimeEntry']


@dataclass
class Opportunity(BaseDataClassModel):
    Activities: List[Optional['ActivityDetail']]
    Address: Optional['Address']
    Amount: Optional['DecimalValue']
    Attributes: List[Optional['AttributeValue']]
    Branch: Optional['StringValue']
    BusinessAccount: Optional['StringValue']
    ClassID: Optional['StringValue']
    ContactDisplayName: Optional['StringValue']
    ContactID: Optional['IntValue']
    ContactInformation: Optional['OpportunityContact']
    ConvertedLeadDisplayName: Optional['StringValue']
    ConvertedLeadID: Optional['IntValue']
    CurrencyID: Optional['StringValue']
    CurrencyViewState: Optional['BooleanValue']
    Details: Optional['StringValue']
    Discount: Optional['DecimalValue']
    Discounts: List[Optional['OpportunityDiscount']]
    Estimation: Optional['DateTimeValue']
    Location: Optional['StringValue']
    ManualAmount: Optional['BooleanValue']
    OpportunityID: Optional['StringValue']
    Override: Optional['BooleanValue']
    Owner: Optional['StringValue']
    OwnerEmployeeName: Optional['StringValue']
    ParentAccount: Optional['StringValue']
    Products: List[Optional['OpportunityProduct']]
    Project: Optional['StringValue']
    Reason: Optional['StringValue']
    Relations: List[Optional['RelationDetail']]
    Source: Optional['StringValue']
    SourceCampaign: Optional['StringValue']
    Stage: Optional['StringValue']
    Status: Optional['StringValue']
    Subject: Optional['StringValue']
    TaxDetails: List[Optional['OpportunityTaxDetail']]
    TaxZone: Optional['StringValue']
    Total: Optional['DecimalValue']
    WeightTotal: Optional['DecimalValue']
    WorkgroupDescription: Optional['StringValue']
    WorkgroupID: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    NoteID: Optional['GuidValue']


@dataclass
class OpportunityContact(BaseDataClassModel):
    Attention: Optional['StringValue']
    CompanyName: Optional['StringValue']
    Email: Optional['StringValue']
    Fax: Optional['StringValue']
    FaxType: Optional['StringValue']
    FirstName: Optional['StringValue']
    LastName: Optional['StringValue']
    Phone1: Optional['StringValue']
    Phone1Type: Optional['StringValue']
    Phone2: Optional['StringValue']
    Phone2Type: Optional['StringValue']
    Phone3: Optional['StringValue']
    Phone3Type: Optional['StringValue']
    Position: Optional['StringValue']
    Title: Optional['StringValue']
    WebSite: Optional['StringValue']


@dataclass
class OpportunityCustomAction(BaseDataClassModel):
    entity: Optional['Opportunity']
    parameters: Optional[Any]


@dataclass
class OpportunityDetail(BaseDataClassModel):
    Currency: Optional['StringValue']
    DisplayName: Optional['StringValue']
    Estimation: Optional['DateTimeValue']
    Owner: Optional['StringValue']
    Probability: Optional['IntValue']
    Stage: Optional['StringValue']
    Status: Optional['StringValue']
    Subject: Optional['StringValue']
    Total: Optional['DecimalValue']
    Workgroup: Optional['StringValue']


@dataclass
class OpportunityDiscount(BaseDataClassModel):
    DiscountableAmount: Optional['DecimalValue']
    DiscountableQty: Optional['DecimalValue']
    DiscountAmount: Optional['DecimalValue']
    DiscountCode: Optional['StringValue']
    DiscountPercent: Optional['DecimalValue']
    FreeItem: Optional['StringValue']
    FreeItemQty: Optional['DecimalValue']
    LineNbr: Optional['IntValue']
    ManualDiscount: Optional['BooleanValue']
    SequenceID: Optional['StringValue']
    SkipDiscount: Optional['BooleanValue']
    Type: Optional['StringValue']


@dataclass
class OpportunityProduct(BaseDataClassModel):
    Amount: Optional['DecimalValue']
    Discount: Optional['DecimalValue']
    DiscountAmount: Optional['DecimalValue']
    DiscountCode: Optional['StringValue']
    DiscountSequence: Optional['StringValue']
    ExternalPrice: Optional['DecimalValue']
    FreeItem: Optional['BooleanValue']
    InventoryID: Optional['StringValue']
    ManualDiscount: Optional['BooleanValue']
    OpportunityProductID: Optional['IntValue']
    ProjectTask: Optional['StringValue']
    Qty: Optional['DecimalValue']
    Subitem: Optional['StringValue']
    TaxCategory: Optional['StringValue']
    TransactionDescription: Optional['StringValue']
    UnitPrice: Optional['DecimalValue']
    UOM: Optional['StringValue']
    Warehouse: Optional['StringValue']
    SkipLineDiscounts: Optional['BooleanValue']


@dataclass
class OpportunityTaxDetail(BaseDataClassModel):
    IncludeInVATExemptTotal: Optional['BooleanValue']
    LineNbr: Optional['IntValue']
    PendingVAT: Optional['BooleanValue']
    ReverseVAT: Optional['BooleanValue']
    StatisticalVAT: Optional['BooleanValue']
    TaxableAmount: Optional['DecimalValue']
    TaxAmount: Optional['DecimalValue']
    TaxID: Optional['StringValue']
    TaxRate: Optional['DecimalValue']
    TaxType: Optional['StringValue']


@dataclass
class OrderRisks(BaseDataClassModel):
    Message: Optional['StringValue']
    Recommendation: Optional['StringValue']
    Score: Optional['DecimalValue']


@dataclass
class PTOBank(BaseDataClassModel):
    AccrualMethod: Optional['StringValue']
    AccrueonCertifiedJobOnly: Optional['BooleanValue']
    Active: Optional['BooleanValue']
    ApplyBandingRules: Optional['BooleanValue']
    BandingRules: Optional['PTOBankBandingRule']
    CarryoverType: Optional['StringValue']
    CreateFinTransactions: Optional['BooleanValue']
    DefaultDisbursingType: Optional['StringValue']
    Description: Optional['StringValue']
    DisbursingEarningType: Optional['StringValue']
    EmployeeClassSettings: List[Optional['PTOBankEmployeeClassSetting']]
    GLAccounts: Optional['PTOBankGLAccounts']
    LastModifiedDateTime: Optional['DateTimeValue']
    OnSettlement: Optional['StringValue']
    PTOBankID: Optional['StringValue']
    TransferDate: Optional['DateTimeValue']
    TransferDateDay: Optional['IntValue']
    TransferDateMonth: Optional['StringValue']
    TransferDateType: Optional['StringValue']


@dataclass
class PTOBankBandingRule(BaseDataClassModel):
    BandingRuleDetails: List[Optional['PTOBankBandingRuleDetail']]
    RoundingMethodforYearsofService: Optional['StringValue']


@dataclass
class PTOBankBandingRuleDetail(BaseDataClassModel):
    AccrualPercent: Optional['DecimalValue']
    BalanceLimit: Optional['DecimalValue']
    CarryoverHours: Optional['DecimalValue']
    EmployeeClass: Optional['StringValue']
    FrontLoadingHours: Optional['DecimalValue']
    HoursperYear: Optional['DecimalValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    YearsofService: Optional['IntValue']


@dataclass
class PTOBankCustomAction(BaseDataClassModel):
    entity: Optional['PTOBank']
    parameters: Optional[Any]


@dataclass
class PTOBankEmployeeClassSetting(BaseDataClassModel):
    AccrualPercent: Optional['DecimalValue']
    Active: Optional['BooleanValue']
    AllowNegativeBalance: Optional['BooleanValue']
    BalanceLimit: Optional['DecimalValue']
    CarryoverHours: Optional['DecimalValue']
    DisburseOnlyfromCarryover: Optional['BooleanValue']
    EffectiveDate: Optional['DateTimeValue']
    EmployeeClass: Optional['StringValue']
    FrontLoadingHours: Optional['DecimalValue']
    HoursperYear: Optional['DecimalValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    ProbationPeriodBehaviour: Optional['StringValue']


@dataclass
class PTOBankGLAccounts(BaseDataClassModel):
    AssetAccount: Optional['StringValue']
    AssetSub: Optional['StringValue']
    ExpenseAccount: Optional['StringValue']
    ExpenseSub: Optional['StringValue']
    LiabilityAccount: Optional['StringValue']
    LiabilitySub: Optional['StringValue']


@dataclass
class PauseAppointment(BaseDataClassModel):
    entity: Optional['Appointment']


@dataclass
class PayGroup(BaseDataClassModel):
    BenefitExpenseAccount: Optional['StringValue']
    BenefitExpenseSub: Optional['StringValue']
    BenefitLiabilityAccount: Optional['StringValue']
    BenefitLiabilitySub: Optional['StringValue']
    DeductionLiabilityAccount: Optional['StringValue']
    DeductionLiabilitySub: Optional['StringValue']
    EarningsAccount: Optional['StringValue']
    EarningsSub: Optional['StringValue']
    IsDefault: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    PayGroupID: Optional['StringValue']
    PayGroupName: Optional['StringValue']
    PTOAssetAccount: Optional['StringValue']
    PTOAssetSub: Optional['StringValue']
    PTOExpenseAccount: Optional['StringValue']
    PTOExpenseSub: Optional['StringValue']
    PTOLiabilityAccount: Optional['StringValue']
    PTOLiabilitySub: Optional['StringValue']
    TaxExpenseAccount: Optional['StringValue']
    TaxExpenseSub: Optional['StringValue']
    TaxLiabilityAccount: Optional['StringValue']
    TaxLiabilitySub: Optional['StringValue']
    UserRole: Optional['StringValue']


@dataclass
class PayGroupCustomAction(BaseDataClassModel):
    entity: Optional['PayGroup']
    parameters: Optional[Any]


@dataclass
class PayPeriod(BaseDataClassModel):
    LastModifiedDateTime: Optional['DateTimeValue']
    NumberofPeriods: Optional['ShortValue']
    Override: Optional['BooleanValue']
    PayGroup: Optional['StringValue']
    PaymentPeriods: List[Optional['PaymentPeriod']]
    StartDate: Optional['DateTimeValue']
    Year: Optional['StringValue']


@dataclass
class PayPeriodCustomAction(BaseDataClassModel):
    entity: Optional['PayPeriod']
    parameters: Optional[Any]


@dataclass
class Payment(BaseDataClassModel):
    ApplicationDate: Optional['DateTimeValue']
    ApplicationHistory: List[Optional['PaymentApplicationHistoryDetail']]
    AppliedToDocuments: Optional['DecimalValue']
    Branch: Optional['StringValue']
    CardAccountNbr: Optional['IntValue']
    CashAccount: Optional['StringValue']
    Charges: List[Optional['PaymentCharge']]
    CreditCardProcessingInfo: List[Optional['CreditCardProcessingDetail']]
    CurrencyID: Optional['StringValue']
    CustomerID: Optional['StringValue']
    Description: Optional['StringValue']
    DocumentsToApply: List[Optional['PaymentDetail']]
    Hold: Optional['BooleanValue']
    IsCCPayment: Optional['BooleanValue']
    OrdersToApply: List[Optional['PaymentOrderDetail']]
    PaymentAmount: Optional['DecimalValue']
    PaymentMethod: Optional['StringValue']
    PaymentRef: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    Status: Optional['StringValue']
    Type: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    ProcessingCenterID: Optional['StringValue']
    SaveCard: Optional['BooleanValue']
    CreditCardTransactionInfo: List[Optional['CreditCardTransactionDetail']]
    ExternalRef: Optional['StringValue']
    OrigTransaction: Optional['StringValue']
    BranchID: Optional['StringValue']
    CustomerLocationID: Optional['StringValue']
    IsNewCard: Optional['BooleanValue']
    NoteID: Optional['GuidValue']
    AvailableBalance: Optional['DecimalValue']
    AppliedToOrders: Optional['DecimalValue']


@dataclass
class PaymentApplicationHistoryDetail(BaseDataClassModel):
    AdjustedDocType: Optional['StringValue']
    AdjustedRefNbr: Optional['StringValue']
    AdjustingDocType: Optional['StringValue']
    AdjustingRefNbr: Optional['StringValue']
    AdjustmentNbr: Optional['IntValue']
    AdjustsVAT: Optional['BooleanValue']
    AmountPaid: Optional['DecimalValue']
    ApplicationPeriod: Optional['StringValue']
    Balance: Optional['DecimalValue']
    BalanceWriteOff: Optional['DecimalValue']
    BatchNbr: Optional['StringValue']
    CashDiscountBalance: Optional['DecimalValue']
    CashDiscountDate: Optional['DateTimeValue']
    CashDiscountTaken: Optional['DecimalValue']
    CurrencyID: Optional['StringValue']
    Customer: Optional['StringValue']
    CustomerOrder: Optional['StringValue']
    Date: Optional['DateTimeValue']
    Description: Optional['StringValue']
    DisplayDocType: Optional['StringValue']
    DisplayRefNbr: Optional['StringValue']
    DueDate: Optional['DateTimeValue']
    PostPeriod: Optional['StringValue']
    VATCreditMemo: Optional['StringValue']


@dataclass
class PaymentCharge(BaseDataClassModel):
    AccountID: Optional['StringValue']
    Amount: Optional['DecimalValue']
    Description: Optional['StringValue']
    DocType: Optional['StringValue']
    EntryTypeID: Optional['StringValue']
    LineNbr: Optional['IntValue']
    RefNbr: Optional['StringValue']
    SubID: Optional['StringValue']


@dataclass
class PaymentCustomAction(BaseDataClassModel):
    entity: Optional['Payment']
    parameters: Optional[Any]


@dataclass
class PaymentDetail(BaseDataClassModel):
    AmountPaid: Optional['DecimalValue']
    BalanceWriteOff: Optional['DecimalValue']
    CashDiscountTaken: Optional['DecimalValue']
    CustomerOrder: Optional['StringValue']
    Description: Optional['StringValue']
    DocLineNbr: Optional['IntValue']
    DocType: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    WriteOffReasonCode: Optional['StringValue']


@dataclass
class PaymentMethod(BaseDataClassModel):
    Active: Optional['BooleanValue']
    AllowedCashAccounts: List[Optional['PaymentMethodAllowedCashAccountDetail']]
    CreatedDateTime: Optional['DateTimeValue']
    Description: Optional['StringValue']
    IntegratedProcessing: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    MeansOfPayment: Optional['StringValue']
    PaymentMethodID: Optional['StringValue']
    ProcessingCenters: List[Optional['PaymentMethodProcessingCenterDetail']]
    RequireRemittanceInformationforCashAccount: Optional['BooleanValue']
    UseInAP: Optional['BooleanValue']
    UseInAR: Optional['BooleanValue']
    UseInPR: Optional['BooleanValue']
    SetPaymentDatetoBankTransactionDate: Optional['BooleanValue']
    SettingsForPR: Optional['SettingsForPR']


@dataclass
class PaymentMethodAllowedCashAccountDetail(BaseDataClassModel):
    APDefault: Optional['BooleanValue']
    APLastRefNbr: Optional['StringValue']
    APSuggestNextNbr: Optional['BooleanValue']
    ARDefault: Optional['BooleanValue']
    ARDefaultForRefund: Optional['BooleanValue']
    ARLastRefNbr: Optional['StringValue']
    ARSuggestNextNbr: Optional['BooleanValue']
    BatchLastRefNbr: Optional['StringValue']
    Branch: Optional['StringValue']
    CashAccount: Optional['StringValue']
    Description: Optional['StringValue']
    PaymentMethod: Optional['StringValue']
    UseInAP: Optional['BooleanValue']
    UseInAR: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    UseInPR: Optional['BooleanValue']


@dataclass
class PaymentMethodCustomAction(BaseDataClassModel):
    entity: Optional['PaymentMethod']
    parameters: Optional[Any]


@dataclass
class PaymentMethodProcessingCenterDetail(BaseDataClassModel):
    Active: Optional['BooleanValue']
    Default: Optional['BooleanValue']
    PaymentMethod: Optional['StringValue']
    ProcCenterID: Optional['StringValue']


@dataclass
class PaymentOrderDetail(BaseDataClassModel):
    AppliedToOrder: Optional['DecimalValue']
    OrderNbr: Optional['StringValue']
    OrderType: Optional['StringValue']


@dataclass
class PaymentPeriod(BaseDataClassModel):
    Description: Optional['StringValue']
    EndDate: Optional['DateTimeValue']
    FinYear: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    PayPeriodID: Optional['StringValue']
    PeriodNbr: Optional['StringValue']
    StartDate: Optional['DateTimeValue']
    TransactionDate: Optional['DateTimeValue']


@dataclass
class PayrollBatch(BaseDataClassModel):
    BatchID: Optional['StringValue']
    DeductionsAndBenefitsDetails: List[Optional['BatchDeductionOrBenefitDetail']]
    Description: Optional['StringValue']
    EarningDetails: List[Optional['BatchEarningDetail']]
    EmployeeSummary: List[Optional['EmployeePaycheckSummary']]
    Hold: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    NumberofEmployees: Optional['IntValue']
    OvertimeRules: Optional['BatchOvertimeRules']
    PayGroup: Optional['StringValue']
    PayPeriod: Optional['StringValue']
    TotalEarnings: Optional['DecimalValue']
    TotalHourQty: Optional['DecimalValue']
    PayrollType: Optional['StringValue']
    PeriodEnd: Optional['DateTimeValue']
    PeriodStart: Optional['DateTimeValue']
    Status: Optional['StringValue']
    TransactionDate: Optional['DateTimeValue']


@dataclass
class PayrollBatchCustomAction(BaseDataClassModel):
    entity: Optional['PayrollBatch']
    parameters: Optional[Any]


@dataclass
class PayrollUnionLocal(BaseDataClassModel):
    Active: Optional['BooleanValue']
    DeductionsAndBenefits: List[Optional['UnionDeductionOrBenefitDetail']]
    Description: Optional['StringValue']
    EarningRates: List[Optional['UnionEarningRateDetail']]
    LastModifiedDateTime: Optional['DateTimeValue']
    Location: Optional['StringValue']
    PayrollUnionLocalID: Optional['StringValue']
    Vendor: Optional['StringValue']


@dataclass
class PayrollUnionLocalCustomAction(BaseDataClassModel):
    entity: Optional['PayrollUnionLocal']
    parameters: Optional[Any]


@dataclass
class PayrollWCCCode(BaseDataClassModel):
    Country: Optional['StringValue']
    WCCCodes: List[Optional['WCCCode']]


@dataclass
class PayrollWCCCodeCustomAction(BaseDataClassModel):
    entity: Optional['PayrollWCCCode']
    parameters: Optional[Any]


@dataclass
class PhysicalInventoryCount(BaseDataClassModel):
    Details: List[Optional['PhysicalInventoryCountDetail']]
    InventoryID: Optional['StringValue']
    Location: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    Subitem: Optional['StringValue']


@dataclass
class PhysicalInventoryCountCustomAction(BaseDataClassModel):
    entity: Optional['PhysicalInventoryCount']
    parameters: Optional[Any]


@dataclass
class PhysicalInventoryCountDetail(BaseDataClassModel):
    BookQty: Optional['DecimalValue']
    Description: Optional['StringValue']
    InventoryID: Optional['StringValue']
    LineNbr: Optional['IntValue']
    Location: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    PhysicalQty: Optional['DecimalValue']
    ReferenceNbr: Optional['StringValue']
    Subitem: Optional['StringValue']


@dataclass
class PhysicalInventoryReview(BaseDataClassModel):
    CreatedDateTime: Optional['DateTimeValue']
    Description: Optional['StringValue']
    Details: List[Optional['PhysicalInventoryReviewDetail']]
    FreezeDate: Optional['DateTimeValue']
    ReferenceNbr: Optional['StringValue']
    Status: Optional['StringValue']
    TotalPhysicalQty: Optional['DecimalValue']
    TotalVarianceCost: Optional['DecimalValue']
    TotalVarianceQty: Optional['DecimalValue']
    TypeID: Optional['StringValue']
    WarehouseID: Optional['StringValue']


@dataclass
class PhysicalInventoryReviewCustomAction(BaseDataClassModel):
    entity: Optional['PhysicalInventoryReview']
    parameters: Optional[Any]


@dataclass
class PhysicalInventoryReviewDetail(BaseDataClassModel):
    BookQty: Optional['DecimalValue']
    Description: Optional['StringValue']
    ExpirationDate: Optional['DateTimeValue']
    ExtendedVarianceCost: Optional['DecimalValue']
    InventoryID: Optional['StringValue']
    LineNbr: Optional['IntValue']
    LocationID: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    PhysicalQty: Optional['DecimalValue']
    ReasonCode: Optional['StringValue']
    Status: Optional['StringValue']
    Subitem: Optional['StringValue']
    TagNbr: Optional['IntValue']
    UnitCost: Optional['DecimalValue']
    VarianceQty: Optional['DecimalValue']


@dataclass
class PrepareInvoice(BaseDataClassModel):
    entity: Optional['Shipment']


@dataclass
class PrepareSalesInvoice(BaseDataClassModel):
    entity: Optional['SalesOrder']


@dataclass
class ProFormaFinancialDetails(BaseDataClassModel):
    ARDocType: Optional['StringValue']
    ARRefNbr: Optional['StringValue']
    Branch: Optional['StringValue']
    CashDiscountDate: Optional['DateTimeValue']
    CustomerTaxZone: Optional['StringValue']
    CustomerUsageType: Optional['StringValue']
    DueDate: Optional['DateTimeValue']
    Terms: Optional['StringValue']


@dataclass
class ProFormaInvoice(BaseDataClassModel):
    AmountDue: Optional['DecimalValue']
    ApprovalDetails: List[Optional['Approval']]
    BillingSettings: Optional['BillToSettings']
    CurrencyID: Optional['StringValue']
    CustomerID: Optional['StringValue']
    Description: Optional['StringValue']
    EffectiveDate: Optional['DateTimeValue']
    ExternalRefNbr: Optional['StringValue']
    FinancialDetails: Optional['ProFormaFinancialDetails']
    Hold: Optional['BooleanValue']
    InvoiceDate: Optional['DateTimeValue']
    InvoiceTotal: Optional['DecimalValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Location: Optional['StringValue']
    PostPeriod: Optional['StringValue']
    ProgressBilling: List[Optional['ProgressBilling']]
    ProgressBillingTotal: Optional['DecimalValue']
    ProjectID: Optional['StringValue']
    RefNbr: Optional['StringValue']
    RetainageTotal: Optional['DecimalValue']
    Status: Optional['StringValue']
    TaxDetails: List[Optional['ProFormaTaxDetail']]
    TaxTotal: Optional['DecimalValue']
    TimeAndMaterial: List[Optional['TimeAndMaterial']]
    TimeAndMaterialTotal: Optional['DecimalValue']


@dataclass
class ProFormaInvoiceCustomAction(BaseDataClassModel):
    entity: Optional['ProFormaInvoice']
    parameters: Optional[Any]


@dataclass
class ProFormaTaxDetail(BaseDataClassModel):
    RetainedTax: Optional['DecimalValue']
    RetainedTaxable: Optional['DecimalValue']
    TaxableAmount: Optional['DecimalValue']
    TaxAmount: Optional['DecimalValue']
    TaxID: Optional['StringValue']
    TaxRate: Optional['DecimalValue']


@dataclass
class ProcessAllEmailProcessing(BaseDataClassModel):
    entity: Optional['EmailProcessing']


@dataclass
class ProcessEmail(BaseDataClassModel):
    entity: Optional['Email']


@dataclass
class ProcessEmailProcessing(BaseDataClassModel):
    entity: Optional['EmailProcessing']


@dataclass
class ProgressBilling(BaseDataClassModel):
    ActualAmount: Optional['DecimalValue']
    Amount: Optional['DecimalValue']
    AmountToInvoice: Optional['DecimalValue']
    Branch: Optional['StringValue']
    CostCode: Optional['StringValue']
    CurrentInvoiced: Optional['DecimalValue']
    DeferralCode: Optional['StringValue']
    Description: Optional['StringValue']
    DraftInvoicesAmount: Optional['DecimalValue']
    InventoryID: Optional['StringValue']
    PreviouslyInvoiced: Optional['DecimalValue']
    ProjectTaskID: Optional['StringValue']
    Retainage: Optional['DecimalValue']
    RetainageAmount: Optional['DecimalValue']
    RevisedBudgetedAmount: Optional['DecimalValue']
    SalesAccount: Optional['StringValue']
    SalesSubaccount: Optional['StringValue']
    StoredMaterial: Optional['DecimalValue']
    TaxCategory: Optional['StringValue']
    TotalCompleted: Optional['DecimalValue']


@dataclass
class Project(BaseDataClassModel):
    ActivityHistory: List[Optional['ProjectActivity']]
    ApprovalDetails: List[Optional['Approval']]
    Assets: Optional['DecimalValue']
    Attributes: List[Optional['AttributeValue']]
    Balances: List[Optional['ProjectBalance']]
    BillingAndAllocationSettings: Optional['ProjectBillingAndAllocationSettings']
    BillToSettings: Optional['BillToSettings']
    Customer: Optional['StringValue']
    Description: Optional['StringValue']
    Employees: List[Optional['ProjectEmployee']]
    Equipments: List[Optional['ProjectEquipment']]
    Expenses: Optional['DecimalValue']
    ExternalRefNbr: Optional['StringValue']
    GLAccounts: Optional['ProjectGLAccount']
    Hold: Optional['BooleanValue']
    Income: Optional['DecimalValue']
    Invoices: List[Optional['ProjectProFormaDetails']]
    LastModifiedDateTime: Optional['DateTimeValue']
    Liabilities: Optional['DecimalValue']
    ProjectID: Optional['StringValue']
    ProjectProperties: Optional['ProjectProperties']
    ProjectTemplateID: Optional['StringValue']
    Status: Optional['StringValue']
    UnionLocals: List[Optional['ProjectUnionLocal']]
    VisibilitySettings: Optional['VisibilitySettings']
    Retainage: Optional['ProjectRetainage']
    ProjectAddress: Optional['ProjectAddress']


@dataclass
class ProjectActivity(BaseDataClassModel):
    Billable: Optional['BooleanValue']
    BillableOvertime: Optional['StringValue']
    BillableTime: Optional['StringValue']
    Category: Optional['StringValue']
    Overtime: Optional['StringValue']
    Owner: Optional['StringValue']
    StartDate: Optional['DateTimeValue']
    Status: Optional['StringValue']
    Summary: Optional['StringValue']
    TimeSpent: Optional['StringValue']
    Type: Optional['StringValue']
    Workgroup: Optional['StringValue']


@dataclass
class ProjectAddress(BaseDataClassModel):
    AddressLine1: Optional['StringValue']
    City: Optional['StringValue']
    Country: Optional['StringValue']
    State: Optional['StringValue']
    PostalCode: Optional['StringValue']
    Latitude: Optional['DecimalValue']
    Longitude: Optional['DecimalValue']


@dataclass
class ProjectBalance(BaseDataClassModel):
    AccountGroup: Optional['StringValue']
    ActualAmount: Optional['DecimalValue']
    ActualOpenCommittedAmount: Optional['DecimalValue']
    BudgetedCOAmount: Optional['DecimalValue']
    CommittedCOAmount: Optional['DecimalValue']
    CommittedInvoicedAmount: Optional['DecimalValue']
    CommittedOpenAmount: Optional['DecimalValue']
    Description: Optional['StringValue']
    OriginalBudgetedAmount: Optional['DecimalValue']
    OriginalCommittedAmount: Optional['DecimalValue']
    Performance: Optional['DecimalValue']
    RevisedBudgetedAmount: Optional['DecimalValue']
    RevisedCommittedAmount: Optional['DecimalValue']
    VarianceAmount: Optional['DecimalValue']


@dataclass
class ProjectBillingAndAllocationSettings(BaseDataClassModel):
    AllocationRule: Optional['StringValue']
    AutomaticallyReleaseARDocuments: Optional['BooleanValue']
    BillingPeriod: Optional['StringValue']
    BillingRule: Optional['StringValue']
    Branch: Optional['StringValue']
    CreateProFormaOnBilling: Optional['BooleanValue']
    LastBillingDate: Optional['DateTimeValue']
    NextBillingDate: Optional['DateTimeValue']
    RateTable: Optional['StringValue']
    RunAllocationOnReleaseOfProjectTransactions: Optional['BooleanValue']
    Terms: Optional['StringValue']
    UseTMRevenueBudgetLimits: Optional['BooleanValue']
    BillingCurrency: Optional['StringValue']


@dataclass
class ProjectBudget(BaseDataClassModel):
    AccountGroup: Optional['StringValue']
    ActualAmount: Optional['DecimalValue']
    ActualPlusOpenCommittedAmount: Optional['DecimalValue']
    ActualQty: Optional['DecimalValue']
    AutoCompleted: Optional['BooleanValue']
    BudgetedCOAmount: Optional['DecimalValue']
    BudgetedCOQty: Optional['DecimalValue']
    CommittedCOAmount: Optional['DecimalValue']
    CommittedCOQty: Optional['DecimalValue']
    CommittedInvoicedAmount: Optional['DecimalValue']
    CommittedInvoicedQty: Optional['DecimalValue']
    CommittedOpenAmount: Optional['DecimalValue']
    CommittedOpenQty: Optional['DecimalValue']
    CommittedReceivedQty: Optional['DecimalValue']
    Completed: Optional['DecimalValue']
    CostAtCompletion: Optional['DecimalValue']
    CostCode: Optional['StringValue']
    CostToComplete: Optional['DecimalValue']
    Description: Optional['StringValue']
    DraftInvoicesAmount: Optional['DecimalValue']
    InventoryID: Optional['StringValue']
    LastCostAtCompletion: Optional['DecimalValue']
    LastCostToComplete: Optional['DecimalValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    LastPercentageOfCompletion: Optional['DecimalValue']
    OriginalBudgetedAmount: Optional['DecimalValue']
    OriginalBudgetedQty: Optional['DecimalValue']
    OriginalCommittedAmount: Optional['DecimalValue']
    OriginalCommittedQty: Optional['DecimalValue']
    PendingInvoiceAmount: Optional['DecimalValue']
    PercentageOfCompletion: Optional['DecimalValue']
    Performance: Optional['DecimalValue']
    ProjectID: Optional['StringValue']
    ProjectTaskID: Optional['StringValue']
    Retainage: Optional['DecimalValue']
    RevenueTask: Optional['IntValue']
    RevisedBudgetedAmount: Optional['DecimalValue']
    RevisedBudgetedQty: Optional['DecimalValue']
    RevisedCommittedAmount: Optional['DecimalValue']
    RevisedCommittedQty: Optional['DecimalValue']
    TaxCategory: Optional['StringValue']
    Type: Optional['StringValue']
    UnitRate: Optional['DecimalValue']
    UOM: Optional['StringValue']
    VarianceAmount: Optional['DecimalValue']


@dataclass
class ProjectBudgetCustomAction(BaseDataClassModel):
    entity: Optional['ProjectBudget']
    parameters: Optional[Any]


@dataclass
class ProjectCustomAction(BaseDataClassModel):
    entity: Optional['Project']
    parameters: Optional[Any]


@dataclass
class ProjectEmployee(BaseDataClassModel):
    Department: Optional['StringValue']
    EmployeeID: Optional['StringValue']
    EmployeeName: Optional['StringValue']


@dataclass
class ProjectEquipment(BaseDataClassModel):
    Active: Optional['BooleanValue']
    Description: Optional['StringValue']
    EquipmentID: Optional['StringValue']
    RunRate: Optional['DecimalValue']
    RunRateItem: Optional['StringValue']
    SetupRate: Optional['DecimalValue']
    SetupRateItem: Optional['StringValue']
    SuspendRate: Optional['DecimalValue']
    SuspendRateItem: Optional['StringValue']


@dataclass
class ProjectGLAccount(BaseDataClassModel):
    AccrualAccount: Optional['StringValue']
    AccrualSubaccount: Optional['StringValue']
    DefaultAccount: Optional['StringValue']
    DefaultSubaccount: Optional['StringValue']
    DefaultCostAccount: Optional['StringValue']
    DefaultCostSubaccount: Optional['StringValue']
    DefaultTaskForGLAccounts: List[Optional['DefaultTaskForGLAccount']]


@dataclass
class ProjectProFormaDetails(BaseDataClassModel):
    ARDocDate: Optional['DateTimeValue']
    ARDocDescription: Optional['StringValue']
    ARDocOriginalAmount: Optional['DecimalValue']
    ARDocStatus: Optional['StringValue']
    ARDocType: Optional['StringValue']
    ARReferenceNbr: Optional['StringValue']
    BillingNbr: Optional['IntValue']
    Description: Optional['StringValue']
    InvoiceTotal: Optional['DecimalValue']
    OpenARBalance: Optional['DecimalValue']
    OriginalRefNbr: Optional['StringValue']
    OriginalRetainage: Optional['DecimalValue']
    PaidRetainage: Optional['DecimalValue']
    ProFormaDate: Optional['DateTimeValue']
    ProFormaReferenceNbr: Optional['StringValue']
    RetainageInvoice: Optional['BooleanValue']
    Status: Optional['StringValue']
    TotalAmount: Optional['DecimalValue']
    UnpaidRetainage: Optional['DecimalValue']
    UnreleasedRetainage: Optional['DecimalValue']


@dataclass
class ProjectProperties(BaseDataClassModel):
    CertifiedJob: Optional['BooleanValue']
    ChangeOrderWorkflow: Optional['BooleanValue']
    EndDate: Optional['DateTimeValue']
    LastRevenueChangeNbr: Optional['StringValue']
    ProjectManager: Optional['StringValue']
    RestrictEmployees: Optional['BooleanValue']
    RestrictEquipment: Optional['BooleanValue']
    RevenueBudgetLevel: Optional['StringValue']
    StartDate: Optional['DateTimeValue']
    TrackProductionData: Optional['BooleanValue']
    CostBudgetLevel: Optional['StringValue']
    TimeActivityApprover: Optional['StringValue']
    ProjectCurrency: Optional['StringValue']
    RateType: Optional['StringValue']
    InventoryTrackingMode: Optional['StringValue']
    CostTaxZone: Optional['StringValue']
    RevenueTaxZone: Optional['StringValue']


@dataclass
class ProjectRetainage(BaseDataClassModel):
    RetainageMode: Optional['StringValue']
    IncludeCO: Optional['BooleanValue']
    UseSteps: Optional['BooleanValue']
    CapPct: Optional['DecimalValue']
    CapAmount: Optional['DecimalValue']
    RetainagePct: Optional['DecimalValue']
    RetainTotal: Optional['DecimalValue']
    ContractTotal: Optional['DecimalValue']
    CompletedPct: Optional['DecimalValue']


@dataclass
class ProjectTask(BaseDataClassModel):
    ActivityHistory: List[Optional['ProjectActivity']]
    Attributes: List[Optional['AttributeValue']]
    BillingAndAllocationSettings: Optional['ProjectTaskBillingAndAllocationSettings']
    CRMLink: Optional['ProjectTaskToCRMLink']
    Default: Optional['BooleanValue']
    DefaultValues: Optional['ProjectTaskDefaultValues']
    Description: Optional['StringValue']
    ExternalRefNbr: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    ProjectID: Optional['StringValue']
    ProjectTaskID: Optional['StringValue']
    Properties: Optional['ProjectTaskProperties']
    Status: Optional['StringValue']
    VisibilitySettings: Optional['VisibilitySettings']


@dataclass
class ProjectTaskBillingAndAllocationSettings(BaseDataClassModel):
    AllocationRule: Optional['StringValue']
    BillingOption: Optional['StringValue']
    BillingRule: Optional['StringValue']
    BillSeparately: Optional['BooleanValue']
    Branch: Optional['StringValue']
    Customer: Optional['StringValue']
    Location: Optional['StringValue']
    RateTable: Optional['StringValue']
    WIPAccountGroup: Optional['StringValue']


@dataclass
class ProjectTaskCustomAction(BaseDataClassModel):
    entity: Optional['ProjectTask']
    parameters: Optional[Any]


@dataclass
class ProjectTaskDefaultValues(BaseDataClassModel):
    AccrualAccount: Optional['StringValue']
    AccrualSubaccount: Optional['StringValue']
    DefaultAccount: Optional['StringValue']
    DefaultSubaccount: Optional['StringValue']
    DefaultCostAccount: Optional['StringValue']
    DefaultCostSubaccount: Optional['StringValue']
    TaxCategory: Optional['StringValue']


@dataclass
class ProjectTaskProperties(BaseDataClassModel):
    Approver: Optional['StringValue']
    Completed: Optional['DecimalValue']
    CompletionMethod: Optional['StringValue']
    EndDate: Optional['DateTimeValue']
    PlannedEndDate: Optional['DateTimeValue']
    PlannedStartDate: Optional['DateTimeValue']
    StartDate: Optional['DateTimeValue']


@dataclass
class ProjectTaskToCRMLink(BaseDataClassModel):
    AccountedCampaign: Optional['StringValue']


@dataclass
class ProjectTemplate(BaseDataClassModel):
    Attributes: List[Optional['AttributeValue']]
    BillingAndAllocationSettings: Optional['ProjectBillingAndAllocationSettings']
    Description: Optional['StringValue']
    Employees: List[Optional['ProjectEmployee']]
    Equipments: List[Optional['ProjectEquipment']]
    GLAccounts: Optional['ProjectGLAccount']
    LastModifiedDateTime: Optional['DateTimeValue']
    ProjectProperties: Optional['ProjectProperties']
    ProjectTemplateID: Optional['StringValue']
    Status: Optional['StringValue']
    VisibilitySettings: Optional['VisibilitySettings']


@dataclass
class ProjectTemplateCustomAction(BaseDataClassModel):
    entity: Optional['ProjectTemplate']
    parameters: Optional[Any]


@dataclass
class ProjectTemplateTask(BaseDataClassModel):
    Attributes: List[Optional['AttributeValue']]
    BillingAndAllocationSettings: Optional['ProjectTaskBillingAndAllocationSettings']
    DefaultValues: Optional['ProjectTaskDefaultValues']
    Description: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    ProjectTemplateID: Optional['StringValue']
    ProjectTemplateTaskID: Optional['StringValue']
    Properties: Optional['ProjectTemplateTaskProperties']
    VisibilitySettings: Optional['VisibilitySettings']


@dataclass
class ProjectTemplateTaskCustomAction(BaseDataClassModel):
    entity: Optional['ProjectTemplateTask']
    parameters: Optional[Any]


@dataclass
class ProjectTemplateTaskProperties(BaseDataClassModel):
    Approver: Optional['StringValue']
    AutomaticallyIncludeInProject: Optional['BooleanValue']
    CompletionMethod: Optional['StringValue']
    Default: Optional['BooleanValue']


@dataclass
class ProjectTransaction(BaseDataClassModel):
    CreatedDateTime: Optional['DateTimeValue']
    Description: Optional['StringValue']
    Details: List[Optional['ProjectTransactionDetail']]
    LastModifiedDateTime: Optional['DateTimeValue']
    Module: Optional['StringValue']
    OriginalDocNbr: Optional['StringValue']
    OriginalDocType: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    Status: Optional['StringValue']
    TotalAmount: Optional['DecimalValue']
    TotalBillableQty: Optional['DecimalValue']
    TotalQty: Optional['DecimalValue']


@dataclass
class ProjectTransactionCustomAction(BaseDataClassModel):
    entity: Optional['ProjectTransaction']
    parameters: Optional[Any]


@dataclass
class ProjectTransactionDetail(BaseDataClassModel):
    AccountGroup: Optional['StringValue']
    AccountGroupDescription: Optional['StringValue']
    Allocated: Optional['BooleanValue']
    Amount: Optional['DecimalValue']
    BatchNbr: Optional['StringValue']
    Billable: Optional['BooleanValue']
    BillableQty: Optional['DecimalValue']
    Billed: Optional['BooleanValue']
    Branch: Optional['StringValue']
    CostCode: Optional['StringValue']
    CreditAccount: Optional['StringValue']
    CreditSubaccount: Optional['StringValue']
    Date: Optional['DateTimeValue']
    DebitAccount: Optional['StringValue']
    DebitSubaccount: Optional['StringValue']
    Description: Optional['StringValue']
    EarningType: Optional['StringValue']
    Employee: Optional['StringValue']
    EndDate: Optional['DateTimeValue']
    ExternalRefNbr: Optional['StringValue']
    FinPeriod: Optional['StringValue']
    InventoryID: Optional['StringValue']
    Location: Optional['StringValue']
    Multiplier: Optional['DecimalValue']
    Project: Optional['StringValue']
    ProjectTask: Optional['StringValue']
    Qty: Optional['DecimalValue']
    Released: Optional['BooleanValue']
    StartDate: Optional['DateTimeValue']
    TransactionID: Optional['LongValue']
    UnitRate: Optional['DecimalValue']
    UOM: Optional['StringValue']
    UseBillableQtyInAmountFormula: Optional['BooleanValue']
    VendorOrCustomer: Optional['StringValue']


@dataclass
class ProjectUnionLocal(BaseDataClassModel):
    Description: Optional['StringValue']
    UnionLocalID: Optional['StringValue']


@dataclass
class PurchaseOrder(BaseDataClassModel):
    BaseCurrencyID: Optional['StringValue']
    Branch: Optional['StringValue']
    ControlTotal: Optional['DecimalValue']
    CurrencyID: Optional['StringValue']
    CurrencyEffectiveDate: Optional['DateTimeValue']
    CurrencyRate: Optional['DecimalValue']
    CurrencyRateTypeID: Optional['StringValue']
    CurrencyReciprocalRate: Optional['DecimalValue']
    Date: Optional['DateTimeValue']
    Description: Optional['StringValue']
    Details: List[Optional['PurchaseOrderDetail']]
    Hold: Optional['BooleanValue']
    IsTaxValid: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    LineTotal: Optional['DecimalValue']
    Location: Optional['StringValue']
    OrderNbr: Optional['StringValue']
    OrderTotal: Optional['DecimalValue']
    Owner: Optional['StringValue']
    Project: Optional['StringValue']
    PromisedOn: Optional['DateTimeValue']
    ShippingInstructions: Optional['ShippingInstructions']
    Status: Optional['StringValue']
    TaxDetails: List[Optional['PurchaseOrderTaxDetail']]
    TaxTotal: Optional['DecimalValue']
    Terms: Optional['StringValue']
    Type: Optional['StringValue']
    VendorID: Optional['StringValue']
    VendorRef: Optional['StringValue']
    VendorTaxZone: Optional['StringValue']


@dataclass
class PurchaseOrderCustomAction(BaseDataClassModel):
    entity: Optional['PurchaseOrder']
    parameters: Optional[Any]


@dataclass
class PurchaseOrderDetail(BaseDataClassModel):
    Account: Optional['StringValue']
    AlternateID: Optional['StringValue']
    BranchID: Optional['StringValue']
    CalculateDiscountsOnImport: Optional['BooleanValue']
    Cancelled: Optional['BooleanValue']
    Completed: Optional['BooleanValue']
    CompleteOn: Optional['DecimalValue']
    CostCode: Optional['StringValue']
    Description: Optional['StringValue']
    ExtendedCost: Optional['DecimalValue']
    InventoryID: Optional['StringValue']
    LineDescription: Optional['StringValue']
    LineNbr: Optional['IntValue']
    LineType: Optional['StringValue']
    MaxReceiptPercent: Optional['DecimalValue']
    MinReceiptPercent: Optional['DecimalValue']
    OrderNbr: Optional['StringValue']
    OrderQty: Optional['DecimalValue']
    OrderedQty: Optional['DecimalValue']
    OrderType: Optional['StringValue']
    OrigPONbr: Optional['StringValue']
    OrigPOType: Optional['StringValue']
    Project: Optional['StringValue']
    ProjectTask: Optional['StringValue']
    Promised: Optional['DateTimeValue']
    QtyOnReceipts: Optional['DecimalValue']
    ReceiptAction: Optional['StringValue']
    ReceivedAmount: Optional['DecimalValue']
    Requested: Optional['DateTimeValue']
    Subaccount: Optional['StringValue']
    Subitem: Optional['StringValue']
    TaxCategory: Optional['StringValue']
    UnitCost: Optional['DecimalValue']
    UOM: Optional['StringValue']
    WarehouseID: Optional['StringValue']


@dataclass
class PurchaseOrderTaxDetail(BaseDataClassModel):
    RetainedTaxableAmount: Optional['DecimalValue']
    RetainedTaxAmount: Optional['DecimalValue']
    TaxableAmount: Optional['DecimalValue']
    TaxAmount: Optional['DecimalValue']
    TaxID: Optional['StringValue']
    TaxRate: Optional['DecimalValue']


@dataclass
class PurchaseReceipt(BaseDataClassModel):
    BaseCurrencyID: Optional['StringValue']
    BillDate: Optional['DateTimeValue']
    Branch: Optional['StringValue']
    ControlQty: Optional['DecimalValue']
    CreateBill: Optional['BooleanValue']
    CurrencyID: Optional['StringValue']
    CurrencyEffectiveDate: Optional['DateTimeValue']
    CurrencyRate: Optional['DecimalValue']
    CurrencyRateTypeID: Optional['StringValue']
    CurrencyReciprocalRate: Optional['DecimalValue']
    Date: Optional['DateTimeValue']
    Details: List[Optional['PurchaseReceiptDetail']]
    Hold: Optional['BooleanValue']
    InventoryRefNbr: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Location: Optional['StringValue']
    PostPeriod: Optional['StringValue']
    ProcessReturnWithOriginalCost: Optional['BooleanValue']
    ReceiptNbr: Optional['StringValue']
    Status: Optional['StringValue']
    TotalCost: Optional['DecimalValue']
    TotalQty: Optional['DecimalValue']
    Type: Optional['StringValue']
    UnbilledQuantity: Optional['DecimalValue']
    VendorID: Optional['StringValue']
    VendorRef: Optional['StringValue']
    Warehouse: Optional['StringValue']


@dataclass
class PurchaseReceiptCustomAction(BaseDataClassModel):
    entity: Optional['PurchaseReceipt']
    parameters: Optional[Any]


@dataclass
class PurchaseReceiptDetail(BaseDataClassModel):
    Account: Optional['StringValue']
    AccrualAccount: Optional['StringValue']
    AccrualSubaccount: Optional['StringValue']
    Allocations: List[Optional['PurchaseReceiptDetailAllocation']]
    Branch: Optional['StringValue']
    Description: Optional['StringValue']
    EditableUnitCost: Optional['BooleanValue']
    EstimatedINExtendedCost: Optional['DecimalValue']
    ExtendedCost: Optional['DecimalValue']
    ExpirationDate: Optional['DateTimeValue']
    FinalINExtendedCost: Optional['DecimalValue']
    InventoryID: Optional['StringValue']
    LineNbr: Optional['IntValue']
    LineType: Optional['StringValue']
    Location: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    OpenQty: Optional['DecimalValue']
    OrderedQty: Optional['DecimalValue']
    POLineNbr: Optional['IntValue']
    POOrderNbr: Optional['StringValue']
    POOrderType: Optional['StringValue']
    POReceiptLineNbr: Optional['IntValue']
    POReceiptNbr: Optional['StringValue']
    ReceiptQty: Optional['DecimalValue']
    Subaccount: Optional['StringValue']
    Subitem: Optional['StringValue']
    TransactionDescription: Optional['StringValue']
    TransferOrderNbr: Optional['StringValue']
    TransferOrderLineNbr: Optional['IntValue']
    TransferOrderType: Optional['StringValue']
    TransferShipmentNbr: Optional['StringValue']
    UnitCost: Optional['DecimalValue']
    UOM: Optional['StringValue']
    Warehouse: Optional['StringValue']


@dataclass
class PurchaseReceiptDetailAllocation(BaseDataClassModel):
    LineNbr: Optional['IntValue']
    Location: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    Qty: Optional['DecimalValue']
    ReceiptNbr: Optional['StringValue']
    SplitLineNbr: Optional['IntValue']
    ExpirationDate: Optional['DateTimeValue']


@dataclass
class PurchaseSettings(BaseDataClassModel):
    POSiteID: Optional['StringValue']
    POSource: Optional['StringValue']
    VendorID: Optional['StringValue']


@dataclass
class PurchasingDetail(BaseDataClassModel):
    POOrderLineNbr: Optional['IntValue']
    POOrderNbr: Optional['StringValue']
    POOrderType: Optional['StringValue']
    Selected: Optional['BooleanValue']


@dataclass
class PutOnHold(BaseDataClassModel):
    entity: Optional['Subcontract']


@dataclass
class PutOnHoldExpenseClaim(BaseDataClassModel):
    entity: Optional['ExpenseClaim']


@dataclass
class PutOnHoldExpenseReceipt(BaseDataClassModel):
    entity: Optional['ExpenseReceipt']


@dataclass
class RecalcExternalTax(BaseDataClassModel):
    entity: Optional['ServiceOrder']


@dataclass
class RecalculatePricesDiscounts(BaseDataClassModel):
    entity: Optional['SalesOrder']
    parameters: Optional[Any]


@dataclass
class RejectChangeOrder(BaseDataClassModel):
    entity: Optional['ChangeOrder']


@dataclass
class RejectExpenseClaim(BaseDataClassModel):
    entity: Optional['ExpenseClaim']


@dataclass
class RejectExpenseReceipt(BaseDataClassModel):
    entity: Optional['ExpenseReceipt']


@dataclass
class RejectInvitationEvent(BaseDataClassModel):
    entity: Optional['Event']


@dataclass
class RejectProFormaInvoice(BaseDataClassModel):
    entity: Optional['ProFormaInvoice']


@dataclass
class RejectProject(BaseDataClassModel):
    entity: Optional['Project']


@dataclass
class RelationDetail(BaseDataClassModel):
    Account: Optional['StringValue']
    AddToCc: Optional['BooleanValue']
    ContactDisplayName: Optional['StringValue']
    ContactID: Optional['IntValue']
    Document: Optional['GuidValue']
    DocumentTargetNoteIDDescription: Optional['StringValue']
    Email: Optional['StringValue']
    Name: Optional['StringValue']
    Primary: Optional['BooleanValue']
    RelationID: Optional['IntValue']
    Role: Optional['StringValue']
    Type: Optional['StringValue']
    DocumentDate: Optional['DateTimeValue']


@dataclass
class ReleaseAdjustment(BaseDataClassModel):
    entity: Optional['InventoryAdjustment']


@dataclass
class ReleaseBatch(BaseDataClassModel):
    entity: Optional['PayrollBatch']


@dataclass
class ReleaseBill(BaseDataClassModel):
    entity: Optional['Bill']


@dataclass
class ReleaseCase(BaseDataClassModel):
    entity: Optional['Case']


@dataclass
class ReleaseCashSale(BaseDataClassModel):
    entity: Optional['CashSale']


@dataclass
class ReleaseCashTransaction(BaseDataClassModel):
    entity: Optional['CashTransaction']


@dataclass
class ReleaseChangeOrder(BaseDataClassModel):
    entity: Optional['ChangeOrder']


@dataclass
class ReleaseCheck(BaseDataClassModel):
    entity: Optional['Check']


@dataclass
class ReleaseExpenseClaim(BaseDataClassModel):
    entity: Optional['ExpenseClaim']


@dataclass
class ReleaseFromCreditHoldSalesOrder(BaseDataClassModel):
    entity: Optional['SalesOrder']


@dataclass
class ReleaseFromHold(BaseDataClassModel):
    entity: Optional['Subcontract']


@dataclass
class ReleaseInventoryIssue(BaseDataClassModel):
    entity: Optional['InventoryIssue']


@dataclass
class ReleaseInventoryReceipt(BaseDataClassModel):
    entity: Optional['InventoryReceipt']


@dataclass
class ReleaseInvoice(BaseDataClassModel):
    entity: Optional['Invoice']


@dataclass
class ReleaseJournalTransaction(BaseDataClassModel):
    entity: Optional['JournalTransaction']


@dataclass
class ReleaseKitAssembly(BaseDataClassModel):
    entity: Optional['KitAssembly']


@dataclass
class ReleasePayment(BaseDataClassModel):
    entity: Optional['Payment']


@dataclass
class ReleaseProFormaInvoice(BaseDataClassModel):
    entity: Optional['ProFormaInvoice']


@dataclass
class ReleasePurchaseReceipt(BaseDataClassModel):
    entity: Optional['PurchaseReceipt']


@dataclass
class ReleaseRetainage(BaseDataClassModel):
    entity: Optional['Bill']
    parameters: Optional[Any]


@dataclass
class ReleaseSalesInvoice(BaseDataClassModel):
    entity: Optional['SalesInvoice']


@dataclass
class ReleaseSalesPriceWorksheet(BaseDataClassModel):
    entity: Optional['SalesPriceWorksheet']


@dataclass
class ReleaseTransactions(BaseDataClassModel):
    entity: Optional['ProjectTransaction']


@dataclass
class ReleaseTransferOrder(BaseDataClassModel):
    entity: Optional['TransferOrder']


@dataclass
class ReleaseVendorPriceWorksheet(BaseDataClassModel):
    entity: Optional['VendorPriceWorksheet']


@dataclass
class ReminderDetail(BaseDataClassModel):
    IsActive: Optional['BooleanValue']
    RemindAtDate: Optional['DateTimeValue']
    RemindAtTime: Optional['DateTimeValue']


@dataclass
class RemoveChangeOrderFromHold(BaseDataClassModel):
    entity: Optional['ChangeOrder']


@dataclass
class RemoveProFormaInvoiceFromHold(BaseDataClassModel):
    entity: Optional['ProFormaInvoice']


@dataclass
class ReopenAppointment(BaseDataClassModel):
    entity: Optional['Appointment']


@dataclass
class ReopenOrder(BaseDataClassModel):
    entity: Optional['ServiceOrder']


@dataclass
class ReopenSalesOrder(BaseDataClassModel):
    entity: Optional['SalesOrder']


@dataclass
class ReplenishmentParameterStockItem(BaseDataClassModel):
    DemandForecastModel: Optional['StringValue']
    ForecastPeriodType: Optional['StringValue']
    LaunchDate: Optional['DateTimeValue']
    MaxQty: Optional['DecimalValue']
    MaxShelfLifeInDays: Optional['IntValue']
    Method: Optional['StringValue']
    PeriodsToAnalyze: Optional['IntValue']
    ReorderPoint: Optional['DecimalValue']
    ReplenishmentClass: Optional['StringValue']
    ReplenishmentWarehouse: Optional['StringValue']
    SafetyStock: Optional['DecimalValue']
    Seasonality: Optional['StringValue']
    ServiceLevel: Optional['DecimalValue']
    Source: Optional['StringValue']
    TerminationDate: Optional['DateTimeValue']
    TransferERQ: Optional['DecimalValue']


@dataclass
class ReportingGroup(BaseDataClassModel):
    GroupType: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Name: Optional['StringValue']


@dataclass
class RestoreArchivedEmail(BaseDataClassModel):
    entity: Optional['Email']


@dataclass
class RestoreDeletedEmail(BaseDataClassModel):
    entity: Optional['Email']


@dataclass
class ResumeAppointment(BaseDataClassModel):
    entity: Optional['Appointment']


@dataclass
class ReverseBill(BaseDataClassModel):
    entity: Optional['Bill']


@dataclass
class ReverseChangeOrder(BaseDataClassModel):
    entity: Optional['ChangeOrder']


@dataclass
class RunProjectAllocation(BaseDataClassModel):
    entity: Optional['Project']


@dataclass
class RunProjectBilling(BaseDataClassModel):
    entity: Optional['Project']


@dataclass
class SalesInvoice(BaseDataClassModel):
    Amount: Optional['DecimalValue']
    ApplicationsCreditMemo: List[Optional['SalesInvoiceApplicationCreditMemo']]
    ApplicationsInvoice: List[Optional['SalesInvoiceApplicationInvoice']]
    Balance: Optional['DecimalValue']
    BillingSettings: Optional['BillToSettings']
    CashDiscount: Optional['DecimalValue']
    Commissions: Optional['SalesInvoiceCommissions']
    CreditHold: Optional['BooleanValue']
    Currency: Optional['StringValue']
    CustomerID: Optional['StringValue']
    CustomerOrder: Optional['StringValue']
    Date: Optional['DateTimeValue']
    Description: Optional['StringValue']
    Details: List[Optional['SalesInvoiceDetail']]
    DetailTotal: Optional['DecimalValue']
    DiscountDetails: List[Optional['SalesInvoiceDiscountDetails']]
    DiscountTotal: Optional['DecimalValue']
    DueDate: Optional['DateTimeValue']
    IsTaxValid: Optional['BooleanValue']
    FinancialDetails: Optional['SalesInvoiceFinancialDetails']
    FreightDetails: List[Optional['SalesInvoiceFreightDetail']]
    FreightPrice: Optional['DecimalValue']
    Hold: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    PaymentTotal: Optional['DecimalValue']
    Project: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    Status: Optional['StringValue']
    TaxDetails: List[Optional['SalesInvoiceTaxDetail']]
    TaxTotal: Optional['DecimalValue']
    Type: Optional['StringValue']
    VATExemptTotal: Optional['DecimalValue']
    VATTaxableTotal: Optional['DecimalValue']
    BillToAddress: Optional['SalesInvoiceAddress']
    BillToAddressOverride: Optional['BooleanValue']
    BillToContact: Optional['SalesInvoiceDocContact']
    BillToContactOverride: Optional['BooleanValue']
    CreatedDate: Optional['DateTimeValue']
    ExternalRef: Optional['StringValue']
    LastModifiedDate: Optional['DateTimeValue']
    ShipToAddress: Optional['SalesInvoiceAddress']
    ShipToAddressOverride: Optional['BooleanValue']
    ShipToContact: Optional['SalesInvoiceDocContact']
    ShipToContactOverride: Optional['BooleanValue']
    TaxCalcMode: Optional['StringValue']


@dataclass
class SalesInvoiceAddress(BaseDataClassModel):
    AddressLine1: Optional['StringValue']
    AddressLine2: Optional['StringValue']
    City: Optional['StringValue']
    Country: Optional['StringValue']
    PostalCode: Optional['StringValue']
    State: Optional['StringValue']


@dataclass
class SalesInvoiceApplicationCreditMemo(BaseDataClassModel):
    AmountPaid: Optional['DecimalValue']
    Balance: Optional['DecimalValue']
    Currency: Optional['StringValue']
    Customer: Optional['StringValue']
    CustomerOrder: Optional['StringValue']
    Date: Optional['DateTimeValue']
    Description: Optional['StringValue']
    DocType: Optional['StringValue']
    PostPeriod: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    Status: Optional['StringValue']


@dataclass
class SalesInvoiceApplicationInvoice(BaseDataClassModel):
    AdjustedDocReferenceNbr: Optional['StringValue']
    AdjustingDocReferenceNbr: Optional['StringValue']
    AdjustmentNbr: Optional['IntValue']
    AmountPaid: Optional['DecimalValue']
    Balance: Optional['DecimalValue']
    CashDiscountTaken: Optional['DecimalValue']
    Currency: Optional['StringValue']
    Customer: Optional['StringValue']
    Description: Optional['StringValue']
    DocType: Optional['StringValue']
    DocumentType: Optional['StringValue']
    PaymentDate: Optional['DateTimeValue']
    PaymentPeriod: Optional['StringValue']
    PaymentRef: Optional['StringValue']
    Status: Optional['StringValue']


@dataclass
class SalesInvoiceCommissions(BaseDataClassModel):
    CommissionAmount: Optional['DecimalValue']
    SalesPersons: List[Optional['SalesInvoiceSalesPersonDetail']]
    TotalCommissionableAmount: Optional['DecimalValue']


@dataclass
class SalesInvoiceCustomAction(BaseDataClassModel):
    entity: Optional['SalesInvoice']
    parameters: Optional[Any]


@dataclass
class SalesInvoiceDetail(BaseDataClassModel):
    Account: Optional['StringValue']
    Amount: Optional['DecimalValue']
    BranchID: Optional['StringValue']
    CalculateDiscountsOnImport: Optional['BooleanValue']
    CostCode: Optional['StringValue']
    Description: Optional['StringValue']
    DiscountAmount: Optional['DecimalValue']
    DiscountPercent: Optional['DecimalValue']
    ExpirationDate: Optional['DateTimeValue']
    ExternalRef: Optional['StringValue']
    InventoryDocType: Optional['StringValue']
    InventoryID: Optional['StringValue']
    InventoryRefNbr: Optional['StringValue']
    LineNbr: Optional['IntValue']
    Location: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    ManualDiscount: Optional['BooleanValue']
    ManualPrice: Optional['BooleanValue']
    NoteID: Optional['GuidValue']
    OrderLineNbr: Optional['IntValue']
    OrderNbr: Optional['StringValue']
    OrderType: Optional['StringValue']
    OrigInvLineNbr: Optional['IntValue']
    OrigInvNbr: Optional['StringValue']
    OrigInvType: Optional['StringValue']
    ProjectTask: Optional['StringValue']
    Qty: Optional['DecimalValue']
    ShipmentNbr: Optional['StringValue']
    SubAccount: Optional['StringValue']
    Subitem: Optional['StringValue']
    TaxCategory: Optional['StringValue']
    TransactionDescr: Optional['StringValue']
    UnitPrice: Optional['DecimalValue']
    UOM: Optional['StringValue']
    WarehouseID: Optional['StringValue']


@dataclass
class SalesInvoiceDiscountDetails(BaseDataClassModel):
    Description: Optional['StringValue']
    DiscountableAmount: Optional['DecimalValue']
    DiscountableQty: Optional['DecimalValue']
    DiscountAmount: Optional['DecimalValue']
    DiscountCode: Optional['StringValue']
    DiscountPercent: Optional['DecimalValue']
    ExternalDiscountCode: Optional['StringValue']
    FreeItem: Optional['StringValue']
    FreeItemQty: Optional['DecimalValue']
    ManualDiscount: Optional['BooleanValue']
    OrderNbr: Optional['StringValue']
    OrderType: Optional['StringValue']
    SequenceID: Optional['StringValue']
    SkipDiscount: Optional['BooleanValue']
    Type: Optional['StringValue']


@dataclass
class SalesInvoiceDocContact(BaseDataClassModel):
    Attention: Optional['StringValue']
    BusinessName: Optional['StringValue']
    Email: Optional['StringValue']
    Phone1: Optional['StringValue']


@dataclass
class SalesInvoiceFinancialDetails(BaseDataClassModel):
    BatchNbr: Optional['StringValue']
    Branch: Optional['StringValue']
    CustomerTaxZone: Optional['StringValue']


@dataclass
class SalesInvoiceFreightDetail(BaseDataClassModel):
    Description: Optional['StringValue']
    FreightAmount: Optional['DecimalValue']
    FreightCost: Optional['DecimalValue']
    LineTotal: Optional['DecimalValue']
    PremiumFreightAmount: Optional['DecimalValue']
    ShipmentNbr: Optional['StringValue']
    ShipmentType: Optional['StringValue']
    TotalFreightAmount: Optional['DecimalValue']
    Volume: Optional['DecimalValue']
    Weight: Optional['DecimalValue']


@dataclass
class SalesInvoiceSalesPersonDetail(BaseDataClassModel):
    CommissionableAmount: Optional['DecimalValue']
    CommissionAmount: Optional['DecimalValue']
    CommissionPercent: Optional['DecimalValue']
    SalespersonID: Optional['StringValue']


@dataclass
class SalesInvoiceTaxDetail(BaseDataClassModel):
    TaxableAmount: Optional['DecimalValue']
    TaxAmount: Optional['DecimalValue']
    TaxID: Optional['StringValue']


@dataclass
class SalesOrder(BaseDataClassModel):
    Approved: Optional['BooleanValue']
    BaseCurrencyID: Optional['StringValue']
    BillToAddress: Optional['Address']
    BillToAddressOverride: Optional['BooleanValue']
    BillToAddressValidated: Optional['BooleanValue']
    BillToContact: Optional['DocContact']
    BillToContactOverride: Optional['BooleanValue']
    Branch: Optional['StringValue']
    CashAccount: Optional['StringValue']
    Commissions: Optional['Commissions']
    ContactID: Optional['StringValue']
    ControlTotal: Optional['DecimalValue']
    CreditHold: Optional['BooleanValue']
    CurrencyID: Optional['StringValue']
    CurrencyRate: Optional['DecimalValue']
    CurrencyRateTypeID: Optional['StringValue']
    CustomerID: Optional['StringValue']
    CustomerOrder: Optional['StringValue']
    Date: Optional['DateTimeValue']
    Description: Optional['StringValue']
    DestinationWarehouseID: Optional['StringValue']
    Details: List[Optional['SalesOrderDetail']]
    DisableAutomaticDiscountUpdate: Optional['BooleanValue']
    DisableAutomaticTaxCalculation: Optional['BooleanValue']
    DiscountDetails: List[Optional['SalesOrdersDiscountDetails']]
    EffectiveDate: Optional['DateTimeValue']
    ExternalRef: Optional['StringValue']
    FinancialSettings: Optional['FinancialSettings']
    Hold: Optional['BooleanValue']
    IsTaxValid: Optional['BooleanValue']
    LastModified: Optional['DateTimeValue']
    LocationID: Optional['StringValue']
    MaxRiskScore: Optional['DecimalValue']
    OrderedQty: Optional['DecimalValue']
    OrderNbr: Optional['StringValue']
    OrderRisks: List[Optional['OrderRisks']]
    OrderTotal: Optional['DecimalValue']
    OrderType: Optional['StringValue']
    PaymentMethod: Optional['StringValue']
    Payments: List[Optional['SalesOrderPayment']]
    PreferredWarehouseID: Optional['StringValue']
    Project: Optional['StringValue']
    ReciprocalRate: Optional['DecimalValue']
    Relations: List[Optional['RelationDetail']]
    RequestedOn: Optional['DateTimeValue']
    Shipments: List[Optional['SalesOrderShipment']]
    ShippingSettings: Optional['ShippingSettings']
    ShipToAddress: Optional['Address']
    ShipToAddressOverride: Optional['BooleanValue']
    ShipToAddressValidated: Optional['BooleanValue']
    ShipToContact: Optional['DocContact']
    ShipToContactOverride: Optional['BooleanValue']
    ShipVia: Optional['StringValue']
    Status: Optional['StringValue']
    TaxDetails: List[Optional['TaxDetail']]
    TaxTotal: Optional['DecimalValue']
    Totals: Optional['Totals']
    VATExemptTotal: Optional['DecimalValue']
    VATTaxableTotal: Optional['DecimalValue']
    ExternalOrderOriginal: Optional['BooleanValue']
    ExternalRefundRef: Optional['StringValue']
    WillCall: Optional['BooleanValue']
    PaymentRef: Optional['StringValue']
    NoteID: Optional['GuidValue']
    UsrExternalOrderOriginal: Optional['BooleanValue']
    ExternalOrderOrigin: Optional['StringValue']
    ExternalOrderSource: Optional['StringValue']
    TaxCalcMode: Optional['StringValue']
    CreatedDate: Optional['DateTimeValue']


@dataclass
class SalesOrderCreateReceipt(BaseDataClassModel):
    entity: Optional['SalesOrder']
    parameters: Optional[Any]


@dataclass
class SalesOrderCreateShipment(BaseDataClassModel):
    entity: Optional['SalesOrder']
    parameters: Optional[Any]


@dataclass
class SalesOrderCreditCardTransactionDetail(BaseDataClassModel):
    AuthNbr: Optional['StringValue']
    ExtProfileId: Optional['StringValue']
    NeedValidation: Optional['BooleanValue']
    TranDate: Optional['DateTimeValue']
    TranNbr: Optional['StringValue']
    TranType: Optional['StringValue']
    CardType: Optional['StringValue']


@dataclass
class SalesOrderCustomAction(BaseDataClassModel):
    entity: Optional['SalesOrder']
    parameters: Optional[Any]


@dataclass
class SalesOrderDetail(BaseDataClassModel):
    Account: Optional['StringValue']
    Allocations: List[Optional['SalesOrderDetailAllocation']]
    AlternateID: Optional['StringValue']
    Amount: Optional['DecimalValue']
    AutoCreateIssue: Optional['BooleanValue']
    AverageCost: Optional['DecimalValue']
    Branch: Optional['StringValue']
    CalculateDiscountsOnImport: Optional['BooleanValue']
    Commissionable: Optional['BooleanValue']
    Completed: Optional['BooleanValue']
    CostCode: Optional['StringValue']
    CustomerOrderNbr: Optional['StringValue']
    DiscountAmount: Optional['DecimalValue']
    DiscountCode: Optional['StringValue']
    DiscountedUnitPrice: Optional['DecimalValue']
    DiscountPercent: Optional['DecimalValue']
    ExtendedPrice: Optional['DecimalValue']
    FreeItem: Optional['BooleanValue']
    InventoryID: Optional['StringValue']
    InvoiceLineNbr: Optional['IntValue']
    InvoiceNbr: Optional['StringValue']
    InvoiceType: Optional['StringValue']
    LastModifiedDate: Optional['StringValue']
    LineDescription: Optional['StringValue']
    LineNbr: Optional['IntValue']
    LineType: Optional['StringValue']
    Location: Optional['StringValue']
    ManualDiscount: Optional['BooleanValue']
    MarkForPO: Optional['BooleanValue']
    OpenQty: Optional['DecimalValue']
    Operation: Optional['StringValue']
    OrderQty: Optional['DecimalValue']
    OvershipThreshold: Optional['DecimalValue']
    POSource: Optional['StringValue']
    ProjectTask: Optional['StringValue']
    PurchaseWarehouse: Optional['StringValue']
    PurchasingDetails: List[Optional['PurchasingDetail']]
    VendorID: Optional['StringValue']
    QtyOnShipments: Optional['DecimalValue']
    ReasonCode: Optional['StringValue']
    RequestedOn: Optional['DateTimeValue']
    SalespersonID: Optional['StringValue']
    SchedOrderDate: Optional['DateTimeValue']
    ShipOn: Optional['DateTimeValue']
    ShippingRule: Optional['StringValue']
    ShipToLocation: Optional['StringValue']
    Subitem: Optional['StringValue']
    TaxCategory: Optional['StringValue']
    TaxZone: Optional['StringValue']
    UnbilledAmount: Optional['DecimalValue']
    UndershipThreshold: Optional['DecimalValue']
    UnitCost: Optional['DecimalValue']
    UnitPrice: Optional['DecimalValue']
    UOM: Optional['StringValue']
    WarehouseID: Optional['StringValue']
    AssociatedOrderLineNbr: Optional['IntValue']
    GiftMessage: Optional['StringValue']
    ManualPrice: Optional['BooleanValue']
    LotSerialNbr: Optional['StringValue']
    NoteID: Optional['GuidValue']
    ExternalRef: Optional['StringValue']


@dataclass
class SalesOrderDetailAllocation(BaseDataClassModel):
    Allocated: Optional['BooleanValue']
    AllocWarehouseID: Optional['StringValue']
    Completed: Optional['BooleanValue']
    CustomerOrderNbr: Optional['StringValue']
    ExpirationDate: Optional['DateTimeValue']
    InventoryID: Optional['StringValue']
    LineNbr: Optional['IntValue']
    LocationID: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    OrderNbr: Optional['StringValue']
    OrderType: Optional['StringValue']
    Qty: Optional['DecimalValue']
    QtyOnShipments: Optional['DecimalValue']
    QtyReceived: Optional['DecimalValue']
    RelatedDocument: Optional['StringValue']
    SchedOrderDate: Optional['DateTimeValue']
    ShipOn: Optional['DateTimeValue']
    SplitLineNbr: Optional['IntValue']
    Subitem: Optional['StringValue']
    UOM: Optional['StringValue']


@dataclass
class SalesOrderPayment(BaseDataClassModel):
    ApplicationDate: Optional['DateTimeValue']
    AppliedToOrder: Optional['DecimalValue']
    Authorize: Optional['BooleanValue']
    Balance: Optional['DecimalValue']
    CardAccountNbr: Optional['StringValue']
    Capture: Optional['BooleanValue']
    CashAccount: Optional['StringValue']
    Currency: Optional['StringValue']
    CreditCardTransactionInfo: List[Optional['SalesOrderCreditCardTransactionDetail']]
    Description: Optional['StringValue']
    DocType: Optional['StringValue']
    Hold: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    OrigTransactionNbr: Optional['StringValue']
    PaymentAmount: Optional['DecimalValue']
    PaymentMethod: Optional['StringValue']
    PaymentRef: Optional['StringValue']
    ProcessingCenterID: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    Refund: Optional['BooleanValue']
    SaveCard: Optional['BooleanValue']
    Status: Optional['StringValue']
    TransferredtoInvoice: Optional['DecimalValue']
    ValidateCCRefundOrigTransaction: Optional['BooleanValue']
    ExternalRef: Optional['StringValue']
    NoteID: Optional['GuidValue']


@dataclass
class SalesOrderShipment(BaseDataClassModel):
    InventoryDocType: Optional['StringValue']
    InventoryRefNbr: Optional['StringValue']
    InvoiceNbr: Optional['StringValue']
    InvoiceType: Optional['StringValue']
    ShipmentDate: Optional['DateTimeValue']
    ShipmentNbr: Optional['StringValue']
    ShipmentType: Optional['StringValue']
    ShippedQty: Optional['DecimalValue']
    ShippedVolume: Optional['DecimalValue']
    ShippedWeight: Optional['DecimalValue']
    Status: Optional['StringValue']
    InventoryNoteID: Optional['GuidValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    OrderNoteID: Optional['GuidValue']
    ShippingNoteID: Optional['GuidValue']


@dataclass
class SalesOrdersDiscountDetails(BaseDataClassModel):
    Description: Optional['StringValue']
    DiscountableAmount: Optional['DecimalValue']
    DiscountableQty: Optional['DecimalValue']
    DiscountAmount: Optional['DecimalValue']
    DiscountCode: Optional['StringValue']
    DiscountPercent: Optional['DecimalValue']
    ExternalDiscountCode: Optional['StringValue']
    FreeItem: Optional['StringValue']
    FreeItemQty: Optional['DecimalValue']
    ManualDiscount: Optional['BooleanValue']
    SequenceID: Optional['StringValue']
    SkipDiscount: Optional['BooleanValue']
    Type: Optional['StringValue']


@dataclass
class SalesPersonDetail(BaseDataClassModel):
    CommissionableAmount: Optional['DecimalValue']
    CommissionAmount: Optional['DecimalValue']
    CommissionPercent: Optional['DecimalValue']
    SalespersonID: Optional['StringValue']


@dataclass
class SalesPriceDetail(BaseDataClassModel):
    BreakQty: Optional['DecimalValue']
    CreatedDateTime: Optional['DateTimeValue']
    CurrencyID: Optional['StringValue']
    Description: Optional['StringValue']
    EffectiveDate: Optional['DateTimeValue']
    ExpirationDate: Optional['DateTimeValue']
    InventoryID: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Price: Optional['DecimalValue']
    PriceCode: Optional['StringValue']
    PriceType: Optional['StringValue']
    Promotion: Optional['BooleanValue']
    RecordID: Optional['IntValue']
    Tax: Optional['StringValue']
    UOM: Optional['StringValue']
    NoteID: Optional['GuidValue']
    Warehouse: Optional['StringValue']
    TaxCalculationMode: Optional['StringValue']


@dataclass
class SalesPriceWorksheet(BaseDataClassModel):
    CreatedDateTime: Optional['DateTimeValue']
    Description: Optional['StringValue']
    EffectiveDate: Optional['DateTimeValue']
    ExpirationDate: Optional['DateTimeValue']
    Hold: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    OverwriteOverlappingPrices: Optional['BooleanValue']
    ReferenceNbr: Optional['StringValue']
    SalesPrices: List[Optional['SalesPricesWorksheetDetail']]
    Status: Optional['StringValue']


@dataclass
class SalesPriceWorksheetCustomAction(BaseDataClassModel):
    entity: Optional['SalesPriceWorksheet']
    parameters: Optional[Any]


@dataclass
class SalesPricesInquiry(BaseDataClassModel):
    EffectiveAsOf: Optional['DateTimeValue']
    InventoryID: Optional['StringValue']
    ItemClassID: Optional['StringValue']
    PriceClass: Optional['StringValue']
    PriceCode: Optional['StringValue']
    PriceManager: Optional['StringValue']
    PriceManagerIsMe: Optional['BooleanValue']
    PriceType: Optional['StringValue']
    PriceWorkgroup: Optional['StringValue']
    PriceWorkgroupIsMine: Optional['BooleanValue']
    SalesPriceDetails: List[Optional['SalesPriceDetail']]
    TaxCalculationMode: Optional['StringValue']


@dataclass
class SalesPricesInquiryCustomAction(BaseDataClassModel):
    entity: Optional['SalesPricesInquiry']
    parameters: Optional[Any]


@dataclass
class SalesPricesWorksheetDetail(BaseDataClassModel):
    BreakQty: Optional['DecimalValue']
    CurrencyID: Optional['StringValue']
    Description: Optional['StringValue']
    InventoryID: Optional['StringValue']
    LineID: Optional['IntValue']
    PendingPrice: Optional['DecimalValue']
    PriceCode: Optional['StringValue']
    PriceType: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    SourcePrice: Optional['DecimalValue']
    Tax: Optional['StringValue']
    UOM: Optional['StringValue']


@dataclass
class Salesperson(BaseDataClassModel):
    CreatedDateTime: Optional['DateTimeValue']
    DefaultCommission: Optional['DecimalValue']
    IsActive: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Name: Optional['StringValue']
    SalespersonID: Optional['StringValue']
    SalesSubaccount: Optional['StringValue']


@dataclass
class SalespersonCustomAction(BaseDataClassModel):
    entity: Optional['Salesperson']
    parameters: Optional[Any]


@dataclass
class SendEmail(BaseDataClassModel):
    entity: Optional['Email']


@dataclass
class ServiceOrder(BaseDataClassModel):
    Address: Optional['SrvOrdAddress']
    AppointmentDuration: Optional['StringValue']
    Appointments: List[Optional['SrvOrdAppointments']]
    AppointmentsNeeded: Optional['BooleanValue']
    Attributes: List[Optional['SrvOrdAttributes']]
    BillableTotal: Optional['DecimalValue']
    BranchLocation: Optional['StringValue']
    Contact: Optional['SrvOrdContact']
    ContractInfo: Optional['SrvOrdContractInfo']
    Currency: Optional['StringValue']
    Customer: Optional['StringValue']
    CustomerOrder: Optional['StringValue']
    Date: Optional['DateTimeValue']
    DefaultProjectTask: Optional['StringValue']
    DefaultStaff: List[Optional['SrvOrdDefaultStaff']]
    Description: Optional['StringValue']
    Details: List[Optional['SrvOrdDetails']]
    EstimatedDuration: Optional['StringValue']
    ExternalReference: Optional['StringValue']
    FinancialDetails: Optional['SrvOrdFinancialDetails']
    Hold: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Location: Optional['StringValue']
    OtherInformation: Optional['SrvOrdOtherInformation']
    Override: Optional['BooleanValue']
    Prepayments: List[Optional['SrvOrdPrepayments']]
    Priority: Optional['StringValue']
    Problem: Optional['StringValue']
    Project: Optional['StringValue']
    ServiceOrderNbr: Optional['StringValue']
    ServiceOrderTotal: Optional['DecimalValue']
    ServiceOrderType: Optional['StringValue']
    Severity: Optional['StringValue']
    SLA: Optional['DateTimeValue']
    SLATime: Optional['DateTimeValue']
    Status: Optional['StringValue']
    Supervisor: Optional['StringValue']
    TaxDetails: List[Optional['SrvOrdTaxDetails']]
    TaxTotal: Optional['DecimalValue']
    Totals: Optional['SrvOrdTotals']
    WaitingforPurchasedItems: Optional['BooleanValue']
    WorkflowStage: Optional['StringValue']


@dataclass
class ServiceOrderCustomAction(BaseDataClassModel):
    entity: Optional['ServiceOrder']
    parameters: Optional[Any]


@dataclass
class SettingsForPR(BaseDataClassModel):
    ExportScenario: Optional['StringValue']
    PRProcessing: Optional['StringValue']
    Report: Optional['StringValue']


@dataclass
class ShipToSettings(BaseDataClassModel):
    ShipToAddress: Optional['Address']
    ShipToAddressOverride: Optional['BooleanValue']
    ShipToContact: Optional['DocContact']
    ShipToContactOverride: Optional['BooleanValue']
    Validated: Optional['BooleanValue']


@dataclass
class ShipVia(BaseDataClassModel):
    CalculationMethod: Optional['StringValue']
    Calendar: Optional['StringValue']
    CarrierID: Optional['StringValue']
    CommonCarrier: Optional['BooleanValue']
    Description: Optional['StringValue']
    FreightExpenseAccount: Optional['StringValue']
    FreightExpenseSubaccount: Optional['StringValue']
    FreightRates: List[Optional['ShipViaFreightRate']]
    FreightSalesAccount: Optional['StringValue']
    FreightSalesSubaccount: Optional['StringValue']
    Packages: List[Optional['ShippingBox']]
    TaxCategory: Optional['StringValue']


@dataclass
class ShipViaCustomAction(BaseDataClassModel):
    entity: Optional['ShipVia']
    parameters: Optional[Any]


@dataclass
class ShipViaFreightRate(BaseDataClassModel):
    LineNbr: Optional['IntValue']
    Rate: Optional['DecimalValue']
    Volume: Optional['DecimalValue']
    Weight: Optional['DecimalValue']
    ZoneID: Optional['StringValue']


@dataclass
class Shipment(BaseDataClassModel):
    BaseCurrencyID: Optional['StringValue']
    ControlQty: Optional['DecimalValue']
    CreatedDateTime: Optional['DateTimeValue']
    CurrencyRate: Optional['DecimalValue']
    CurrencyRateTypeID: Optional['StringValue']
    CurrencyViewState: Optional['BooleanValue']
    CustomerID: Optional['StringValue']
    CreateNewShipmentForEveryOrder: Optional['BooleanValue']
    Details: List[Optional['ShipmentDetail']]
    Description: Optional['StringValue']
    EffectiveDate: Optional['DateTimeValue']
    FOBPoint: Optional['StringValue']
    OverrideFreightPrice: Optional['BooleanValue']
    FreightPrice: Optional['DecimalValue']
    FreightCost: Optional['DecimalValue']
    FreightCurrencyID: Optional['StringValue']
    GroundCollect: Optional['BooleanValue']
    Hold: Optional['BooleanValue']
    Insurance: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    LocationID: Optional['StringValue']
    Operation: Optional['StringValue']
    Orders: List[Optional['ShipmentOrderDetail']]
    Owner: Optional['StringValue']
    PackageCount: Optional['IntValue']
    Packages: List[Optional['ShipmentPackage']]
    PackageWeight: Optional['DecimalValue']
    Picked: Optional['BooleanValue']
    ReciprocalRate: Optional['DecimalValue']
    ResidentialDelivery: Optional['BooleanValue']
    SaturdayDelivery: Optional['BooleanValue']
    ShipmentDate: Optional['DateTimeValue']
    ShipmentNbr: Optional['StringValue']
    ShippedQty: Optional['DecimalValue']
    ShippedVolume: Optional['DecimalValue']
    ShippedWeight: Optional['DecimalValue']
    ShippingSettings: Optional['ShipToSettings']
    ShippingTerms: Optional['StringValue']
    ShippingZoneID: Optional['StringValue']
    ShipVia: Optional['StringValue']
    Status: Optional['StringValue']
    ToWarehouseID: Optional['StringValue']
    Type: Optional['StringValue']
    UnlimitedPackages: Optional['BooleanValue']
    UseCustomersAccount: Optional['BooleanValue']
    WarehouseID: Optional['StringValue']
    WorkgroupID: Optional['StringValue']
    NoteID: Optional['GuidValue']


@dataclass
class ShipmentCustomAction(BaseDataClassModel):
    entity: Optional['Shipment']
    parameters: Optional[Any]


@dataclass
class ShipmentDetail(BaseDataClassModel):
    Allocations: List[Optional['ShipmentDetailAllocation']]
    Description: Optional['StringValue']
    ExpirationDate: Optional['DateTimeValue']
    FreeItem: Optional['BooleanValue']
    InventoryID: Optional['StringValue']
    LineNbr: Optional['IntValue']
    LocationID: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    OpenQty: Optional['DecimalValue']
    OrderedQty: Optional['DecimalValue']
    OrderLineNbr: Optional['IntValue']
    OrderNbr: Optional['StringValue']
    OrderType: Optional['StringValue']
    OriginalQty: Optional['DecimalValue']
    ReasonCode: Optional['StringValue']
    ShippedQty: Optional['DecimalValue']
    Subitem: Optional['StringValue']
    UOM: Optional['StringValue']
    WarehouseID: Optional['StringValue']


@dataclass
class ShipmentDetailAllocation(BaseDataClassModel):
    Description: Optional['StringValue']
    ExpirationDate: Optional['DateTimeValue']
    InventoryID: Optional['StringValue']
    LocationID: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    OrderNbr: Optional['StringValue']
    OrderType: Optional['StringValue']
    Qty: Optional['DecimalValue']
    Subitem: Optional['StringValue']
    SplitLineNbr: Optional['IntValue']
    UOM: Optional['StringValue']


@dataclass
class ShipmentOrderDetail(BaseDataClassModel):
    InventoryDocType: Optional['StringValue']
    InventoryRefNbr: Optional['StringValue']
    InvoiceNbr: Optional['StringValue']
    InvoiceType: Optional['StringValue']
    OrderNbr: Optional['StringValue']
    OrderType: Optional['StringValue']
    ShipmentNbr: Optional['StringValue']
    ShipmentType: Optional['StringValue']
    ShippedQty: Optional['DecimalValue']
    ShippedVolume: Optional['DecimalValue']
    ShippedWeight: Optional['DecimalValue']
    OrderNoteID: Optional['GuidValue']


@dataclass
class ShipmentPackage(BaseDataClassModel):
    BoxID: Optional['StringValue']
    CODAmount: Optional['DecimalValue']
    Confirmed: Optional['BooleanValue']
    CustomRefNbr1: Optional['StringValue']
    CustomRefNbr2: Optional['StringValue']
    DeclaredValue: Optional['DecimalValue']
    Description: Optional['StringValue']
    TrackingNbr: Optional['StringValue']
    Type: Optional['StringValue']
    UOM: Optional['StringValue']
    Weight: Optional['DecimalValue']
    Length: Optional['DecimalValue']
    Width: Optional['DecimalValue']
    Height: Optional['DecimalValue']
    PackageContents: List[Optional['ShipmentPackageDetail']]
    LineNbr: Optional['IntValue']
    NoteID: Optional['GuidValue']


@dataclass
class ShipmentPackageDetail(BaseDataClassModel):
    InventoryID: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    OrigOrderNbr: Optional['StringValue']
    OrigOrderType: Optional['StringValue']
    Quantity: Optional['DecimalValue']
    ShipmentSplitLineNbr: Optional['IntValue']
    Subitem: Optional['StringValue']
    UOM: Optional['StringValue']


@dataclass
class ShippingBox(BaseDataClassModel):
    ActiveByDefault: Optional['BooleanValue']
    BoxID: Optional['StringValue']
    BoxWeight: Optional['DecimalValue']
    CarriersPackage: Optional['StringValue']
    Description: Optional['StringValue']
    Height: Optional['DecimalValue']
    Length: Optional['DecimalValue']
    MaxVolume: Optional['DecimalValue']
    MaxWeight: Optional['DecimalValue']
    VolumeUOM: Optional['StringValue']
    WeightUOM: Optional['StringValue']
    Width: Optional['DecimalValue']
    LinearUOM: Optional['StringValue']


@dataclass
class ShippingBoxCustomAction(BaseDataClassModel):
    entity: Optional['ShippingBox']
    parameters: Optional[Any]


@dataclass
class ShippingInstructions(BaseDataClassModel):
    ShippingDestinationType: Optional['StringValue']
    ShippingLocation: Optional['StringValue']
    ShipTo: Optional['StringValue']
    ShipToAddress: Optional['Address']
    ShipToAddressOverride: Optional['BooleanValue']
    ShipToAddressValidated: Optional['BooleanValue']
    ShipToContact: Optional['DocContact']
    ShipToContactOverride: Optional['BooleanValue']
    Warehouse: Optional['StringValue']


@dataclass
class ShippingSettings(BaseDataClassModel):
    CancelByDate: Optional['DateTimeValue']
    Canceled: Optional['BooleanValue']
    FOBPoint: Optional['StringValue']
    GroundCollect: Optional['BooleanValue']
    Insurance: Optional['BooleanValue']
    PreferredWarehouseID: Optional['StringValue']
    Priority: Optional['ShortValue']
    ResidentialDelivery: Optional['BooleanValue']
    SaturdayDelivery: Optional['BooleanValue']
    ScheduledShipmentDate: Optional['DateTimeValue']
    ShippingRule: Optional['StringValue']
    ShippingTerms: Optional['StringValue']
    ShippingZone: Optional['StringValue']
    ShipSeparately: Optional['BooleanValue']
    ShipVia: Optional['StringValue']
    ShopForRates: Optional['ShopForRates']
    UseCustomersAccount: Optional['BooleanValue']
    FreightPrice: Optional['DecimalValue']
    FreightCost: Optional['DecimalValue']
    FreightCostIsuptodate: Optional['BooleanValue']
    FreightTaxCategory: Optional['StringValue']
    OrderVolume: Optional['DecimalValue']
    OrderWeight: Optional['DecimalValue']
    OverrideFreightPrice: Optional['BooleanValue']
    PackageWeight: Optional['DecimalValue']
    PremiumFreight: Optional['DecimalValue']


@dataclass
class ShippingTerm(BaseDataClassModel):
    Description: Optional['StringValue']
    Details: List[Optional['ShippingTermDetail']]
    TermID: Optional['StringValue']


@dataclass
class ShippingTermCustomAction(BaseDataClassModel):
    entity: Optional['ShippingTerm']
    parameters: Optional[Any]


@dataclass
class ShippingTermDetail(BaseDataClassModel):
    BreakAmount: Optional['DecimalValue']
    FreightCost: Optional['DecimalValue']
    InvoiceAmount: Optional['DecimalValue']
    LineHandling: Optional['DecimalValue']
    LineNbr: Optional['IntValue']
    ShippingandHandling: Optional['DecimalValue']


@dataclass
class ShippingZones(BaseDataClassModel):
    Description: Optional['StringValue']
    ZoneID: Optional['StringValue']


@dataclass
class ShippingZonesCustomAction(BaseDataClassModel):
    entity: Optional['ShippingZones']
    parameters: Optional[Any]


@dataclass
class ShopForRates(BaseDataClassModel):
    IsManualPackage: Optional['BooleanValue']
    OrderWeight: Optional['DecimalValue']
    PackageWeight: Optional['DecimalValue']


@dataclass
class ShopifyStore(BaseDataClassModel):
    AccessToken: Optional['StringValue']
    Active: Optional['BooleanValue']
    Connector: Optional['StringValue']
    Default: Optional['BooleanValue']
    SharedSecret: Optional['StringValue']
    StoreAdminURL: Optional['StringValue']
    StoreName: Optional['StringValue']


@dataclass
class ShopifyStoreCustomAction(BaseDataClassModel):
    entity: Optional['ShopifyStore']
    parameters: Optional[Any]


@dataclass
class ShortValue(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class SrvOrdAddress(BaseDataClassModel):
    AddressLine1: Optional['StringValue']
    AddressLine2: Optional['StringValue']
    City: Optional['StringValue']
    Country: Optional['StringValue']
    PostalCode: Optional['StringValue']
    State: Optional['StringValue']


@dataclass
class SrvOrdAppointments(BaseDataClassModel):
    AppointmentNbr: Optional['StringValue']
    Confirmed: Optional['BooleanValue']
    ScheduledEndDate: Optional['DateTimeValue']
    ScheduledEndTime: Optional['DateTimeValue']
    ScheduledStartDate: Optional['DateTimeValue']
    ScheduledStartTime: Optional['DateTimeValue']
    ServiceOrderType: Optional['StringValue']
    Status: Optional['StringValue']


@dataclass
class SrvOrdAttributes(BaseDataClassModel):
    Attribute: Optional['StringValue']
    RefNoteID: Optional['GuidValue']
    Required: Optional['BooleanValue']
    Value: Optional['StringValue']


@dataclass
class SrvOrdContact(BaseDataClassModel):
    Attention: Optional['StringValue']
    CompanyName: Optional['StringValue']
    Email: Optional['StringValue']
    Phone1: Optional['StringValue']
    Phone1Type: Optional['StringValue']


@dataclass
class SrvOrdContractInfo(BaseDataClassModel):
    ContractPeriod: Optional['StringValue']
    ServiceContract: Optional['StringValue']


@dataclass
class SrvOrdDefaultStaff(BaseDataClassModel):
    Comment: Optional['StringValue']
    Description: Optional['StringValue']
    InventoryID: Optional['StringValue']
    LineNbr: Optional['IntValue']
    ServiceLineRef: Optional['StringValue']
    ServiceOrderNbr: Optional['StringValue']
    ServiceOrderType: Optional['StringValue']
    StaffMemberID: Optional['StringValue']
    Type: Optional['StringValue']


@dataclass
class SrvOrdDetails(BaseDataClassModel):
    Account: Optional['StringValue']
    Amount: Optional['DecimalValue']
    AppointmentAmount: Optional['DecimalValue']
    AppointmentCount: Optional['IntValue']
    AppointmentDuration: Optional['StringValue']
    AppointmentEstimatedDuration: Optional['StringValue']
    AppointmentQty: Optional['DecimalValue']
    Billable: Optional['BooleanValue']
    BillingRule: Optional['StringValue']
    Branch: Optional['StringValue']
    ComponentID: Optional['StringValue']
    ComponentLineRef: Optional['StringValue']
    CostCode: Optional['StringValue']
    CoveredQty: Optional['DecimalValue']
    Description: Optional['StringValue']
    DiscountAmount: Optional['DecimalValue']
    DiscountPercent: Optional['DecimalValue']
    EquipmentAction: Optional['StringValue']
    EquipmentActionComment: Optional['StringValue']
    EstimatedAmount: Optional['DecimalValue']
    EstimatedDuration: Optional['StringValue']
    EstimatedQty: Optional['DecimalValue']
    ExtPrice: Optional['DecimalValue']
    InventoryID: Optional['StringValue']
    LastReference: Optional['StringValue']
    LineNbr: Optional['IntValue']
    LineRef: Optional['StringValue']
    LineStatus: Optional['StringValue']
    LineType: Optional['StringValue']
    Location: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    ManualPrice: Optional['BooleanValue']
    MarkforPO: Optional['BooleanValue']
    ModelEquipmentLineRef: Optional['StringValue']
    OverageQty: Optional['DecimalValue']
    OverageUnitPrice: Optional['DecimalValue']
    POCompleted: Optional['BooleanValue']
    PONbr: Optional['StringValue']
    POStatus: Optional['StringValue']
    PrepaidItem: Optional['BooleanValue']
    ProjectTask: Optional['StringValue']
    Qty: Optional['DecimalValue']
    ServiceContractItem: Optional['BooleanValue']
    ServiceOrderNbr: Optional['StringValue']
    ServiceOrderType: Optional['StringValue']
    SortOrder: Optional['IntValue']
    StaffMemberID: Optional['StringValue']
    Subaccount: Optional['StringValue']
    Subitem: Optional['StringValue']
    TargetEquipmentID: Optional['StringValue']
    TaxCategory: Optional['StringValue']
    UnitCost: Optional['DecimalValue']
    UnitPrice: Optional['DecimalValue']
    UOM: Optional['StringValue']
    VendorID: Optional['StringValue']
    VendorLocationID: Optional['StringValue']
    Warehouse: Optional['StringValue']
    Warranty: Optional['BooleanValue']


@dataclass
class SrvOrdFinancialDetails(BaseDataClassModel):
    BillingCustomer: Optional['StringValue']
    BillingCycle: Optional['StringValue']
    BillingLocation: Optional['StringValue']
    Branch: Optional['StringValue']
    Commissionable: Optional['BooleanValue']
    CustomerTaxZone: Optional['StringValue']
    RunBillingFor: Optional['StringValue']
    Salesperson: Optional['StringValue']
    TaxCalculationMode: Optional['StringValue']


@dataclass
class SrvOrdOtherInformation(BaseDataClassModel):
    BatchNumber: Optional['StringValue']
    Description: Optional['StringValue']
    DocumentType: Optional['StringValue']
    InvoiceNbr: Optional['StringValue']
    IssueReferenceNbr: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']


@dataclass
class SrvOrdPrepayments(BaseDataClassModel):
    ApplicationDate: Optional['DateTimeValue']
    AppliedtoOrders: Optional['DecimalValue']
    AvailableBalance: Optional['DecimalValue']
    CashAccount: Optional['IntValue']
    Currency: Optional['StringValue']
    PaymentAmount: Optional['DecimalValue']
    PaymentMethod: Optional['StringValue']
    PaymentRef: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    SourceAppointmentNbr: Optional['StringValue']
    Status: Optional['StringValue']
    Type: Optional['StringValue']


@dataclass
class SrvOrdTaxDetails(BaseDataClassModel):
    IncludeinVATExemptTotal: Optional['BooleanValue']
    PendingVAT: Optional['BooleanValue']
    RecordID: Optional['IntValue']
    ReverseVAT: Optional['BooleanValue']
    ServiceOrderNbr: Optional['StringValue']
    ServiceOrderType: Optional['StringValue']
    StatisticalVAT: Optional['BooleanValue']
    TaxableAmount: Optional['DecimalValue']
    TaxAmount: Optional['DecimalValue']
    TaxID: Optional['StringValue']
    TaxRate: Optional['DecimalValue']
    TaxType: Optional['StringValue']


@dataclass
class SrvOrdTotals(BaseDataClassModel):
    AppointmentTotal: Optional['DecimalValue']
    BillableTotal: Optional['DecimalValue']
    EstimatedTotal: Optional['DecimalValue']
    LineTotal: Optional['DecimalValue']
    PrepaymentApplied: Optional['DecimalValue']
    PrepaymentReceived: Optional['DecimalValue']
    PrepaymentRemaining: Optional['DecimalValue']
    ServiceOrderBillableUnpaidBalance: Optional['DecimalValue']
    ServiceOrderTotal: Optional['DecimalValue']
    ServiceOrderUnpaidBalance: Optional['DecimalValue']
    TaxTotal: Optional['DecimalValue']
    VATExemptTotal: Optional['DecimalValue']
    VATTaxableTotal: Optional['DecimalValue']


@dataclass
class StartAppointment(BaseDataClassModel):
    entity: Optional['Appointment']


@dataclass
class StockItem(BaseDataClassModel):
    ABCCode: Optional['StringValue']
    Attributes: List[Optional['AttributeValue']]
    AutoIncrementalValue: Optional['StringValue']
    AverageCost: Optional['DecimalValue']
    BaseUOM: Optional['StringValue']
    Boxes: List[Optional['BoxStockItem']]
    Categories: List[Optional['CategoryStockItem']]
    COGSAccount: Optional['StringValue']
    COGSSubaccount: Optional['StringValue']
    Content: Optional['StringValue']
    CountryOfOrigin: Optional['StringValue']
    CrossReferences: List[Optional['InventoryItemCrossReference']]
    CurrentStdCost: Optional['DecimalValue']
    DefaultIssueLocationID: Optional['StringValue']
    DefaultPrice: Optional['DecimalValue']
    DefaultReceiptLocationID: Optional['StringValue']
    DefaultSubitem: Optional['StringValue']
    DefaultWarehouseID: Optional['StringValue']
    DeferralAccount: Optional['StringValue']
    DeferralSubaccount: Optional['StringValue']
    Description: Optional['StringValue']
    DimensionVolume: Optional['DecimalValue']
    DimensionWeight: Optional['DecimalValue']
    DiscountAccount: Optional['StringValue']
    DiscountSubaccount: Optional['StringValue']
    ImageUrl: Optional['StringValue']
    InventoryAccount: Optional['StringValue']
    InventoryID: Optional['StringValue']
    InventorySubaccount: Optional['StringValue']
    IsAKit: Optional['BooleanValue']
    ItemClass: Optional['StringValue']
    ItemStatus: Optional['StringValue']
    ItemType: Optional['StringValue']
    LandedCostVarianceAccount: Optional['StringValue']
    LandedCostVarianceSubaccount: Optional['StringValue']
    LastCost: Optional['DecimalValue']
    LastModified: Optional['DateTimeValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    LastStdCost: Optional['DecimalValue']
    LotSerialClass: Optional['StringValue']
    Markup: Optional['DecimalValue']
    MaxCost: Optional['DecimalValue']
    MinCost: Optional['DecimalValue']
    MinMarkup: Optional['DecimalValue']
    MSRP: Optional['DecimalValue']
    PackagingOption: Optional['StringValue']
    PackSeparately: Optional['BooleanValue']
    PendingStdCost: Optional['DecimalValue']
    POAccrualAccount: Optional['StringValue']
    POAccrualSubaccount: Optional['StringValue']
    PostingClass: Optional['StringValue']
    PriceClass: Optional['StringValue']
    PriceManager: Optional['StringValue']
    PriceWorkgroup: Optional['StringValue']
    ProductManager: Optional['StringValue']
    ProductWorkgroup: Optional['StringValue']
    PurchasePriceVarianceAccount: Optional['StringValue']
    PurchasePriceVarianceSubaccount: Optional['StringValue']
    PurchaseUOM: Optional['StringValue']
    ReasonCodeSubaccount: Optional['StringValue']
    ReplenishmentParameters: List[Optional['ReplenishmentParameterStockItem']]
    SalesAccount: Optional['StringValue']
    SalesSubaccount: Optional['StringValue']
    SalesUOM: Optional['StringValue']
    StandardCostRevaluationAccount: Optional['StringValue']
    StandardCostRevaluationSubaccount: Optional['StringValue']
    StandardCostVarianceAccount: Optional['StringValue']
    StandardCostVarianceSubaccount: Optional['StringValue']
    SubjectToCommission: Optional['BooleanValue']
    TaxCategory: Optional['StringValue']
    TariffCode: Optional['StringValue']
    UOMConversions: List[Optional['InventoryItemUOMConversion']]
    UseOnEntry: Optional['BooleanValue']
    ValuationMethod: Optional['StringValue']
    VendorDetails: List[Optional['StockItemVendorDetail']]
    VolumeUOM: Optional['StringValue']
    WarehouseDetails: List[Optional['StockItemWarehouseDetail']]
    WeightUOM: Optional['StringValue']
    CurySpecificMSRP: Optional['DecimalValue']
    CurySpecificPrice: Optional['DecimalValue']
    Availability: Optional['StringValue']
    CustomURL: Optional['StringValue']
    ExportToExternal: Optional['BooleanValue']
    FileURLs: List[Optional['InventoryFileUrls']]
    MetaDescription: Optional['StringValue']
    MetaKeywords: Optional['StringValue']
    NoteID: Optional['GuidValue']
    PageTitle: Optional['StringValue']
    SearchKeywords: Optional['StringValue']
    TemplateItemID: Optional['StringValue']
    Visibility: Optional['StringValue']
    NotAvailable: Optional['StringValue']


@dataclass
class StockItemCustomAction(BaseDataClassModel):
    entity: Optional['StockItem']
    parameters: Optional[Any]


@dataclass
class StockItemVendorDetail(BaseDataClassModel):
    Active: Optional['BooleanValue']
    AddLeadTimeDays: Optional['ShortValue']
    CurrencyID: Optional['StringValue']
    Default: Optional['BooleanValue']
    EOQ: Optional['DecimalValue']
    LastVendorPrice: Optional['DecimalValue']
    LeadTimeDays: Optional['ShortValue']
    Location: Optional['StringValue']
    LotSize: Optional['DecimalValue']
    MaxOrderQty: Optional['DecimalValue']
    MinOrderFrequencyInDays: Optional['IntValue']
    MinOrderQty: Optional['DecimalValue']
    Override: Optional['BooleanValue']
    PurchaseUnit: Optional['StringValue']
    RecordID: Optional['IntValue']
    Subitem: Optional['StringValue']
    VendorID: Optional['StringValue']
    VendorName: Optional['StringValue']
    Warehouse: Optional['StringValue']


@dataclass
class StockItemWarehouseDetail(BaseDataClassModel):
    DailyDemandForecast: Optional['DecimalValue']
    DailyDemandForecastErrorSTDEV: Optional['DecimalValue']
    DefaultIssueLocationID: Optional['StringValue']
    DefaultReceiptLocationID: Optional['StringValue']
    InventoryAccount: Optional['StringValue']
    InventorySubaccount: Optional['StringValue']
    IsDefault: Optional['BooleanValue']
    LastForecastDate: Optional['DateTimeValue']
    Override: Optional['BooleanValue']
    OverridePreferredVendor: Optional['BooleanValue']
    OverrideReplenishmentSettings: Optional['BooleanValue']
    OverrideStdCost: Optional['BooleanValue']
    PreferredVendor: Optional['StringValue']
    PriceOverride: Optional['BooleanValue']
    ProductManager: Optional['StringValue']
    ProductWorkgroup: Optional['StringValue']
    QtyOnHand: Optional['DecimalValue']
    ReplenishmentSource: Optional['StringValue']
    ReplenishmentWarehouse: Optional['StringValue']
    Seasonality: Optional['StringValue']
    ServiceLevel: Optional['DecimalValue']
    Status: Optional['StringValue']
    WarehouseID: Optional['StringValue']


@dataclass
class StorageDetail(BaseDataClassModel):
    InventoryID: Optional['StringValue']
    QtyAvailable: Optional['DecimalValue']
    QtyAvailableforIssue: Optional['DecimalValue']
    QtyHardAvailable: Optional['DecimalValue']
    WarehouseID: Optional['StringValue']
    LastModifiedDateofWarehouseQty: Optional['DateTimeValue']
    QtyOnHand: Optional['DecimalValue']


@dataclass
class StorageDetailByLocation(BaseDataClassModel):
    InventoryID: Optional['StringValue']
    QtyAvailableinLocation: Optional['DecimalValue']
    QtyAvailableforIssueinLocation: Optional['DecimalValue']
    QtyAvailableforShippinginLocation: Optional['DecimalValue']
    LocationID: Optional['StringValue']
    LastModifiedDateofLocationQty: Optional['DateTimeValue']
    QtyOnHandinLocation: Optional['DecimalValue']
    QtyAvailableinWarehouse: Optional['DecimalValue']
    QtyAvailableforIssueinWarehouse: Optional['DecimalValue']
    QtyAvailableforShippinginWarehouse: Optional['DecimalValue']
    WarehouseID: Optional['StringValue']
    LastModifiedDateofWarehouseQty: Optional['DateTimeValue']
    QtyOnHandinWarehouse: Optional['DecimalValue']


@dataclass
class StorageDetailsByLocationInquiry(BaseDataClassModel):
    SplitByLocation: Optional['BooleanValue']
    StorageDetailsByLocation: List[Optional['StorageDetailByLocation']]
    WarehouseID: Optional['StringValue']


@dataclass
class StorageDetailsByLocationInquiryCustomAction(BaseDataClassModel):
    entity: Optional['StorageDetailsByLocationInquiry']
    parameters: Optional[Any]


@dataclass
class StorageDetailsInquiry(BaseDataClassModel):
    StorageDetails: List[Optional['StorageDetail']]
    WarehouseID: Optional['StringValue']


@dataclass
class StorageDetailsInquiryCustomAction(BaseDataClassModel):
    entity: Optional['StorageDetailsInquiry']
    parameters: Optional[Any]


@dataclass
class StringValue(BaseDataClassModel):
    value: Optional[Any]


@dataclass
class Subaccount(BaseDataClassModel):
    Active: Optional['BooleanValue']
    Description: Optional['StringValue']
    Secured: Optional['BooleanValue']
    SubaccountCD: Optional['StringValue']
    SubaccountID: Optional['IntValue']


@dataclass
class SubaccountCustomAction(BaseDataClassModel):
    entity: Optional['Subaccount']
    parameters: Optional[Any]


@dataclass
class Subcontract(BaseDataClassModel):
    SubcontractNbr: Optional['StringValue']
    Status: Optional['StringValue']
    Date: Optional['DateTimeValue']
    StartDate: Optional['DateTimeValue']
    Description: Optional['StringValue']
    VendorID: Optional['StringValue']
    Location: Optional['StringValue']
    Owner: Optional['StringValue']
    CurrencyID: Optional['StringValue']
    BaseCurrencyID: Optional['StringValue']
    CurrencyEffectiveDate: Optional['DateTimeValue']
    CurrencyRate: Optional['DecimalValue']
    CurrencyRateTypeID: Optional['StringValue']
    CurrencyReciprocalRate: Optional['DecimalValue']
    VendorRef: Optional['StringValue']
    LineTotal: Optional['DecimalValue']
    DiscountTotal: Optional['DecimalValue']
    RetainageTotal: Optional['DecimalValue']
    SubcontractTotal: Optional['DecimalValue']
    TaxTotal: Optional['DecimalValue']
    ControlTotal: Optional['DecimalValue']
    Branch: Optional['StringValue']
    Terms: Optional['StringValue']
    VendorTaxZone: Optional['StringValue']
    ApplyRetainage: Optional['BooleanValue']
    RetainagePct: Optional['DecimalValue']
    DoNotEmail: Optional['BooleanValue']
    DoNotPrint: Optional['BooleanValue']
    Emailed: Optional['BooleanValue']
    Printed: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Details: List[Optional['SubcontractDetail']]
    TaxDetails: List[Optional['SubcontractTaxDetail']]
    VendorAddressInfo: Optional['SubcontractVendorAddressInfo']
    VendorContactInfo: Optional['SubcontractVendorContactInfo']


@dataclass
class SubcontractCustomAction(BaseDataClassModel):
    entity: Optional['Subcontract']
    parameters: Optional[Any]


@dataclass
class SubcontractDetail(BaseDataClassModel):
    Account: Optional['StringValue']
    AlternateID: Optional['StringValue']
    Amount: Optional['DecimalValue']
    BranchID: Optional['StringValue']
    Canceled: Optional['BooleanValue']
    Closed: Optional['BooleanValue']
    Completed: Optional['BooleanValue']
    CostCode: Optional['StringValue']
    Description: Optional['StringValue']
    DiscountAmount: Optional['DecimalValue']
    DiscountCode: Optional['StringValue']
    DiscountPct: Optional['DecimalValue']
    DiscountSequence: Optional['StringValue']
    ExtendedCost: Optional['DecimalValue']
    InventoryID: Optional['StringValue']
    LineDescription: Optional['StringValue']
    LineNbr: Optional['IntValue']
    ManualCost: Optional['BooleanValue']
    ManualDiscount: Optional['BooleanValue']
    OrderNbr: Optional['StringValue']
    OrderQty: Optional['DecimalValue']
    OrderType: Optional['StringValue']
    PrepaidAmount: Optional['DecimalValue']
    PrepaidQty: Optional['DecimalValue']
    Project: Optional['StringValue']
    Task: Optional['StringValue']
    Requested: Optional['DateTimeValue']
    RetainageAmount: Optional['DecimalValue']
    RetainagePct: Optional['DecimalValue']
    StartDate: Optional['DateTimeValue']
    Subaccount: Optional['StringValue']
    TaxCategory: Optional['StringValue']
    UnitCost: Optional['DecimalValue']
    UOM: Optional['StringValue']


@dataclass
class SubcontractTaxDetail(BaseDataClassModel):
    RetainedTax: Optional['DecimalValue']
    RetainedTaxable: Optional['DecimalValue']
    TaxableAmount: Optional['DecimalValue']
    TaxAmount: Optional['DecimalValue']
    TaxID: Optional['StringValue']
    TaxRate: Optional['DecimalValue']
    TaxType: Optional['StringValue']


@dataclass
class SubcontractVendorAddressInfo(BaseDataClassModel):
    AddressLine1: Optional['StringValue']
    AddressLine2: Optional['StringValue']
    City: Optional['StringValue']
    Country: Optional['StringValue']
    VendorAddressOverride: Optional['BooleanValue']
    PostalCode: Optional['StringValue']
    State: Optional['StringValue']


@dataclass
class SubcontractVendorContactInfo(BaseDataClassModel):
    AccountName: Optional['StringValue']
    Email: Optional['StringValue']
    JobTitle: Optional['StringValue']
    VendorContactOverride: Optional['BooleanValue']
    Phone: Optional['StringValue']


@dataclass
class SubmitExpenseClaim(BaseDataClassModel):
    entity: Optional['ExpenseClaim']


@dataclass
class SubmitExpenseReceipt(BaseDataClassModel):
    entity: Optional['ExpenseReceipt']


@dataclass
class SuspendProject(BaseDataClassModel):
    entity: Optional['Project']


@dataclass
class Task(BaseDataClassModel):
    Body: Optional['StringValue']
    Category: Optional['StringValue']
    CompletedAt: Optional['DateTimeValue']
    CompletionPercentage: Optional['IntValue']
    DueDate: Optional['DateTimeValue']
    Internal: Optional['BooleanValue']
    NoteID: Optional['GuidValue']
    Owner: Optional['StringValue']
    Parent: Optional['GuidValue']
    ParentSummary: Optional['StringValue']
    Priority: Optional['StringValue']
    RelatedActivities: List[Optional['ActivityDetail']]
    RelatedTasks: List[Optional['TaskRelatedTask']]
    Reminder: Optional['ReminderDetail']
    StartDate: Optional['DateTimeValue']
    Status: Optional['StringValue']
    Summary: Optional['StringValue']
    TimeActivity: Optional['TaskTimeActivity']
    WorkgroupID: Optional['StringValue']
    CreatedByID: Optional['StringValue']
    CreatedDateTime: Optional['DateTimeValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    RelatedEntityType: Optional['StringValue']
    RelatedEntityNoteID: Optional['GuidValue']
    RelatedEntityDescription: Optional['StringValue']


@dataclass
class TaskCustomAction(BaseDataClassModel):
    entity: Optional['Task']
    parameters: Optional[Any]


@dataclass
class TaskRelatedTask(BaseDataClassModel):
    CompletedAt: Optional['DateTimeValue']
    DueDate: Optional['DateTimeValue']
    RecordID: Optional['IntValue']
    StartDate: Optional['DateTimeValue']
    Status: Optional['StringValue']
    Subject: Optional['StringValue']


@dataclass
class TaskTimeActivity(BaseDataClassModel):
    BillableOvertime: Optional['StringValue']
    BillableTime: Optional['StringValue']
    CostCode: Optional['StringValue']
    Overtime: Optional['StringValue']
    Project: Optional['StringValue']
    ProjectTask: Optional['StringValue']
    TimeSpent: Optional['StringValue']


@dataclass
class Tax(BaseDataClassModel):
    CalculateOn: Optional['StringValue']
    CashDiscount: Optional['StringValue']
    CreatedDateTime: Optional['DateTimeValue']
    DeductibleVAT: Optional['BooleanValue']
    Description: Optional['StringValue']
    EnterFromTaxBill: Optional['BooleanValue']
    ExcludeFromTaxonTaxCalculation: Optional['BooleanValue']
    IncludeInVATExemptTotal: Optional['BooleanValue']
    IncludeInVATTaxableTotal: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    NotValidAfter: Optional['DateTimeValue']
    PendingVAT: Optional['BooleanValue']
    ReverseVAT: Optional['BooleanValue']
    StatisticalVAT: Optional['BooleanValue']
    TaxAgency: Optional['StringValue']
    TaxClaimableAccount: Optional['StringValue']
    TaxClaimableSubaccount: Optional['StringValue']
    TaxExpenseAccount: Optional['StringValue']
    TaxExpenseSubaccount: Optional['StringValue']
    TaxID: Optional['StringValue']
    TaxPayableAccount: Optional['StringValue']
    TaxPayableSubaccount: Optional['StringValue']
    TaxSchedule: List[Optional['TaxScheduleDetail']]
    TaxType: Optional['StringValue']
    Zones: List[Optional['TaxZoneDetail']]


@dataclass
class TaxAndReportingCA(BaseDataClassModel):
    ReportingType: Optional['StringValue']
    SupplementalIncome: Optional['BooleanValue']
    TaxDetailsCA: List[Optional['EarningCodeTaxDetailCA']]
    WageType: Optional['StringValue']


@dataclass
class TaxAndReportingUS(BaseDataClassModel):
    ReportingType: Optional['StringValue']
    SubjecttoTaxes: Optional['StringValue']
    TaxDetailsUS: List[Optional['EarningCodeTaxDetailUS']]
    WageType: Optional['StringValue']


@dataclass
class TaxCategory(BaseDataClassModel):
    Active: Optional['BooleanValue']
    CreatedDateTime: Optional['DateTimeValue']
    Description: Optional['StringValue']
    Details: List[Optional['TaxCategoryTaxDetail']]
    ExcludeListedTaxes: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    TaxCategoryID: Optional['StringValue']


@dataclass
class TaxCategoryCustomAction(BaseDataClassModel):
    entity: Optional['TaxCategory']
    parameters: Optional[Any]


@dataclass
class TaxCategoryTaxDetail(BaseDataClassModel):
    CalculateOn: Optional['StringValue']
    CashDiscount: Optional['StringValue']
    Description: Optional['StringValue']
    TaxCategory: Optional['StringValue']
    TaxID: Optional['StringValue']
    TaxType: Optional['StringValue']


@dataclass
class TaxCodeSetting(BaseDataClassModel):
    AdditionalInformation: Optional['StringValue']
    CompanyNotes: Optional['StringValue']
    FormBox: Optional['StringValue']
    Name: Optional['StringValue']
    Required: Optional['BooleanValue']
    UseDefault: Optional['BooleanValue']
    Value: Optional['StringValue']


@dataclass
class TaxCustomAction(BaseDataClassModel):
    entity: Optional['Tax']
    parameters: Optional[Any]


@dataclass
class TaxDetail(BaseDataClassModel):
    CustomerTaxZone: Optional['StringValue']
    IncludeInVATExemptTotal: Optional['BooleanValue']
    LineNbr: Optional['IntValue']
    OrderNbr: Optional['StringValue']
    OrderType: Optional['StringValue']
    PendingVAT: Optional['BooleanValue']
    RecordID: Optional['IntValue']
    ReverseVAT: Optional['BooleanValue']
    StatisticalVAT: Optional['BooleanValue']
    TaxableAmount: Optional['DecimalValue']
    TaxAmount: Optional['DecimalValue']
    TaxID: Optional['StringValue']
    TaxRate: Optional['DecimalValue']
    TaxType: Optional['StringValue']


@dataclass
class TaxReportingSettings(BaseDataClassModel):
    ReportingGroups: List[Optional['ReportingGroup']]
    TaxAgency: Optional['StringValue']


@dataclass
class TaxReportingSettingsCustomAction(BaseDataClassModel):
    entity: Optional['TaxReportingSettings']
    parameters: Optional[Any]


@dataclass
class TaxScheduleDetail(BaseDataClassModel):
    DeductibleTaxRate: Optional['DecimalValue']
    MaxTaxableAmount: Optional['DecimalValue']
    MinTaxableAmount: Optional['DecimalValue']
    ReportingGroup: Optional['StringValue']
    RevisionID: Optional['IntValue']
    StartDate: Optional['DateTimeValue']
    TaxID: Optional['StringValue']
    TaxRate: Optional['DecimalValue']


@dataclass
class TaxSettingDetail(BaseDataClassModel):
    AdditionalInformation: Optional['StringValue']
    CompanyNotes: Optional['StringValue']
    FormBox: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Name: Optional['StringValue']
    Required: Optional['BooleanValue']
    Setting: Optional['StringValue']
    State: Optional['StringValue']
    UseDefault: Optional['BooleanValue']
    UsedforGovernmentReporting: Optional['BooleanValue']
    UsedforTaxCalculation: Optional['BooleanValue']
    Value: Optional['StringValue']


@dataclass
class TaxSettingsCA(BaseDataClassModel):
    CodeType: Optional['StringValue']
    TaxDetailsCA: List[Optional['DeductionOrBenefitTaxDetailCA']]


@dataclass
class TaxSettingsUS(BaseDataClassModel):
    AllowSupplementalElection: Optional['BooleanValue']
    CodeType: Optional['StringValue']
    ImpactonTaxableWage: Optional['StringValue']
    TaxDetailsUS: List[Optional['DeductionOrBenefitTaxDetailUS']]


@dataclass
class TaxZone(BaseDataClassModel):
    ApplicableTaxes: List[Optional['TaxZoneApplicableTaxDetail']]
    CreatedDateTime: Optional['DateTimeValue']
    Description: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    TaxZoneID: Optional['StringValue']


@dataclass
class TaxZoneApplicableTaxDetail(BaseDataClassModel):
    TaxID: Optional['StringValue']


@dataclass
class TaxZoneCustomAction(BaseDataClassModel):
    entity: Optional['TaxZone']
    parameters: Optional[Any]


@dataclass
class TaxZoneDetail(BaseDataClassModel):
    DefaultTaxCategory: Optional['StringValue']
    Description: Optional['StringValue']
    TaxID: Optional['StringValue']
    TaxZoneID: Optional['StringValue']


@dataclass
class TaxesDecreasingApplWage(BaseDataClassModel):
    EmployeeTaxesDecreasingApplWageDetails: List[Optional['TaxesDecreasingApplWageDetail']]
    InclusionType: Optional['StringValue']


@dataclass
class TaxesDecreasingApplWageDetail(BaseDataClassModel):
    LastModifiedDateTime: Optional['DateTimeValue']
    TaxCategory: Optional['StringValue']
    TaxCode: Optional['StringValue']
    TaxName: Optional['StringValue']


@dataclass
class TemplateItemVendorDetail(BaseDataClassModel):
    RecordID: Optional['IntValue']
    VendorID: Optional['StringValue']
    VendorName: Optional['StringValue']
    Default: Optional['BooleanValue']


@dataclass
class TemplateItems(BaseDataClassModel):
    SalesUOM: Optional['StringValue']
    CurySpecificMSRP: Optional['DecimalValue']
    CurySpecificPrice: Optional['DecimalValue']
    ItemClass: Optional['StringValue']
    Availability: Optional['StringValue']
    Attributes: List[Optional['AttributeValue']]
    BaseUOM: Optional['StringValue']
    Categories: List[Optional['CategoryStockItem']]
    Content: Optional['StringValue']
    CurrentStdCost: Optional['DecimalValue']
    CustomURL: Optional['StringValue']
    DefaultIssueLocationID: Optional['StringValue']
    DefaultPrice: Optional['DecimalValue']
    Description: Optional['StringValue']
    DimensionWeight: Optional['DecimalValue']
    ExportToExternal: Optional['BooleanValue']
    FileURLs: List[Optional['InventoryFileUrls']]
    InventoryID: Optional['StringValue']
    IsStockItem: Optional['BooleanValue']
    ItemStatus: Optional['StringValue']
    LastModified: Optional['DateTimeValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Matrix: List[Optional['MatrixItems']]
    MetaDescription: Optional['StringValue']
    MSRP: Optional['DecimalValue']
    PageTitle: Optional['StringValue']
    SearchKeywords: Optional['StringValue']
    TaxCategory: Optional['StringValue']
    Visibility: Optional['StringValue']
    WeightUOM: Optional['StringValue']
    MetaKeywords: Optional['StringValue']
    RequireShipment: Optional['BooleanValue']
    NotAvailable: Optional['StringValue']
    VendorDetails: List[Optional['TemplateItemVendorDetail']]


@dataclass
class TemplateItemsCustomAction(BaseDataClassModel):
    entity: Optional['TemplateItems']
    parameters: Optional[Any]


@dataclass
class TimeActivity(BaseDataClassModel):
    Approver: Optional['StringValue']
    Billable: Optional['BooleanValue']
    BillableOvertime: Optional['StringValue']
    BillableTime: Optional['StringValue']
    CostCode: Optional['StringValue']
    EarningType: Optional['StringValue']
    Overtime: Optional['StringValue']
    Project: Optional['StringValue']
    ProjectTask: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    Released: Optional['BooleanValue']
    Status: Optional['StringValue']
    TimeSpent: Optional['StringValue']
    TrackTime: Optional['BooleanValue']


@dataclass
class TimeAndMaterial(BaseDataClassModel):
    AmountToInvoice: Optional['DecimalValue']
    BilledAmount: Optional['DecimalValue']
    BilledQty: Optional['DecimalValue']
    Branch: Optional['StringValue']
    CostCode: Optional['StringValue']
    Date: Optional['DateTimeValue']
    DeferralCode: Optional['StringValue']
    Description: Optional['StringValue']
    EmployeeID: Optional['StringValue']
    InventoryID: Optional['StringValue']
    MaxAvailableAmount: Optional['DecimalValue']
    MaxLimitAmount: Optional['DecimalValue']
    OverLimitAmount: Optional['DecimalValue']
    ProjectTaskID: Optional['StringValue']
    QtyToInvoice: Optional['DecimalValue']
    Retainage: Optional['DecimalValue']
    RetainageAmount: Optional['DecimalValue']
    SalesAccount: Optional['StringValue']
    SalesSubaccount: Optional['StringValue']
    Status: Optional['StringValue']
    TaxCategory: Optional['StringValue']
    UnitPrice: Optional['DecimalValue']
    UOM: Optional['StringValue']
    Vendor: Optional['StringValue']


@dataclass
class TimeEntry(BaseDataClassModel):
    ApprovalStatus: Optional['StringValue']
    Approver: Optional['StringValue']
    Billable: Optional['BooleanValue']
    BillableOvertime: Optional['StringValue']
    BillableTime: Optional['StringValue']
    CertifiedJob: Optional['BooleanValue']
    CostCode: Optional['StringValue']
    CostRate: Optional['DecimalValue']
    Date: Optional['DateTimeValue']
    EarningType: Optional['StringValue']
    Employee: Optional['StringValue']
    ExternalRefNbr: Optional['StringValue']
    LaborItem: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Overtime: Optional['StringValue']
    ProjectID: Optional['StringValue']
    ProjectTaskID: Optional['StringValue']
    Summary: Optional['StringValue']
    Time: Optional['DateTimeValue']
    TimeEntryID: Optional['GuidValue']
    TimeSpent: Optional['StringValue']
    UnionLocal: Optional['StringValue']
    WCCCode: Optional['StringValue']


@dataclass
class TimeEntryCustomAction(BaseDataClassModel):
    entity: Optional['TimeEntry']
    parameters: Optional[Any]


@dataclass
class Totals(BaseDataClassModel):
    DiscountTotal: Optional['DecimalValue']
    LineTotalAmount: Optional['DecimalValue']
    MiscTotalAmount: Optional['DecimalValue']
    TaxTotal: Optional['DecimalValue']
    UnbilledAmount: Optional['DecimalValue']
    UnbilledQty: Optional['DecimalValue']
    UnpaidBalance: Optional['DecimalValue']
    Freight: Optional['DecimalValue']
    FreightCost: Optional['DecimalValue']
    FreightCostIsuptodate: Optional['BooleanValue']
    FreightTaxCategory: Optional['StringValue']
    OrderVolume: Optional['DecimalValue']
    OrderWeight: Optional['DecimalValue']
    PackageWeight: Optional['DecimalValue']
    PremiumFreight: Optional['DecimalValue']
    OverrideFreightAmount: Optional['BooleanValue']


@dataclass
class TransferOrder(BaseDataClassModel):
    Date: Optional['DateTimeValue']
    Description: Optional['StringValue']
    Details: List[Optional['TransferOrderDetail']]
    ExternalRef: Optional['StringValue']
    FromWarehouseID: Optional['StringValue']
    Hold: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    PostPeriod: Optional['StringValue']
    ReferenceNbr: Optional['StringValue']
    Status: Optional['StringValue']
    TotalQty: Optional['DecimalValue']
    ToWarehouseID: Optional['StringValue']
    TransferType: Optional['StringValue']


@dataclass
class TransferOrderCustomAction(BaseDataClassModel):
    entity: Optional['TransferOrder']
    parameters: Optional[Any]


@dataclass
class TransferOrderDetail(BaseDataClassModel):
    Allocations: List[Optional['TransferOrderDetailAllocation']]
    CostCode: Optional['StringValue']
    Description: Optional['StringValue']
    ExpirationDate: Optional['DateTimeValue']
    FromLocationID: Optional['StringValue']
    InventoryID: Optional['StringValue']
    LineNbr: Optional['IntValue']
    LotSerialNbr: Optional['StringValue']
    Project: Optional['StringValue']
    ProjectTask: Optional['StringValue']
    Qty: Optional['DecimalValue']
    ReasonCode: Optional['StringValue']
    SpecialOrderNbr: Optional['StringValue']
    Subitem: Optional['StringValue']
    ToLocationID: Optional['StringValue']
    ToCostCode: Optional['StringValue']
    ToCostLayerType: Optional['StringValue']
    ToProject: Optional['StringValue']
    ToProjectTask: Optional['StringValue']
    ToSpecialOrderNbr: Optional['StringValue']
    UOM: Optional['StringValue']


@dataclass
class TransferOrderDetailAllocation(BaseDataClassModel):
    LocationID: Optional['StringValue']
    LotSerialNbr: Optional['StringValue']
    Qty: Optional['DecimalValue']
    SplitLineNumber: Optional['IntValue']
    Subitem: Optional['StringValue']
    ExpirationDate: Optional['DateTimeValue']


@dataclass
class UncloseAppointment(BaseDataClassModel):
    entity: Optional['Appointment']


@dataclass
class UncloseOrder(BaseDataClassModel):
    entity: Optional['ServiceOrder']


@dataclass
class UnionDeductionOrBenefitDetail(BaseDataClassModel):
    ContributionAmount: Optional['DecimalValue']
    ContributionCalculationMethod: Optional['StringValue']
    ContributionPercent: Optional['DecimalValue']
    ContributionType: Optional['StringValue']
    DeductionAmount: Optional['DecimalValue']
    DeductionAndBenefitCode: Optional['StringValue']
    DeductionCalculationMethod: Optional['StringValue']
    DeductionPercent: Optional['DecimalValue']
    Description: Optional['StringValue']
    EffectiveDate: Optional['DateTimeValue']
    LaborItem: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']


@dataclass
class UnionEarningRateDetail(BaseDataClassModel):
    Description: Optional['StringValue']
    EffectiveDate: Optional['DateTimeValue']
    LaborItem: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    WageRate: Optional['DecimalValue']


@dataclass
class UnionLocal(BaseDataClassModel):
    Active: Optional['BooleanValue']
    Description: Optional['StringValue']
    UnionLocalID: Optional['StringValue']


@dataclass
class UnionLocalCustomAction(BaseDataClassModel):
    entity: Optional['UnionLocal']
    parameters: Optional[Any]


@dataclass
class Units(BaseDataClassModel):
    ConversionFactor: Optional['DecimalValue']
    CreatedDateTime: Optional['DateTimeValue']
    FromUOM: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    MultiplyOrDivide: Optional['StringValue']
    ToUOM: Optional['StringValue']


@dataclass
class UnitsOfMeasure(BaseDataClassModel):
    UnitID: Optional['StringValue']
    Description: Optional['StringValue']
    L3Code: Optional['StringValue']
    Conversion: List[Optional['Units']]


@dataclass
class UnitsOfMeasureCustomAction(BaseDataClassModel):
    entity: Optional['UnitsOfMeasure']
    parameters: Optional[Any]


@dataclass
class UnlockProjectBudget(BaseDataClassModel):
    entity: Optional['Project']


@dataclass
class UnlockProjectCommitments(BaseDataClassModel):
    entity: Optional['Project']


@dataclass
class UpdateDiscounts(BaseDataClassModel):
    entity: Optional['Discount']
    parameters: Optional[Any]


@dataclass
class UpdateIN(BaseDataClassModel):
    entity: Optional['Shipment']


@dataclass
class UpdateStandardCostNonStockItem(BaseDataClassModel):
    entity: Optional['NonStockItem']


@dataclass
class UpdateStandardCostStockItem(BaseDataClassModel):
    entity: Optional['StockItem']


@dataclass
class ValidateBusinessAccountAddresses(BaseDataClassModel):
    entity: Optional['BusinessAccount']


@dataclass
class ValidateContactAddress(BaseDataClassModel):
    entity: Optional['Contact']


@dataclass
class ValidateLeadAddress(BaseDataClassModel):
    entity: Optional['Lead']


@dataclass
class ValidateProjectBalance(BaseDataClassModel):
    entity: Optional['Project']


@dataclass
class Vendor(BaseDataClassModel):
    AccountRef: Optional['StringValue']
    APAccount: Optional['StringValue']
    APSubaccount: Optional['StringValue']
    Attributes: List[Optional['AttributeValue']]
    CashAccount: Optional['StringValue']
    Contacts: List[Optional['CustomerContact']]
    CreatedDateTime: Optional['DateTimeValue']
    CurrencyID: Optional['StringValue']
    CurrencyRateType: Optional['StringValue']
    EnableCurrencyOverride: Optional['BooleanValue']
    EnableRateOverride: Optional['BooleanValue']
    F1099Box: Optional['StringValue']
    F1099Vendor: Optional['BooleanValue']
    FATCA: Optional['BooleanValue']
    FOBPoint: Optional['StringValue']
    ForeignEntity: Optional['BooleanValue']
    LandedCostVendor: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    LeadTimedays: Optional['ShortValue']
    LegalName: Optional['StringValue']
    LocationName: Optional['StringValue']
    MainContact: Optional['Contact']
    MaxReceipt: Optional['DecimalValue']
    MinReceipt: Optional['DecimalValue']
    ParentAccount: Optional['StringValue']
    PaymentBy: Optional['StringValue']
    PaymentInstructions: List[Optional['BusinessAccountPaymentInstructionDetail']]
    PaymentLeadTimedays: Optional['ShortValue']
    PaymentMethod: Optional['StringValue']
    PaySeparately: Optional['BooleanValue']
    PrimaryContact: Optional['Contact']
    PrintOrders: Optional['BooleanValue']
    ReceiptAction: Optional['StringValue']
    ReceivingBranch: Optional['StringValue']
    RemittanceAddressOverride: Optional['BooleanValue']
    RemittanceContact: Optional['Contact']
    RemittanceContactOverride: Optional['BooleanValue']
    SendOrdersbyEmail: Optional['BooleanValue']
    ShippingContactOverride: Optional['BooleanValue']
    ShippingAddressOverride: Optional['BooleanValue']
    ShippingContact: Optional['Contact']
    ShippingTerms: Optional['StringValue']
    ShipVia: Optional['StringValue']
    Status: Optional['StringValue']
    TaxCalculationMode: Optional['StringValue']
    TaxRegistrationID: Optional['StringValue']
    TaxZone: Optional['StringValue']
    Terms: Optional['StringValue']
    ThresholdReceipt: Optional['DecimalValue']
    VendorClass: Optional['StringValue']
    VendorID: Optional['StringValue']
    VendorIsLaborUnion: Optional['BooleanValue']
    VendorIsTaxAgency: Optional['BooleanValue']
    VendorName: Optional['StringValue']
    Warehouse: Optional['StringValue']


@dataclass
class VendorClass(BaseDataClassModel):
    Attributes: List[Optional['BusinessAccountClassAttributeDetail']]
    ClassID: Optional['StringValue']
    CreatedDateTime: Optional['DateTimeValue']
    Description: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']


@dataclass
class VendorClassCustomAction(BaseDataClassModel):
    entity: Optional['VendorClass']
    parameters: Optional[Any]


@dataclass
class VendorCustomAction(BaseDataClassModel):
    entity: Optional['Vendor']
    parameters: Optional[Any]


@dataclass
class VendorPriceDetail(BaseDataClassModel):
    BreakQty: Optional['DecimalValue']
    CreatedDateTime: Optional['DateTimeValue']
    CurrencyID: Optional['StringValue']
    Description: Optional['StringValue']
    EffectiveDate: Optional['DateTimeValue']
    ExpirationDate: Optional['DateTimeValue']
    InventoryID: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Price: Optional['DecimalValue']
    Promotional: Optional['BooleanValue']
    RecordID: Optional['IntValue']
    UOM: Optional['StringValue']
    Vendor: Optional['StringValue']
    VendorName: Optional['StringValue']


@dataclass
class VendorPriceWorksheet(BaseDataClassModel):
    CreatedDateTime: Optional['DateTimeValue']
    Description: Optional['StringValue']
    EffectiveDate: Optional['DateTimeValue']
    ExpirationDate: Optional['DateTimeValue']
    Hold: Optional['BooleanValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    OverwriteOverlappingPrices: Optional['BooleanValue']
    Promotional: Optional['BooleanValue']
    ReferenceNbr: Optional['StringValue']
    Status: Optional['StringValue']
    VendorSalesPrices: List[Optional['VendorPriceWorksheetDetail']]


@dataclass
class VendorPriceWorksheetCustomAction(BaseDataClassModel):
    entity: Optional['VendorPriceWorksheet']
    parameters: Optional[Any]


@dataclass
class VendorPriceWorksheetDetail(BaseDataClassModel):
    BreakQty: Optional['DecimalValue']
    CurrencyID: Optional['StringValue']
    Description: Optional['StringValue']
    InventoryID: Optional['StringValue']
    LineID: Optional['IntValue']
    PendingPrice: Optional['DecimalValue']
    ReferenceNbr: Optional['StringValue']
    SourcePrice: Optional['DecimalValue']
    Tax: Optional['StringValue']
    UOM: Optional['StringValue']
    Vendor: Optional['StringValue']


@dataclass
class VendorPricesInquiry(BaseDataClassModel):
    InventoryID: Optional['StringValue']
    ItemClass: Optional['StringValue']
    ProductManager: Optional['StringValue']
    ProductWorkgroup: Optional['StringValue']
    Vendor: Optional['StringValue']
    VendorPriceDetails: List[Optional['VendorPriceDetail']]


@dataclass
class VendorPricesInquiryCustomAction(BaseDataClassModel):
    entity: Optional['VendorPricesInquiry']
    parameters: Optional[Any]


@dataclass
class VisibilitySettings(BaseDataClassModel):
    AP: Optional['BooleanValue']
    AR: Optional['BooleanValue']
    CA: Optional['BooleanValue']
    CRM: Optional['BooleanValue']
    Expenses: Optional['BooleanValue']
    GL: Optional['BooleanValue']
    IN: Optional['BooleanValue']
    PO: Optional['BooleanValue']
    SO: Optional['BooleanValue']
    TimeEntries: Optional['BooleanValue']


@dataclass
class VoidCardPayment(BaseDataClassModel):
    entity: Optional['Payment']
    parameters: Optional[Any]


@dataclass
class VoidCheck(BaseDataClassModel):
    entity: Optional['Check']


@dataclass
class VoidPayment(BaseDataClassModel):
    entity: Optional['Payment']


@dataclass
class WCCCode(BaseDataClassModel):
    Active: Optional['BooleanValue']
    Description: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    WCCCode: Optional['StringValue']
    WCCCodeCostCodeSources: List[Optional['WCCCodeCostCodeSource']]
    WCCCodeLaborItemSources: List[Optional['WCCCodeLaborItemSource']]
    WCCCodeMaxInsurableWages: List[Optional['WCCCodeMaxInsurableWage']]
    WCCCodeProjectSources: List[Optional['WCCCodeProjectSource']]
    WCCCodeRates: List[Optional['WCCCodeRate']]


@dataclass
class WCCCodeCostCodeSource(BaseDataClassModel):
    CostCodeFrom: Optional['StringValue']
    CostCodeTo: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    LineNbr: Optional['IntValue']
    WorkCodeID: Optional['StringValue']


@dataclass
class WCCCodeLaborItemSource(BaseDataClassModel):
    LaborItem: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    WorkCodeID: Optional['StringValue']


@dataclass
class WCCCodeMaxInsurableWage(BaseDataClassModel):
    DeductionandBenefitCode: Optional['StringValue']
    EffectiveDate: Optional['DateTimeValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    State: Optional['StringValue']
    Wage: Optional['DecimalValue']
    WCCode: Optional['StringValue']


@dataclass
class WCCCodeMaxInsurableWageDetail(BaseDataClassModel):
    DeductionandBenefitCode: Optional['StringValue']
    EffectiveDate: Optional['DateTimeValue']
    Wage: Optional['DecimalValue']


@dataclass
class WCCCodeProjectSource(BaseDataClassModel):
    LastModifiedDateTime: Optional['DateTimeValue']
    LineNbr: Optional['IntValue']
    Project: Optional['StringValue']
    ProjectTask: Optional['StringValue']
    WorkCodeID: Optional['StringValue']


@dataclass
class WCCCodeRate(BaseDataClassModel):
    Active: Optional['BooleanValue']
    BenefitCalculationMethod: Optional['StringValue']
    BenefitRate: Optional['DecimalValue']
    Branch: Optional['StringValue']
    DeductionCalculationMethod: Optional['StringValue']
    DeductionCode: Optional['StringValue']
    DeductionRate: Optional['DecimalValue']
    EffectiveDate: Optional['DateTimeValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    RecordID: Optional['IntValue']
    State: Optional['StringValue']
    WorkCodeID: Optional['StringValue']


@dataclass
class WCCCodeRateDetail(BaseDataClassModel):
    Active: Optional['GuidValue']
    BenefitRate: Optional['DecimalValue']
    Branch: Optional['StringValue']
    DeductionRate: Optional['DecimalValue']
    Description: Optional['StringValue']
    EffectiveDate: Optional['DateTimeValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    WCCCode: Optional['StringValue']
    WCCCodeMaxInsurableWages: List[Optional['WCCCodeMaxInsurableWageDetail']]


@dataclass
class Warehouse(BaseDataClassModel):
    Active: Optional['BooleanValue']
    COGSExpenseAccount: Optional['StringValue']
    COGSExpenseSubaccount: Optional['StringValue']
    Description: Optional['StringValue']
    DiscountAccount: Optional['StringValue']
    DiscountSubaccount: Optional['StringValue']
    DropShipLocationID: Optional['StringValue']
    FreightChargeAccount: Optional['StringValue']
    FreightChargeSubaccount: Optional['StringValue']
    InventoryAccount: Optional['StringValue']
    InventorySubaccount: Optional['StringValue']
    LandedCostVarianceAccount: Optional['StringValue']
    LandedCostVarianceSubaccount: Optional['StringValue']
    LastModifiedDateTime: Optional['DateTimeValue']
    Locations: List[Optional['WarehouseLocation']]
    MiscChargeAccount: Optional['StringValue']
    MiscChargeSubaccount: Optional['StringValue']
    NonStockPickingLocationID: Optional['StringValue']
    OverrideInventoryAccountSubaccount: Optional['BooleanValue']
    POAccrualAccount: Optional['StringValue']
    POAccrualSubaccount: Optional['StringValue']
    PurchasePriceVarianceAccount: Optional['StringValue']
    PurchasePriceVarianceSubaccount: Optional['StringValue']
    ReasonCodeSubaccount: Optional['StringValue']
    ReceivingLocationID: Optional['StringValue']
    RMALocationID: Optional['StringValue']
    SalesAccount: Optional['StringValue']
    SalesSubaccount: Optional['StringValue']
    ShippingLocationID: Optional['StringValue']
    StandardCostRevaluationAccount: Optional['StringValue']
    StandardCostRevaluationSubaccount: Optional['StringValue']
    StandardCostVarianceAccount: Optional['StringValue']
    StandardCostVarianceSubaccount: Optional['StringValue']
    UseItemDefaultLocationForPicking: Optional['BooleanValue']
    WarehouseID: Optional['StringValue']


@dataclass
class WarehouseCustomAction(BaseDataClassModel):
    entity: Optional['Warehouse']
    parameters: Optional[Any]


@dataclass
class WarehouseLocation(BaseDataClassModel):
    Active: Optional['BooleanValue']
    AssemblyAllowed: Optional['BooleanValue']
    Description: Optional['StringValue']
    LocationID: Optional['StringValue']
    PickPriority: Optional['ShortValue']
    ReceiptsAllowed: Optional['BooleanValue']
    SalesAllowed: Optional['BooleanValue']
    TransfersAllowed: Optional['BooleanValue']


@dataclass
class WorkCalendar(BaseDataClassModel):
    CalendarExceptions: List[Optional['WorkCalendarExceptionDetail']]
    CalendarSettings: Optional['CalendarSettings']
    Description: Optional['StringValue']
    TimeZone: Optional['StringValue']
    WorkCalendarID: Optional['StringValue']


@dataclass
class WorkCalendarCustomAction(BaseDataClassModel):
    entity: Optional['WorkCalendar']
    parameters: Optional[Any]


@dataclass
class WorkCalendarExceptionDetail(BaseDataClassModel):
    Date: Optional['DateTimeValue']
    DayOfWeek: Optional['StringValue']
    Description: Optional['StringValue']
    EndTime: Optional['DateTimeValue']
    StartTime: Optional['DateTimeValue']
    UnpaidBreakTime: Optional['StringValue']
    WorkDay: Optional['BooleanValue']


@dataclass
class WorkClassCompensationCode(BaseDataClassModel):
    Active: Optional['BooleanValue']
    CostCodeFrom: Optional['StringValue']
    CostCodeTo: Optional['StringValue']
    Description: Optional['StringValue']
    WCCCode: Optional['StringValue']


@dataclass
class WorkClassCompensationCodeCustomAction(BaseDataClassModel):
    entity: Optional['WorkClassCompensationCode']
    parameters: Optional[Any]


@dataclass
class WorkLocation(BaseDataClassModel):
    Active: Optional['BooleanValue']
    AddressInfo: Optional['Address']
    LastModifiedDateTime: Optional['DateTimeValue']
    UseAddressfromBranchID: Optional['StringValue']
    WorkLocationID: Optional['StringValue']
    WorkLocationName: Optional['StringValue']


@dataclass
class WorkLocationCustomAction(BaseDataClassModel):
    entity: Optional['WorkLocation']
    parameters: Optional[Any]

