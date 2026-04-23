"""
משמש לנתונים ההסטוריים
הגדרת מבנה הטבלאות למסד הנתונים
"""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, BigInteger, Index, UniqueConstraint, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


# ten_years_back_data schema

class HistoricalTradeData(Base):
    """
    טבלה מרכזית לשמירת נתוני מסחר
    מבוססת על שדות ה-result מה-API
    מאונדקסת גם לפי תאריך וגם לפי ניירות ערך לביצועים מיטביים
    """
    __tablename__ = 'trade_data'
    __table_args__ = (
        # אינדקס ייחודי למניעת כפילויות - אותו ניירות ערך באותו תאריך
        UniqueConstraint('security_id', 'trade_date', name='uq_security_date'),

        # אינדקס לשליפה מהירה לפי תאריך
        Index('idx_trade_date', 'trade_date'),

        # אינדקס לשליפה מהירה לפי ניירות ערך
        Index('idx_security_id', 'security_id'),

        # אינדקס משולב לשליפה לפי ניירות ערך עם סידור לפי תאריך
        Index('idx_security_date', 'security_id', 'trade_date'),

        # אינדקס לשליפה לפי סמל
        Index('idx_symbol', 'symbol'),

        # הגדרת הסכמה
        {'schema': 'ten_years_back_data'}
    )

    # מפתח ראשי
    id = Column(Integer, primary_key=True, autoincrement=True)

    # שדות מה-JSON API
    trade_date = Column(Date, nullable=False, comment='תאריך המסחר בפורמט yyyy-mm-dd')
    first_trading_date = Column(Date, nullable=True, comment='תאריך מסחר ראשון')
    isin = Column(String(50), nullable=True, comment='International Security Identification Number')
    change = Column(Float, nullable=True, comment='שינוי במחיר')
    security_id = Column(BigInteger, nullable=False, comment='מזהה ניירות הערך')
    turnover = Column(BigInteger, nullable=True, comment='מחזור מסחר')
    closing_price = Column(Float, nullable=True, comment='מחיר סגירה')
    base_price = Column(Float, nullable=True, comment='מחיר בסיס')
    opening_price = Column(Float, nullable=True, comment='מחיר פתיחה')
    high = Column(Float, nullable=True, comment='מחיר גבוה')
    low = Column(Float, nullable=True, comment='מחיר נמוך')
    change_value = Column(Float, nullable=True, comment='ערך השינוי')
    transactions_number = Column(BigInteger, nullable=True, comment='מספר עסקאות')
    volume = Column(BigInteger, nullable=True, comment='נפח מסחר')
    market_cap = Column(BigInteger, nullable=True, comment='שווי שוק')
    min_cont_phase_amount = Column(BigInteger, nullable=True, comment='סכום מינימום לשלב רציף')
    listed_capital = Column(BigInteger, nullable=True, comment='הון רשום למסחר')
    adjusted_closing_price = Column(Float, nullable=True, comment='מחיר סגירה מתואם')
    ex_code = Column(Integer, nullable=True, comment='קוד ex')
    adjustment_coefficient = Column(Float, nullable=True, comment='מקדם התאמה')
    symbol = Column(String(50), nullable=True, comment='סמל ניירות הערך')
    market_type = Column(String(50), nullable=True, comment='סוג שוק')

    # עמודת תאריך עדכון
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='תאריך עדכון הרשומה')

    def __repr__(self):
        return f"<TradeData(security_id={self.security_id}, trade_date={self.trade_date}, symbol={self.symbol})>"


class HistoricalExCode(Base):
    """
    טבלת קודי EX (Ex Codes) - טבלת reference
    מכילה את רשימת קודי ה-EX עם התיאור שלהם
    """
    __tablename__ = 'ex_code'
    __table_args__ = (
        # אינדקס לשליפה מהירה לפי סוג
        Index('idx_ex_code_type', 'ex_code_type'),

        # הגדרת הסכמה
        {'schema': 'ten_years_back_data'}
    )

    # מפתח ראשי
    id = Column(Integer, primary_key=True, autoincrement=True)

    # שדות מה-JSON API
    ex_code = Column(Integer, nullable=False, unique=True, comment='מספר קוד EX')
    ex_code_type = Column(String(50), nullable=True, comment='סוג קוד EX')
    ex_code_description = Column(String(200), nullable=True, comment='תיאור קוד EX')

    # עמודת תאריך עדכון
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='תאריך עדכון הרשומה')

    def __repr__(self):
        return f"<ExCode(ex_code={self.ex_code}, type={self.ex_code_type}, description={self.ex_code_description})>"

# stg schema

class StgTradeData(Base):
    """
    Table for storing current daily trading data (last 7 days)
    Based on API result fields
    Indexed by both date and security for optimal performance
    """
    __tablename__ = 'trade_data_current'
    __table_args__ = (
        # Unique index to prevent duplicates - same security on same date
        UniqueConstraint('security_id', 'trade_date', name='uq_current_security_date'),

        # Index for fast retrieval by date
        Index('idx_current_trade_date', 'trade_date'),

        # Index for fast retrieval by security
        Index('idx_current_security_id', 'security_id'),

        # Combined index for retrieval by security with date ordering
        Index('idx_current_security_date', 'security_id', 'trade_date'),

        # Index for retrieval by symbol
        Index('idx_current_symbol', 'symbol'),

        # Schema definition
        {'schema': 'stg'}
    )

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Fields from JSON API
    trade_date = Column(Date, nullable=False, comment='Trading date in yyyy-mm-dd format')
    first_trading_date = Column(Date, nullable=True, comment='First trading date')
    isin = Column(String(50), nullable=True, comment='International Security Identification Number')
    change = Column(Float, nullable=True, comment='Price change')
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    turnover = Column(BigInteger, nullable=True, comment='Trading turnover')
    closing_price = Column(Float, nullable=True, comment='Closing price')
    base_price = Column(Float, nullable=True, comment='Base price')
    opening_price = Column(Float, nullable=True, comment='Opening price')
    high = Column(Float, nullable=True, comment='High price')
    low = Column(Float, nullable=True, comment='Low price')
    change_value = Column(Float, nullable=True, comment='Change value')
    transactions_number = Column(BigInteger, nullable=True, comment='Number of transactions')
    volume = Column(BigInteger, nullable=True, comment='Trading volume')
    market_cap = Column(BigInteger, nullable=True, comment='Market capitalization')
    min_cont_phase_amount = Column(BigInteger, nullable=True, comment='Minimum continuous phase amount')
    listed_capital = Column(BigInteger, nullable=True, comment='Listed capital')
    adjusted_closing_price = Column(Float, nullable=True, comment='Adjusted closing price')
    ex_code = Column(Integer, nullable=True, comment='Ex code')
    adjustment_coefficient = Column(Float, nullable=True, comment='Adjustment coefficient')
    symbol = Column(String(50), nullable=True, comment='Security symbol')
    market_type = Column(String(50), nullable=True, comment='Market type')

    # Update timestamp column
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<TradeDataCurrent(security_id={self.security_id}, trade_date={self.trade_date}, symbol={self.symbol})>"


class StgExCode(Base):
    """
    EX Codes reference table for current daily data
    Contains list of EX codes with their descriptions
    """
    __tablename__ = 'ex_code_current'
    __table_args__ = (
        # Index for fast retrieval by type
        Index('idx_current_ex_code_type', 'ex_code_type'),

        # Schema definition
        {'schema': 'stg'}
    )

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Fields from JSON API
    ex_code = Column(Integer, nullable=False, unique=True, comment='EX code number')
    ex_code_type = Column(String(50), nullable=True, comment='EX code type')
    ex_code_description = Column(String(200), nullable=True, comment='EX code description')

    # Update timestamp column
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<ExCodeCurrent(ex_code={self.ex_code}, type={self.ex_code_type}, description={self.ex_code_description})>"

# core schema

class TradeData(Base):
    """
    Table for storing current daily trading data (last 7 days)
    Based on API result fields
    Indexed by both date and security for optimal performance
    """
    __tablename__ = 'trade_data'
    __table_args__ = (
        # Unique index to prevent duplicates - same security on same date
        UniqueConstraint('security_id', 'trade_date', name='uq_security_date'),

        # Index for fast retrieval by date
        Index('idx_trade_date', 'trade_date'),

        # Index for fast retrieval by security
        Index('idx_security_id', 'security_id'),

        # Combined index for retrieval by security with date ordering
        Index('idx_security_date', 'security_id', 'trade_date'),

        # Index for retrieval by symbol
        Index('idx_symbol', 'symbol'),

        # Schema definition
        {'schema': 'core'}
    )

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Fields from JSON API
    trade_date = Column(Date, nullable=False, comment='Trading date in yyyy-mm-dd format')
    first_trading_date = Column(Date, nullable=True, comment='First trading date')
    isin = Column(String(50), nullable=True, comment='International Security Identification Number')
    change = Column(Float, nullable=True, comment='Price change')
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    turnover = Column(BigInteger, nullable=True, comment='Trading turnover')
    closing_price = Column(Float, nullable=True, comment='Closing price')
    base_price = Column(Float, nullable=True, comment='Base price')
    opening_price = Column(Float, nullable=True, comment='Opening price')
    high = Column(Float, nullable=True, comment='High price')
    low = Column(Float, nullable=True, comment='Low price')
    change_value = Column(Float, nullable=True, comment='Change value')
    transactions_number = Column(BigInteger, nullable=True, comment='Number of transactions')
    volume = Column(BigInteger, nullable=True, comment='Trading volume')
    market_cap = Column(BigInteger, nullable=True, comment='Market capitalization')
    min_cont_phase_amount = Column(BigInteger, nullable=True, comment='Minimum continuous phase amount')
    listed_capital = Column(BigInteger, nullable=True, comment='Listed capital')
    adjusted_closing_price = Column(Float, nullable=True, comment='Adjusted closing price')
    ex_code = Column(Integer, nullable=True, comment='Ex code')
    adjustment_coefficient = Column(Float, nullable=True, comment='Adjustment coefficient')
    symbol = Column(String(50), nullable=True, comment='Security symbol')
    market_type = Column(String(50), nullable=True, comment='Market type')

    # Update timestamp column
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<TradeData(security_id={self.security_id}, trade_date={self.trade_date}, symbol={self.symbol})>"


class CoreExCode(Base):
    """
    EX Codes reference table for current daily data
    Contains list of EX codes with their descriptions
    """
    __tablename__ = 'ex_code'
    __table_args__ = (
        # Index for fast retrieval by type
        Index('idx_ex_code_type', 'ex_code_type'),

        # Schema definition
        {'schema': 'core'}
    )

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Fields from JSON API
    ex_code = Column(Integer, nullable=False, unique=True, comment='EX code number')
    ex_code_type = Column(String(50), nullable=True, comment='EX code type')
    ex_code_description = Column(String(200), nullable=True, comment='EX code description')

    # Update timestamp column
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<ExCode(ex_code={self.ex_code}, type={self.ex_code_type}, description={self.ex_code_description})>"

# New basic entities tables

# stg schema - Traded Securities List
class StgTradedSecuritiesList(Base):
    """
    Staging table for traded securities list
    """
    __tablename__ = 'traded_securities_list'
    __table_args__ = (
        UniqueConstraint('security_id', 'date', name='uq_traded_security_date'),
        Index('idx_traded_security_id', 'security_id'),
        Index('idx_traded_symbol', 'symbol'),
        Index('idx_traded_date', 'date'),
        Index('idx_traded_isin', 'isin'),
        {'schema': 'stg'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    security_full_type_code = Column(String(50), nullable=True, comment='Security full type code')
    isin = Column(String(50), nullable=True, comment='International Security Identification Number')
    security_name = Column(String(200), nullable=True, comment='Security name')
    symbol = Column(String(50), nullable=True, comment='Security symbol')
    company_super_sector = Column(String(200), nullable=True, comment='Company super sector')
    company_sector = Column(String(200), nullable=True, comment='Company sector')
    company_sub_sector = Column(String(200), nullable=True, comment='Company sub sector')
    security_is_included_in_continuous_indices = Column(JSONB, nullable=True, comment='Security indices (array of arrays)')
    corporate_id = Column(String(50), nullable=True, comment='Corporate ID')
    issuer_id = Column(BigInteger, nullable=True, comment='Issuer ID')
    company_name = Column(String(200), nullable=True, comment='Company name')
    date = Column(Date, nullable=False, comment='Date of the list')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<StgTradedSecuritiesList(security_id={self.security_id}, date={self.date}, symbol={self.symbol})>"


# core schema - Traded Securities List
class CoreTradedSecuritiesList(Base):
    """
    Core table for traded securities list
    """
    __tablename__ = 'traded_securities_list'
    __table_args__ = (
        UniqueConstraint('security_id', 'date', name='uq_traded_security_date'),
        Index('idx_traded_security_id', 'security_id'),
        Index('idx_traded_symbol', 'symbol'),
        Index('idx_traded_date', 'date'),
        Index('idx_traded_isin', 'isin'),
        {'schema': 'core'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    security_full_type_code = Column(String(50), nullable=True, comment='Security full type code')
    isin = Column(String(50), nullable=True, comment='International Security Identification Number')
    security_name = Column(String(200), nullable=True, comment='Security name')
    symbol = Column(String(50), nullable=True, comment='Security symbol')
    company_super_sector = Column(String(200), nullable=True, comment='Company super sector')
    company_sector = Column(String(200), nullable=True, comment='Company sector')
    company_sub_sector = Column(String(200), nullable=True, comment='Company sub sector')
    security_is_included_in_continuous_indices = Column(JSONB, nullable=True, comment='Security indices (array of arrays)')
    corporate_id = Column(String(50), nullable=True, comment='Corporate ID')
    issuer_id = Column(BigInteger, nullable=True, comment='Issuer ID')
    company_name = Column(String(200), nullable=True, comment='Company name')
    date = Column(Date, nullable=False, comment='Date of the list')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<CoreTradedSecuritiesList(security_id={self.security_id}, date={self.date}, symbol={self.symbol})>"


# stg schema - Delisted Securities List
class StgDelistedSecuritiesList(Base):
    """
    Staging table for delisted securities list
    """
    __tablename__ = 'delisted_securities_list'
    __table_args__ = (
        UniqueConstraint('security_id', 'date', name='uq_delisted_security_date'),
        Index('idx_delisted_security_id', 'security_id'),
        Index('idx_delisted_symbol', 'symbol'),
        Index('idx_delisted_date', 'date'),
        Index('idx_delisted_date_last_trade', 'date_last_trade'),
        {'schema': 'stg'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    security_name = Column(String(200), nullable=True, comment='Security name')
    symbol = Column(String(50), nullable=True, comment='Security symbol')
    date_last_trade = Column(Date, nullable=True, comment='Date of last trade')
    date = Column(Date, nullable=False, comment='Date (year/month) when delisted')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<StgDelistedSecuritiesList(security_id={self.security_id}, date={self.date}, symbol={self.symbol})>"


# core schema - Delisted Securities List
class CoreDelistedSecuritiesList(Base):
    """
    Core table for delisted securities list
    """
    __tablename__ = 'delisted_securities_list'
    __table_args__ = (
        UniqueConstraint('security_id', 'date', name='uq_delisted_security_date'),
        Index('idx_delisted_security_id', 'security_id'),
        Index('idx_delisted_symbol', 'symbol'),
        Index('idx_delisted_date', 'date'),
        Index('idx_delisted_date_last_trade', 'date_last_trade'),
        {'schema': 'core'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    security_name = Column(String(200), nullable=True, comment='Security name')
    symbol = Column(String(50), nullable=True, comment='Security symbol')
    date_last_trade = Column(Date, nullable=True, comment='Date of last trade')
    date = Column(Date, nullable=False, comment='Date (year/month) when delisted')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<CoreDelistedSecuritiesList(security_id={self.security_id}, date={self.date}, symbol={self.symbol})>"


# stg schema - Companies List
class StgCompaniesList(Base):
    """
    Staging table for companies list
    """
    __tablename__ = 'companies_list'
    __table_args__ = (
        UniqueConstraint('issuer_id', name='uq_companies_issuer_id'),
        Index('idx_companies_issuer_id', 'issuer_id'),
        Index('idx_companies_corporate_id', 'corporate_id'),
        Index('idx_companies_name', 'company_name'),
        {'schema': 'stg'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(200), nullable=True, comment='Company name')
    company_full_name = Column(String(500), nullable=True, comment='Company full name')
    tase_sector = Column(String(500), nullable=True, comment='TASE sector')
    issuer_id = Column(BigInteger, nullable=False, unique=True, comment='Issuer ID')
    corporate_id = Column(String(50), nullable=True, comment='Corporate ID')
    is_dual = Column(Boolean, nullable=True, comment='Is dual listing')
    extraction_date = Column(Date, nullable=False, comment='Date when data was extracted')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<StgCompaniesList(issuer_id={self.issuer_id}, company_name={self.company_name})>"


# core schema - Companies List
class CoreCompaniesList(Base):
    """
    Core table for companies list
    """
    __tablename__ = 'companies_list'
    __table_args__ = (
        UniqueConstraint('issuer_id', name='uq_companies_issuer_id'),
        Index('idx_companies_issuer_id', 'issuer_id'),
        Index('idx_companies_corporate_id', 'corporate_id'),
        Index('idx_companies_name', 'company_name'),
        {'schema': 'core'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(200), nullable=True, comment='Company name')
    company_full_name = Column(String(500), nullable=True, comment='Company full name')
    tase_sector = Column(String(500), nullable=True, comment='TASE sector')
    issuer_id = Column(BigInteger, nullable=False, unique=True, comment='Issuer ID')
    corporate_id = Column(String(50), nullable=True, comment='Corporate ID')
    is_dual = Column(Boolean, nullable=True, comment='Is dual listing')
    extraction_date = Column(Date, nullable=False, comment='Date when data was extracted')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<CoreCompaniesList(issuer_id={self.issuer_id}, company_name={self.company_name})>"


# stg schema - Illiquid Maintenance and Suspension List
class StgIlliquidMaintenanceSuspensionList(Base):
    """
    Staging table for illiquid maintenance and suspension list
    """
    __tablename__ = 'illiquid_maintenance_suspension_list'
    __table_args__ = (
        UniqueConstraint('security_id', 'status_date', 'list_type_id', name='uq_illiquid_security_status'),
        Index('idx_illiquid_security_id', 'security_id'),
        Index('idx_illiquid_list_type_id', 'list_type_id'),
        Index('idx_illiquid_status_date', 'status_date'),
        {'schema': 'stg'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    list_type_id = Column(String(50), nullable=True, comment='List type ID')
    status_date = Column(Date, nullable=False, comment='Status date')
    extraction_date = Column(Date, nullable=False, comment='Date when data was extracted')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<StgIlliquidMaintenanceSuspensionList(security_id={self.security_id}, status_date={self.status_date})>"


# core schema - Illiquid Maintenance and Suspension List
class CoreIlliquidMaintenanceSuspensionList(Base):
    """
    Core table for illiquid maintenance and suspension list
    """
    __tablename__ = 'illiquid_maintenance_suspension_list'
    __table_args__ = (
        UniqueConstraint('security_id', 'status_date', 'list_type_id', name='uq_illiquid_security_status'),
        Index('idx_illiquid_security_id', 'security_id'),
        Index('idx_illiquid_list_type_id', 'list_type_id'),
        Index('idx_illiquid_status_date', 'status_date'),
        {'schema': 'core'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    list_type_id = Column(String(50), nullable=True, comment='List type ID')
    status_date = Column(Date, nullable=False, comment='Status date')
    extraction_date = Column(Date, nullable=False, comment='Date when data was extracted')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<CoreIlliquidMaintenanceSuspensionList(security_id={self.security_id}, status_date={self.status_date})>"


# stg schema - Trading Code List
class StgTradingCodeList(Base):
    """
    Staging table for trading code list
    """
    __tablename__ = 'trading_code_list'
    __table_args__ = (
        UniqueConstraint('list_type_id', name='uq_trading_code_list_type_id'),
        Index('idx_trading_code_list_type_id', 'list_type_id'),
        {'schema': 'stg'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    list_type_id = Column(Integer, nullable=False, unique=True, comment='List type ID')
    list_type_desc = Column(String(200), nullable=True, comment='List type description')
    extraction_date = Column(Date, nullable=False, comment='Date when data was extracted')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<StgTradingCodeList(list_type_id={self.list_type_id}, list_type_desc={self.list_type_desc})>"


# core schema - Trading Code List
class CoreTradingCodeList(Base):
    """
    Core table for trading code list
    """
    __tablename__ = 'trading_code_list'
    __table_args__ = (
        UniqueConstraint('list_type_id', name='uq_trading_code_list_type_id'),
        Index('idx_trading_code_list_type_id', 'list_type_id'),
        {'schema': 'core'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    list_type_id = Column(Integer, nullable=False, unique=True, comment='List type ID')
    list_type_desc = Column(String(200), nullable=True, comment='List type description')
    extraction_date = Column(Date, nullable=False, comment='Date when data was extracted')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<CoreTradingCodeList(list_type_id={self.list_type_id}, list_type_desc={self.list_type_desc})>"


# stg schema - Securities Types
class StgSecuritiesTypes(Base):
    """
    Staging table for securities types
    """
    __tablename__ = 'securities_types'
    __table_args__ = (
        UniqueConstraint('security_full_type_code', name='uq_securities_types_full_code'),
        Index('idx_securities_types_full_code', 'security_full_type_code'),
        Index('idx_securities_types_main_code', 'security_main_type_code'),
        {'schema': 'stg'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    security_main_type_desc = Column(String(200), nullable=True, comment='Security main type description')
    security_main_type_code = Column(String(50), nullable=True, comment='Security main type code')
    security_full_type_code = Column(String(50), nullable=False, unique=True, comment='Security full type code')
    security_type_desc = Column(String(200), nullable=True, comment='Security type description')
    extraction_date = Column(Date, nullable=False, comment='Date when data was extracted')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<StgSecuritiesTypes(security_full_type_code={self.security_full_type_code}, security_type_desc={self.security_type_desc})>"


# core schema - Securities Types
class CoreSecuritiesTypes(Base):
    """
    Core table for securities types
    """
    __tablename__ = 'securities_types'
    __table_args__ = (
        UniqueConstraint('security_full_type_code', name='uq_securities_types_full_code'),
        Index('idx_securities_types_full_code', 'security_full_type_code'),
        Index('idx_securities_types_main_code', 'security_main_type_code'),
        {'schema': 'core'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    security_main_type_desc = Column(String(200), nullable=True, comment='Security main type description')
    security_main_type_code = Column(String(50), nullable=True, comment='Security main type code')
    security_full_type_code = Column(String(50), nullable=False, unique=True, comment='Security full type code')
    security_type_desc = Column(String(200), nullable=True, comment='Security type description')
    extraction_date = Column(Date, nullable=False, comment='Date when data was extracted')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<CoreSecuritiesTypes(security_full_type_code={self.security_full_type_code}, security_type_desc={self.security_type_desc})>"


# stg schema - Public Holdings in TASE Indices
class StgPublicHoldingsIndices(Base):
    """
    Staging table for public holdings in TASE indices
    """
    __tablename__ = 'public_holdings_indices'
    __table_args__ = (
        UniqueConstraint('index_id', 'date', name='uq_public_holdings_index_date'),
        Index('idx_public_holdings_index_id', 'index_id'),
        Index('idx_public_holdings_date', 'date'),
        Index('idx_public_holdings_fund_type', 'fund_type'),
        {'schema': 'stg'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the holdings data')
    index_id = Column(Integer, nullable=False, comment='Index ID')
    fund_type = Column(String(200), nullable=True, comment='Fund type')
    total_investment_in_the_index = Column(Float, nullable=True, comment='Total investment in the index')
    capital_listed_fund_and_etf = Column(BigInteger, nullable=True, comment='Capital listed fund and ETF')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<StgPublicHoldingsIndices(index_id={self.index_id}, date={self.date})>"


# core schema - Public Holdings in TASE Indices
class CorePublicHoldingsIndices(Base):
    """
    Core table for public holdings in TASE indices
    """
    __tablename__ = 'public_holdings_indices'
    __table_args__ = (
        UniqueConstraint('index_id', 'date', name='uq_public_holdings_index_date'),
        Index('idx_public_holdings_index_id', 'index_id'),
        Index('idx_public_holdings_date', 'date'),
        Index('idx_public_holdings_fund_type', 'fund_type'),
        {'schema': 'core'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the holdings data')
    index_id = Column(Integer, nullable=False, comment='Index ID')
    fund_type = Column(String(200), nullable=True, comment='Fund type')
    total_investment_in_the_index = Column(Float, nullable=True, comment='Total investment in the index')
    capital_listed_fund_and_etf = Column(BigInteger, nullable=True, comment='Capital listed fund and ETF')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<CorePublicHoldingsIndices(index_id={self.index_id}, date={self.date})>"


# stg schema - Expected Changes in IANS and Float
class StgExpectedChangesIansFloat(Base):
    """
    Staging table for expected changes in IANS and float
    """
    __tablename__ = 'expected_changes_ians_float'
    __table_args__ = (
        UniqueConstraint('security_id', 'date', name='uq_expected_changes_security_date'),
        Index('idx_expected_changes_security_id', 'security_id'),
        Index('idx_expected_changes_date', 'date'),
        Index('idx_expected_changes_symbol', 'symbol'),
        Index('idx_expected_changes_effective_date', 'effective_date'),
        {'schema': 'stg'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the data (from year/month/day parameters)')
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    security_name = Column(String(200), nullable=True, comment='Security name')
    symbol = Column(String(50), nullable=True, comment='Security symbol')
    isin = Column(String(50), nullable=True, comment='International Security Identification Number')
    update_type = Column(String(50), nullable=True, comment='Update type')
    announcement_date = Column(Date, nullable=True, comment='Announcement date')
    effective_date = Column(Date, nullable=True, comment='Effective date')
    last_ians_update = Column(Date, nullable=True, comment='Last IANS update date')
    new_ians = Column(String(50), nullable=True, comment='New IANS')
    new_index_adjusted_free_float = Column(Float, nullable=True, comment='New index adjusted free float')
    current_ians = Column(BigInteger, nullable=True, comment='Current IANS')
    current_index_adjusted_free_float = Column(Float, nullable=True, comment='Current index adjusted free float')
    liquidity_ratio = Column(Float, nullable=True, comment='Liquidity ratio')
    new_liquidity_ratio = Column(Float, nullable=True, comment='New liquidity ratio')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<StgExpectedChangesIansFloat(security_id={self.security_id}, date={self.date}, symbol={self.symbol})>"


# core schema - Expected Changes in IANS and Float
class CoreExpectedChangesIansFloat(Base):
    """
    Core table for expected changes in IANS and float
    """
    __tablename__ = 'expected_changes_ians_float'
    __table_args__ = (
        UniqueConstraint('security_id', 'date', name='uq_expected_changes_security_date'),
        Index('idx_expected_changes_security_id', 'security_id'),
        Index('idx_expected_changes_date', 'date'),
        Index('idx_expected_changes_symbol', 'symbol'),
        Index('idx_expected_changes_effective_date', 'effective_date'),
        {'schema': 'core'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the data (from year/month/day parameters)')
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    security_name = Column(String(200), nullable=True, comment='Security name')
    symbol = Column(String(50), nullable=True, comment='Security symbol')
    isin = Column(String(50), nullable=True, comment='International Security Identification Number')
    update_type = Column(String(50), nullable=True, comment='Update type')
    announcement_date = Column(Date, nullable=True, comment='Announcement date')
    effective_date = Column(Date, nullable=True, comment='Effective date')
    last_ians_update = Column(Date, nullable=True, comment='Last IANS update date')
    new_ians = Column(String(50), nullable=True, comment='New IANS')
    new_index_adjusted_free_float = Column(Float, nullable=True, comment='New index adjusted free float')
    current_ians = Column(BigInteger, nullable=True, comment='Current IANS')
    current_index_adjusted_free_float = Column(Float, nullable=True, comment='Current index adjusted free float')
    liquidity_ratio = Column(Float, nullable=True, comment='Liquidity ratio')
    new_liquidity_ratio = Column(Float, nullable=True, comment='New liquidity ratio')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<CoreExpectedChangesIansFloat(security_id={self.security_id}, date={self.date}, symbol={self.symbol})>"


# stg schema - Expected Changes Weight Factor
class StgExpectedChangesWeightFactor(Base):
    """
    Staging table for expected changes in weight factor
    """
    __tablename__ = 'expected_changes_weight_factor'
    __table_args__ = (
        UniqueConstraint('security_id', 'date', 'index_name', name='uq_expected_changes_weight_security_date_index'),
        Index('idx_expected_changes_weight_security_id', 'security_id'),
        Index('idx_expected_changes_weight_date', 'date'),
        Index('idx_expected_changes_weight_symbol', 'symbol'),
        Index('idx_expected_changes_weight_index_name', 'index_name'),
        Index('idx_expected_changes_weight_effective_date', 'effective_date'),
        {'schema': 'stg'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the data (from year/month/day parameters)')
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    security_name = Column(String(200), nullable=True, comment='Security name')
    symbol = Column(String(50), nullable=True, comment='Security symbol')
    isin = Column(String(50), nullable=True, comment='International Security Identification Number')
    index_name = Column(String(200), nullable=True, comment='Index name')
    update_type = Column(String(50), nullable=True, comment='Update type')
    announcement_date = Column(Date, nullable=True, comment='Announcement date')
    effective_date = Column(Date, nullable=True, comment='Effective date')
    previous_factor_date = Column(Date, nullable=True, comment='Previous factor date')
    new_weight_factor = Column(Float, nullable=True, comment='New weight factor')
    weight_factor = Column(Float, nullable=True, comment='Weight factor')
    new_issuer_adjusted_weight_cap = Column(Float, nullable=True, comment='New issuer adjusted weight cap')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<StgExpectedChangesWeightFactor(security_id={self.security_id}, date={self.date}, symbol={self.symbol}, index_name={self.index_name})>"


# core schema - Expected Changes Weight Factor
class CoreExpectedChangesWeightFactor(Base):
    """
    Core table for expected changes in weight factor
    """
    __tablename__ = 'expected_changes_weight_factor'
    __table_args__ = (
        UniqueConstraint('security_id', 'date', 'index_name', name='uq_expected_changes_weight_security_date_index'),
        Index('idx_expected_changes_weight_security_id', 'security_id'),
        Index('idx_expected_changes_weight_date', 'date'),
        Index('idx_expected_changes_weight_symbol', 'symbol'),
        Index('idx_expected_changes_weight_index_name', 'index_name'),
        Index('idx_expected_changes_weight_effective_date', 'effective_date'),
        {'schema': 'core'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the data (from year/month/day parameters)')
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    security_name = Column(String(200), nullable=True, comment='Security name')
    symbol = Column(String(50), nullable=True, comment='Security symbol')
    isin = Column(String(50), nullable=True, comment='International Security Identification Number')
    index_name = Column(String(200), nullable=True, comment='Index name')
    update_type = Column(String(50), nullable=True, comment='Update type')
    announcement_date = Column(Date, nullable=True, comment='Announcement date')
    effective_date = Column(Date, nullable=True, comment='Effective date')
    previous_factor_date = Column(Date, nullable=True, comment='Previous factor date')
    new_weight_factor = Column(Float, nullable=True, comment='New weight factor')
    weight_factor = Column(Float, nullable=True, comment='Weight factor')
    new_issuer_adjusted_weight_cap = Column(Float, nullable=True, comment='New issuer adjusted weight cap')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<CoreExpectedChangesWeightFactor(security_id={self.security_id}, date={self.date}, symbol={self.symbol}, index_name={self.index_name})>"


# stg schema - Index Components Extended
class StgIndexComponentsExtended(Base):
    """
    Staging table for index components extended
    """
    __tablename__ = 'index_components_extended'
    __table_args__ = (
        UniqueConstraint('security_id', 'index_id', 'date', name='uq_index_components_security_index_date'),
        Index('idx_index_components_security_id', 'security_id'),
        Index('idx_index_components_date', 'date'),
        Index('idx_index_components_index_id', 'index_id'),
        Index('idx_index_components_symbol', 'symbol'),
        {'schema': 'stg'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the data (from year/month/day parameters)')
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    security_name = Column(String(200), nullable=True, comment='Security name')
    symbol = Column(String(50), nullable=True, comment='Security symbol')
    isin = Column(String(50), nullable=True, comment='International Security Identification Number')
    index_id = Column(String(50), nullable=True, comment='Index ID')
    last_ians_update = Column(String(50), nullable=True, comment='Last IANS update date (DD/MM/YYYY format)')
    weight = Column(Float, nullable=True, comment='Weight')
    market_cap = Column(Float, nullable=True, comment='Market capitalization')
    base_price = Column(Float, nullable=True, comment='Base price')
    closing_price = Column(Float, nullable=True, comment='Closing price')
    is_ex = Column(Boolean, nullable=True, comment='Is EX')
    semi_ann_daily_turnover_avg = Column(Float, nullable=True, comment='Semi-annual daily turnover average')
    semi_ann_median_turnover = Column(Float, nullable=True, comment='Semi-annual median turnover')
    free_float_rate = Column(Float, nullable=True, comment='Free float rate')
    free_float_percent = Column(Float, nullable=True, comment='Free float percent')
    ians = Column(BigInteger, nullable=True, comment='IANS')
    index_adjusted_free_float = Column(Float, nullable=True, comment='Index adjusted free float')
    weight_factor = Column(Float, nullable=True, comment='Weight factor')
    free_float_market_cap = Column(Float, nullable=True, comment='Free float market cap')
    liquidity_ratio = Column(Float, nullable=True, comment='Liquidity ratio')
    weighted_factor = Column(Float, nullable=True, comment='Weighted factor')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<StgIndexComponentsExtended(security_id={self.security_id}, index_id={self.index_id}, date={self.date}, symbol={self.symbol})>"


# core schema - Index Components Extended
class CoreIndexComponentsExtended(Base):
    """
    Core table for index components extended
    """
    __tablename__ = 'index_components_extended'
    __table_args__ = (
        UniqueConstraint('security_id', 'index_id', 'date', name='uq_index_components_security_index_date'),
        Index('idx_index_components_security_id', 'security_id'),
        Index('idx_index_components_date', 'date'),
        Index('idx_index_components_index_id', 'index_id'),
        Index('idx_index_components_symbol', 'symbol'),
        {'schema': 'core'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the data (from year/month/day parameters)')
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    security_name = Column(String(200), nullable=True, comment='Security name')
    symbol = Column(String(50), nullable=True, comment='Security symbol')
    isin = Column(String(50), nullable=True, comment='International Security Identification Number')
    index_id = Column(String(50), nullable=True, comment='Index ID')
    last_ians_update = Column(String(50), nullable=True, comment='Last IANS update date (DD/MM/YYYY format)')
    weight = Column(Float, nullable=True, comment='Weight')
    market_cap = Column(Float, nullable=True, comment='Market capitalization')
    base_price = Column(Float, nullable=True, comment='Base price')
    closing_price = Column(Float, nullable=True, comment='Closing price')
    is_ex = Column(Boolean, nullable=True, comment='Is EX')
    semi_ann_daily_turnover_avg = Column(Float, nullable=True, comment='Semi-annual daily turnover average')
    semi_ann_median_turnover = Column(Float, nullable=True, comment='Semi-annual median turnover')
    free_float_rate = Column(Float, nullable=True, comment='Free float rate')
    free_float_percent = Column(Float, nullable=True, comment='Free float percent')
    ians = Column(BigInteger, nullable=True, comment='IANS')
    index_adjusted_free_float = Column(Float, nullable=True, comment='Index adjusted free float')
    weight_factor = Column(Float, nullable=True, comment='Weight factor')
    free_float_market_cap = Column(Float, nullable=True, comment='Free float market cap')
    liquidity_ratio = Column(Float, nullable=True, comment='Liquidity ratio')
    weighted_factor = Column(Float, nullable=True, comment='Weighted factor')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<CoreIndexComponentsExtended(security_id={self.security_id}, index_id={self.index_id}, date={self.date}, symbol={self.symbol})>"


# stg schema - Parameters Update Schedule
class StgParametersUpdateSchedule(Base):
    """
    Staging table for parameters update schedule
    """
    __tablename__ = 'parameters_update_schedule'
    __table_args__ = (
        UniqueConstraint('record_date', 'effective_date', 'index_category', 'update_type', name='uq_parameters_schedule_record_effective_category_type'),
        Index('idx_parameters_schedule_date', 'date'),
        Index('idx_parameters_schedule_record_date', 'record_date'),
        Index('idx_parameters_schedule_effective_date', 'effective_date'),
        Index('idx_parameters_schedule_index_category', 'index_category'),
        {'schema': 'stg'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the data (from year/month parameters)')
    index_category = Column(String(200), nullable=True, comment='Index category')
    update_type = Column(String(200), nullable=True, comment='Update type')
    record_date = Column(Date, nullable=True, comment='Record date')
    announcement_date = Column(Date, nullable=True, comment='Announcement date')
    effective_date = Column(Date, nullable=True, comment='Effective date')
    free_float_record_date = Column(Date, nullable=True, comment='Free float record date')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<StgParametersUpdateSchedule(index_category={self.index_category}, update_type={self.update_type}, record_date={self.record_date})>"


# core schema - Parameters Update Schedule
class CoreParametersUpdateSchedule(Base):
    """
    Core table for parameters update schedule
    """
    __tablename__ = 'parameters_update_schedule'
    __table_args__ = (
        UniqueConstraint('record_date', 'effective_date', 'index_category', 'update_type', name='uq_parameters_schedule_record_effective_category_type'),
        Index('idx_parameters_schedule_date', 'date'),
        Index('idx_parameters_schedule_record_date', 'record_date'),
        Index('idx_parameters_schedule_effective_date', 'effective_date'),
        Index('idx_parameters_schedule_index_category', 'index_category'),
        {'schema': 'core'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the data (from year/month parameters)')
    index_category = Column(String(200), nullable=True, comment='Index category')
    update_type = Column(String(200), nullable=True, comment='Update type')
    record_date = Column(Date, nullable=True, comment='Record date')
    announcement_date = Column(Date, nullable=True, comment='Announcement date')
    effective_date = Column(Date, nullable=True, comment='Effective date')
    free_float_record_date = Column(Date, nullable=True, comment='Free float record date')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<CoreParametersUpdateSchedule(index_category={self.index_category}, update_type={self.update_type}, record_date={self.record_date})>"


# stg schema - Indices Constituents Update
class StgIndicesConstituentsUpdate(Base):
    """
    Staging table for indices constituents update
    """
    __tablename__ = 'indices_constituents_update'
    __table_args__ = (
        UniqueConstraint('security_id', 'index_id', 'effective_date', 'announcement_date', name='uq_indices_constituents_security_index_effective_announcement'),
        Index('idx_indices_constituents_security_id', 'security_id'),
        Index('idx_indices_constituents_date', 'date'),
        Index('idx_indices_constituents_index_id', 'index_id'),
        Index('idx_indices_constituents_symbol', 'symbol'),
        Index('idx_indices_constituents_effective_date', 'effective_date'),
        {'schema': 'stg'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the data (from year/month parameters)')
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    security_name = Column(String(200), nullable=True, comment='Security name')
    symbol = Column(String(50), nullable=True, comment='Security symbol')
    isin = Column(String(50), nullable=True, comment='International Security Identification Number')
    index_id = Column(Integer, nullable=True, comment='Index ID')
    index_name = Column(String(200), nullable=True, comment='Index name')
    security_status_index = Column(String(200), nullable=True, comment='Security status index')
    update_type = Column(String(50), nullable=True, comment='Update type')
    market_sector = Column(String(200), nullable=True, comment='Market sector')
    announcement_date = Column(Date, nullable=True, comment='Announcement date')
    effective_date = Column(Date, nullable=True, comment='Effective date')
    new_ians = Column(BigInteger, nullable=True, comment='New IANS')
    expected_fnv_pre_rebalance_bonds_only = Column(BigInteger, nullable=True, comment='Expected FNV pre rebalance bonds only')
    new_index_adjusted_free_float = Column(String(50), nullable=True, comment='New index adjusted free float')
    new_weight_factor = Column(Float, nullable=True, comment='New weight factor')
    free_float_semi_annual = Column(Float, nullable=True, comment='Free float semi annual')
    free_float_monthly = Column(Float, nullable=True, comment='Free float monthly')
    average_free_float = Column(Float, nullable=True, comment='Average free float')
    is_illiquid_securities_candidate = Column(Boolean, nullable=True, comment='Is illiquid securities candidate')
    is_maintenance_list = Column(Boolean, nullable=True, comment='Is maintenance list')
    is_suspended_securities = Column(Boolean, nullable=True, comment='Is suspended securities')
    semi_annual_average_daily_turnover = Column(Float, nullable=True, comment='Semi annual average daily turnover')
    semi_annual_median_turnover = Column(Float, nullable=True, comment='Semi annual median turnover')
    capital_listed_trading = Column(BigInteger, nullable=True, comment='Capital listed trading')
    average_market_cap = Column(Float, nullable=True, comment='Average market cap')
    average_price = Column(Float, nullable=True, comment='Average price')
    closing_price = Column(Float, nullable=True, comment='Closing price')
    liquidity_ratio = Column(Float, nullable=True, comment='Liquidity ratio')
    weighted_factor = Column(Float, nullable=True, comment='Weighted factor')
    median_velocity_turnover = Column(Float, nullable=True, comment='Median velocity turnover')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<StgIndicesConstituentsUpdate(security_id={self.security_id}, index_id={self.index_id}, effective_date={self.effective_date}, symbol={self.symbol})>"


# core schema - Indices Constituents Update
class CoreIndicesConstituentsUpdate(Base):
    """
    Core table for indices constituents update
    """
    __tablename__ = 'indices_constituents_update'
    __table_args__ = (
        UniqueConstraint('security_id', 'index_id', 'effective_date', 'announcement_date', name='uq_indices_constituents_security_index_effective_announcement'),
        Index('idx_indices_constituents_security_id', 'security_id'),
        Index('idx_indices_constituents_date', 'date'),
        Index('idx_indices_constituents_index_id', 'index_id'),
        Index('idx_indices_constituents_symbol', 'symbol'),
        Index('idx_indices_constituents_effective_date', 'effective_date'),
        {'schema': 'core'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the data (from year/month parameters)')
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    security_name = Column(String(200), nullable=True, comment='Security name')
    symbol = Column(String(50), nullable=True, comment='Security symbol')
    isin = Column(String(50), nullable=True, comment='International Security Identification Number')
    index_id = Column(Integer, nullable=True, comment='Index ID')
    index_name = Column(String(200), nullable=True, comment='Index name')
    security_status_index = Column(String(200), nullable=True, comment='Security status index')
    update_type = Column(String(50), nullable=True, comment='Update type')
    market_sector = Column(String(200), nullable=True, comment='Market sector')
    announcement_date = Column(Date, nullable=True, comment='Announcement date')
    effective_date = Column(Date, nullable=True, comment='Effective date')
    new_ians = Column(BigInteger, nullable=True, comment='New IANS')
    expected_fnv_pre_rebalance_bonds_only = Column(BigInteger, nullable=True, comment='Expected FNV pre rebalance bonds only')
    new_index_adjusted_free_float = Column(String(50), nullable=True, comment='New index adjusted free float')
    new_weight_factor = Column(Float, nullable=True, comment='New weight factor')
    free_float_semi_annual = Column(Float, nullable=True, comment='Free float semi annual')
    free_float_monthly = Column(Float, nullable=True, comment='Free float monthly')
    average_free_float = Column(Float, nullable=True, comment='Average free float')
    is_illiquid_securities_candidate = Column(Boolean, nullable=True, comment='Is illiquid securities candidate')
    is_maintenance_list = Column(Boolean, nullable=True, comment='Is maintenance list')
    is_suspended_securities = Column(Boolean, nullable=True, comment='Is suspended securities')
    semi_annual_average_daily_turnover = Column(Float, nullable=True, comment='Semi annual average daily turnover')
    semi_annual_median_turnover = Column(Float, nullable=True, comment='Semi annual median turnover')
    capital_listed_trading = Column(BigInteger, nullable=True, comment='Capital listed trading')
    average_market_cap = Column(Float, nullable=True, comment='Average market cap')
    average_price = Column(Float, nullable=True, comment='Average price')
    closing_price = Column(Float, nullable=True, comment='Closing price')
    liquidity_ratio = Column(Float, nullable=True, comment='Liquidity ratio')
    weighted_factor = Column(Float, nullable=True, comment='Weighted factor')
    median_velocity_turnover = Column(Float, nullable=True, comment='Median velocity turnover')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<CoreIndicesConstituentsUpdate(security_id={self.security_id}, index_id={self.index_id}, effective_date={self.effective_date}, symbol={self.symbol})>"


# stg schema - Capital Listed For Trading End Of Day
class StgCapitalListedForTradingEod(Base):
    """
    Staging table for capital listed for trading end of day
    """
    __tablename__ = 'capital_listed_for_trading_eod'
    __table_args__ = (
        UniqueConstraint('security_id', 'trade_date', name='uq_capital_listed_security_trade_date'),
        Index('idx_capital_listed_security_id', 'security_id'),
        Index('idx_capital_listed_date', 'date'),
        Index('idx_capital_listed_trade_date', 'trade_date'),
        Index('idx_capital_listed_symbol', 'symbol'),
        {'schema': 'stg'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the data (from year/month/day parameters)')
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    security_name = Column(String(200), nullable=True, comment='Security name')
    symbol = Column(String(50), nullable=True, comment='Security symbol')
    isin = Column(String(50), nullable=True, comment='International Security Identification Number')
    trade_date = Column(Date, nullable=True, comment='Trade date')
    last_ians_update = Column(Date, nullable=True, comment='Last IANS update date')
    ians = Column(BigInteger, nullable=True, comment='IANS')
    index_adjusted_free_float = Column(Float, nullable=True, comment='Index adjusted free float')
    ians_change = Column(Integer, nullable=True, comment='IANS change')
    listed_capital = Column(BigInteger, nullable=True, comment='Listed capital')
    capital_change = Column(Integer, nullable=True, comment='Capital change')
    liquidity_ratio = Column(Float, nullable=True, comment='Liquidity ratio')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<StgCapitalListedForTradingEod(security_id={self.security_id}, trade_date={self.trade_date}, symbol={self.symbol})>"


# core schema - Capital Listed For Trading End Of Day
class CoreCapitalListedForTradingEod(Base):
    """
    Core table for capital listed for trading end of day
    """
    __tablename__ = 'capital_listed_for_trading_eod'
    __table_args__ = (
        UniqueConstraint('security_id', 'trade_date', name='uq_capital_listed_security_trade_date'),
        Index('idx_capital_listed_security_id', 'security_id'),
        Index('idx_capital_listed_date', 'date'),
        Index('idx_capital_listed_trade_date', 'trade_date'),
        Index('idx_capital_listed_symbol', 'symbol'),
        {'schema': 'core'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the data (from year/month/day parameters)')
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    security_name = Column(String(200), nullable=True, comment='Security name')
    symbol = Column(String(50), nullable=True, comment='Security symbol')
    isin = Column(String(50), nullable=True, comment='International Security Identification Number')
    trade_date = Column(Date, nullable=True, comment='Trade date')
    last_ians_update = Column(Date, nullable=True, comment='Last IANS update date')
    ians = Column(BigInteger, nullable=True, comment='IANS')
    index_adjusted_free_float = Column(Float, nullable=True, comment='Index adjusted free float')
    ians_change = Column(Integer, nullable=True, comment='IANS change')
    listed_capital = Column(BigInteger, nullable=True, comment='Listed capital')
    capital_change = Column(Integer, nullable=True, comment='Capital change')
    liquidity_ratio = Column(Float, nullable=True, comment='Liquidity ratio')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<CoreCapitalListedForTradingEod(security_id={self.security_id}, trade_date={self.trade_date}, symbol={self.symbol})>"


# stg schema - Constituents Update Lists
class StgConstituentsUpdateLists(Base):
    """
    Staging table for constituents update lists
    """
    __tablename__ = 'constituents_update_lists'
    __table_args__ = (
        UniqueConstraint('security_id', 'trade_date', name='uq_constituents_update_security_trade_date'),
        Index('idx_constituents_update_security_id', 'security_id'),
        Index('idx_constituents_update_date', 'date'),
        Index('idx_constituents_update_trade_date', 'trade_date'),
        {'schema': 'stg'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the data (from year/month/day parameters)')
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    security_name = Column(String(200), nullable=True, comment='Security name')
    security_type = Column(Integer, nullable=True, comment='Security type')
    isin = Column(String(50), nullable=True, comment='International Security Identification Number')
    market_sektor = Column(String(200), nullable=True, comment='Market sector')
    trade_date = Column(Date, nullable=True, comment='Trade date')
    securities_for_indices_lists_update = Column(JSONB, nullable=True, comment='Securities for indices lists update (array of objects)')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<StgConstituentsUpdateLists(security_id={self.security_id}, trade_date={self.trade_date}, security_name={self.security_name})>"


# core schema - Constituents Update Lists
class CoreConstituentsUpdateLists(Base):
    """
    Core table for constituents update lists
    """
    __tablename__ = 'constituents_update_lists'
    __table_args__ = (
        UniqueConstraint('security_id', 'trade_date', name='uq_constituents_update_security_trade_date'),
        Index('idx_constituents_update_security_id', 'security_id'),
        Index('idx_constituents_update_date', 'date'),
        Index('idx_constituents_update_trade_date', 'trade_date'),
        {'schema': 'core'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the data (from year/month/day parameters)')
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    security_name = Column(String(200), nullable=True, comment='Security name')
    security_type = Column(Integer, nullable=True, comment='Security type')
    isin = Column(String(50), nullable=True, comment='International Security Identification Number')
    market_sektor = Column(String(200), nullable=True, comment='Market sector')
    trade_date = Column(Date, nullable=True, comment='Trade date')
    securities_for_indices_lists_update = Column(JSONB, nullable=True, comment='Securities for indices lists update (array of objects)')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<CoreConstituentsUpdateLists(security_id={self.security_id}, trade_date={self.trade_date}, security_name={self.security_name})>"


# stg schema - Bond Data
class StgBondData(Base):
    """
    Staging table for bond data
    """
    __tablename__ = 'bond_data'
    __table_args__ = (
        UniqueConstraint('security_id', 'first_trading_date', name='uq_bond_data_security_first_trading_date'),
        Index('idx_bond_data_security_id', 'security_id'),
        Index('idx_bond_data_date', 'date'),
        Index('idx_bond_data_first_trading_date', 'first_trading_date'),
        {'schema': 'stg'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the data (from year/month/day parameters)')
    security_id = Column(String(50), nullable=False, comment='Security identifier (can be string)')
    first_trading_date = Column(Date, nullable=True, comment='First trading date')
    market_cap = Column(String(200), nullable=True, comment='Market cap')
    average_market_cap_without_redemption = Column(BigInteger, nullable=True, comment='Average market cap without redemption')
    exit_from_tel_bond = Column(String(200), nullable=True, comment='Exit from Tel Bond')
    interest_type = Column(String(200), nullable=True, comment='Interest type')
    indices = Column(JSONB, nullable=True, comment='Indices (array of objects)')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<StgBondData(security_id={self.security_id}, first_trading_date={self.first_trading_date})>"


# core schema - Bond Data
class CoreBondData(Base):
    """
    Core table for bond data
    """
    __tablename__ = 'bond_data'
    __table_args__ = (
        UniqueConstraint('security_id', 'first_trading_date', name='uq_bond_data_security_first_trading_date'),
        Index('idx_bond_data_security_id', 'security_id'),
        Index('idx_bond_data_date', 'date'),
        Index('idx_bond_data_first_trading_date', 'first_trading_date'),
        {'schema': 'core'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the data (from year/month/day parameters)')
    security_id = Column(String(50), nullable=False, comment='Security identifier (can be string)')
    first_trading_date = Column(Date, nullable=True, comment='First trading date')
    market_cap = Column(String(200), nullable=True, comment='Market cap')
    average_market_cap_without_redemption = Column(BigInteger, nullable=True, comment='Average market cap without redemption')
    exit_from_tel_bond = Column(String(200), nullable=True, comment='Exit from Tel Bond')
    interest_type = Column(String(200), nullable=True, comment='Interest type')
    indices = Column(JSONB, nullable=True, comment='Indices (array of objects)')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<CoreBondData(security_id={self.security_id}, first_trading_date={self.first_trading_date})>"


# stg schema - Universe Constituents Update
class StgUniverseConstituentsUpdate(Base):
    """
    Staging table for universe constituents update
    """
    __tablename__ = 'universe_constituents_update'
    __table_args__ = (
        UniqueConstraint('security_id', 'effective_date', 'universe_name', name='uq_universe_constituents_security_effective_universe'),
        Index('idx_universe_constituents_security_id', 'security_id'),
        Index('idx_universe_constituents_date', 'date'),
        Index('idx_universe_constituents_universe_name', 'universe_name'),
        Index('idx_universe_constituents_effective_date', 'effective_date'),
        Index('idx_universe_constituents_symbol', 'symbol'),
        {'schema': 'stg'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the data (from year/month parameters)')
    universe_name = Column(String(200), nullable=False, comment='Universe name (from URL parameter)')
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    security_name = Column(String(200), nullable=True, comment='Security name')
    symbol = Column(String(50), nullable=True, comment='Security symbol')
    isin = Column(String(50), nullable=True, comment='International Security Identification Number')
    index_universe_name = Column(String(200), nullable=True, comment='Index universe name')
    security_status = Column(String(200), nullable=True, comment='Security status')
    update_type = Column(String(50), nullable=True, comment='Update type')
    market_sector = Column(String(200), nullable=True, comment='Market sector')
    announcement_date = Column(Date, nullable=True, comment='Announcement date')
    effective_date = Column(Date, nullable=True, comment='Effective date')
    new_ians = Column(String(50), nullable=True, comment='New IANS')
    new_index_adjusted_free_float = Column(String(50), nullable=True, comment='New index adjusted free float')
    free_float_semi_annual = Column(String(50), nullable=True, comment='Free float semi annual')
    free_float_monthly = Column(String(50), nullable=True, comment='Free float monthly')
    average_free_float = Column(Float, nullable=True, comment='Average free float')
    is_illiquid_securities_candidate = Column(Boolean, nullable=True, comment='Is illiquid securities candidate')
    is_maintenance_list = Column(Boolean, nullable=True, comment='Is maintenance list')
    is_suspended_securities = Column(Boolean, nullable=True, comment='Is suspended securities')
    semi_annual_average_daily_turnover = Column(Float, nullable=True, comment='Semi annual average daily turnover')
    semi_annual_median_turnover = Column(Float, nullable=True, comment='Semi annual median turnover')
    capital_listed_trading = Column(BigInteger, nullable=True, comment='Capital listed trading')
    average_market_cap = Column(Float, nullable=True, comment='Average market cap')
    average_price = Column(Float, nullable=True, comment='Average price')
    closing_price = Column(Float, nullable=True, comment='Closing price')
    median_velocity_turnover = Column(Float, nullable=True, comment='Median velocity turnover')
    liquidity_ratio = Column(Float, nullable=True, comment='Liquidity ratio')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<StgUniverseConstituentsUpdate(security_id={self.security_id}, universe_name={self.universe_name}, effective_date={self.effective_date})>"


# core schema - Universe Constituents Update
class CoreUniverseConstituentsUpdate(Base):
    """
    Core table for universe constituents update
    """
    __tablename__ = 'universe_constituents_update'
    __table_args__ = (
        UniqueConstraint('security_id', 'effective_date', 'universe_name', name='uq_universe_constituents_security_effective_universe'),
        Index('idx_universe_constituents_security_id', 'security_id'),
        Index('idx_universe_constituents_date', 'date'),
        Index('idx_universe_constituents_universe_name', 'universe_name'),
        Index('idx_universe_constituents_effective_date', 'effective_date'),
        Index('idx_universe_constituents_symbol', 'symbol'),
        {'schema': 'core'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, comment='Date of the data (from year/month parameters)')
    universe_name = Column(String(200), nullable=False, comment='Universe name (from URL parameter)')
    security_id = Column(BigInteger, nullable=False, comment='Security identifier')
    security_name = Column(String(200), nullable=True, comment='Security name')
    symbol = Column(String(50), nullable=True, comment='Security symbol')
    isin = Column(String(50), nullable=True, comment='International Security Identification Number')
    index_universe_name = Column(String(200), nullable=True, comment='Index universe name')
    security_status = Column(String(200), nullable=True, comment='Security status')
    update_type = Column(String(50), nullable=True, comment='Update type')
    market_sector = Column(String(200), nullable=True, comment='Market sector')
    announcement_date = Column(Date, nullable=True, comment='Announcement date')
    effective_date = Column(Date, nullable=True, comment='Effective date')
    new_ians = Column(String(50), nullable=True, comment='New IANS')
    new_index_adjusted_free_float = Column(String(50), nullable=True, comment='New index adjusted free float')
    free_float_semi_annual = Column(String(50), nullable=True, comment='Free float semi annual')
    free_float_monthly = Column(String(50), nullable=True, comment='Free float monthly')
    average_free_float = Column(Float, nullable=True, comment='Average free float')
    is_illiquid_securities_candidate = Column(Boolean, nullable=True, comment='Is illiquid securities candidate')
    is_maintenance_list = Column(Boolean, nullable=True, comment='Is maintenance list')
    is_suspended_securities = Column(Boolean, nullable=True, comment='Is suspended securities')
    semi_annual_average_daily_turnover = Column(Float, nullable=True, comment='Semi annual average daily turnover')
    semi_annual_median_turnover = Column(Float, nullable=True, comment='Semi annual median turnover')
    capital_listed_trading = Column(BigInteger, nullable=True, comment='Capital listed trading')
    average_market_cap = Column(Float, nullable=True, comment='Average market cap')
    average_price = Column(Float, nullable=True, comment='Average price')
    closing_price = Column(Float, nullable=True, comment='Closing price')
    median_velocity_turnover = Column(Float, nullable=True, comment='Median velocity turnover')
    liquidity_ratio = Column(Float, nullable=True, comment='Liquidity ratio')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<CoreUniverseConstituentsUpdate(security_id={self.security_id}, universe_name={self.universe_name}, effective_date={self.effective_date})>"


# stg schema - Update Types
class StgUpdateTypes(Base):
    """
    Staging table for update types
    """
    __tablename__ = 'update_types'
    __table_args__ = (
        UniqueConstraint('update_type_id', name='uq_update_types_id'),
        Index('idx_update_types_id', 'update_type_id'),
        {'schema': 'stg'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    update_type_id = Column(String(50), nullable=False, comment='Update type identifier')
    update_type = Column(String(200), nullable=True, comment='Update type description')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<StgUpdateTypes(update_type_id={self.update_type_id}, update_type={self.update_type})>"


# core schema - Update Types
class CoreUpdateTypes(Base):
    """
    Core table for update types
    """
    __tablename__ = 'update_types'
    __table_args__ = (
        UniqueConstraint('update_type_id', name='uq_update_types_id'),
        Index('idx_update_types_id', 'update_type_id'),
        {'schema': 'core'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    update_type_id = Column(String(50), nullable=False, comment='Update type identifier')
    update_type = Column(String(200), nullable=True, comment='Update type description')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                       nullable=False, comment='Record update timestamp')

    def __repr__(self):
        return f"<CoreUpdateTypes(update_type_id={self.update_type_id}, update_type={self.update_type})>"