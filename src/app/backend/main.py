from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
DB_CONN = os.getenv("DB_CONN")

app = FastAPI()

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_connection():
    return psycopg2.connect(DB_CONN)

@app.get("/")
def root():
    return {"message": "Stock analysis API is running ✅"}

@app.get("/companies")
def get_companies():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT ticker, name FROM companies ORDER BY ticker")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"ticker": t, "name": n} for t, n in rows]

@app.get("/statements/{ticker}")
def get_statements(ticker: str, limit: int = 100):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.tag, s.value, s.unit, s.start_date, s.end_date, s.fiscal_year, s.fiscal_period
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s
        ORDER BY s.end_date DESC
        LIMIT %s
    """, (ticker.upper(), limit))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail=f"No statements found for {ticker}")
    
    return [
        {
            "tag": tag,
            "value": float(value),
            "unit": unit,
            "start_date": str(start),
            "end_date": str(end),
            "fiscal_year": fy,
            "fiscal_period": fp
        }
        for tag, value, unit, start, end, fy, fp in rows
    ]


@app.get("/tags/{ticker}/{year}")
def get_tags_for_year(ticker: str, year: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT s.tag
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s AND s.fiscal_year = %s
        ORDER BY s.tag
    """, (ticker.upper(), year))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [tag for (tag,) in rows]

@app.get("/statement-summary/{ticker}/{year}")
def get_statement_summary(ticker: str, year: int):
    # Customize these tags to fit what you care about
    key_tags = [
        "Revenues",
        "NetIncomeLoss",
        "OperatingIncomeLoss",
        "Assets",
        "Liabilities",
        "StockholdersEquity"
    ]
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.tag, s.value, s.unit, s.fiscal_period
        FROM statements s
        JOIN companies c ON s.company_id = c.id
        WHERE c.ticker = %s AND s.fiscal_year = %s AND s.tag = ANY(%s)
    """, (ticker.upper(), year, key_tags))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    summary = {}
    for tag, value, unit, period in rows:
        summary[tag] = {
            "value": float(value),
            "unit": unit,
            "period": period
        }

    return {
        "ticker": ticker.upper(),
        "fiscal_year": year,
        "summary": summary
    }


# Enhanced Financial Statement Endpoints

def format_financial_data(rows, format_detailed: bool = False, currency_format: str = "actual"):
    """Helper function to format financial data consistently"""
    result = {}
    
    for row in rows:
        tag, value, unit, start_date, end_date, fiscal_year, fiscal_period, standard_label, documentation, financial_statement = row
        
        # Convert value based on currency format
        formatted_value = float(value) if value else 0
        if currency_format == "millions" and formatted_value != 0:
            formatted_value = formatted_value / 1_000_000
        elif currency_format == "billions" and formatted_value != 0:
            formatted_value = formatted_value / 1_000_000_000
        
        item = {
            "value": formatted_value,
            "unit": unit,
            "label": standard_label or tag,
            "fiscal_year": fiscal_year,
            "fiscal_period": fiscal_period,
            "start_date": str(start_date) if start_date else None,
            "end_date": str(end_date) if end_date else None
        }
        
        if format_detailed:
            item["tag"] = tag
            item["documentation"] = documentation
            item["financial_statement"] = financial_statement
        
        result[tag] = item
    
    return result

def get_latest_period(conn, ticker: str, period_type: str = "any"):
    """Get the most recent fiscal period for a ticker"""
    cur = conn.cursor()
    
    if period_type == "annual":
        period_filter = "AND s.fiscal_period = 'FY'"
    elif period_type == "quarterly":
        period_filter = "AND s.fiscal_period != 'FY'"
    else:
        period_filter = ""
    
    cur.execute(f"""
        SELECT s.fiscal_year, s.fiscal_period, MAX(s.end_date) as latest_date
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s {period_filter}
        GROUP BY s.fiscal_year, s.fiscal_period
        ORDER BY latest_date DESC
        LIMIT 1
    """, (ticker.upper(),))
    
    result = cur.fetchone()
    cur.close()
    return result


# 1. Latest Financial Statements
@app.get("/financial-statements/{ticker}/latest")
def get_latest_financial_statements(
    ticker: str,
    format: str = Query("standard", description="Response format: standard or detailed"),
    currency: str = Query("actual", description="Currency format: actual, millions, or billions")
):
    """Get all financial statements for the most recent period"""
    conn = get_connection()
    
    # Get latest period
    latest = get_latest_period(conn, ticker)
    if not latest:
        raise HTTPException(status_code=404, detail=f"No data found for {ticker}")
    
    fiscal_year, fiscal_period, _ = latest
    
    cur = conn.cursor()
    cur.execute("""
        SELECT s.tag, s.value, s.unit, s.start_date, s.end_date, s.fiscal_year, s.fiscal_period,
               s.standard_label, s.documentation, s.financial_statement
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s AND s.fiscal_year = %s AND s.fiscal_period = %s
              AND s.financial_statement IS NOT NULL
        ORDER BY s.financial_statement, ABS(s.value) DESC
    """, (ticker.upper(), fiscal_year, fiscal_period))
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail=f"No financial statements found for {ticker}")
    
    # Group by financial statement type
    statements = {}
    for row in rows:
        stmt_type = row[9]  # financial_statement column
        if stmt_type not in statements:
            statements[stmt_type] = {}
        
        formatted_row = format_financial_data([row], format == "detailed", currency)
        statements[stmt_type].update(formatted_row)
    
    return {
        "ticker": ticker.upper(),
        "fiscal_year": fiscal_year,
        "fiscal_period": fiscal_period,
        "statements": statements
    }

@app.get("/income-statement/{ticker}/latest")
def get_latest_income_statement(
    ticker: str,
    format: str = Query("standard", description="Response format: standard or detailed"),
    currency: str = Query("actual", description="Currency format: actual, millions, or billions")
):
    """Get the latest income statement"""
    conn = get_connection()
    latest = get_latest_period(conn, ticker)
    if not latest:
        raise HTTPException(status_code=404, detail=f"No data found for {ticker}")
    
    fiscal_year, fiscal_period, _ = latest
    
    cur = conn.cursor()
    cur.execute("""
        SELECT s.tag, s.value, s.unit, s.start_date, s.end_date, s.fiscal_year, s.fiscal_period,
               s.standard_label, s.documentation, s.financial_statement
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s AND s.fiscal_year = %s AND s.fiscal_period = %s
              AND s.financial_statement = 'Statement of Income'
        ORDER BY ABS(s.value) DESC
    """, (ticker.upper(), fiscal_year, fiscal_period))
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail=f"No income statement found for {ticker}")
    
    return {
        "ticker": ticker.upper(),
        "fiscal_year": fiscal_year,
        "fiscal_period": fiscal_period,
        "statement_type": "Statement of Income",
        "data": format_financial_data(rows, format == "detailed", currency)
    }

@app.get("/balance-sheet/{ticker}/latest")
def get_latest_balance_sheet(
    ticker: str,
    format: str = Query("standard", description="Response format: standard or detailed"),
    currency: str = Query("actual", description="Currency format: actual, millions, or billions")
):
    """Get the latest balance sheet"""
    conn = get_connection()
    latest = get_latest_period(conn, ticker)
    if not latest:
        raise HTTPException(status_code=404, detail=f"No data found for {ticker}")
    
    fiscal_year, fiscal_period, _ = latest
    
    cur = conn.cursor()
    cur.execute("""
        SELECT s.tag, s.value, s.unit, s.start_date, s.end_date, s.fiscal_year, s.fiscal_period,
               s.standard_label, s.documentation, s.financial_statement
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s AND s.fiscal_year = %s AND s.fiscal_period = %s
              AND s.financial_statement = 'Statement of Financial Position'
        ORDER BY ABS(s.value) DESC
    """, (ticker.upper(), fiscal_year, fiscal_period))
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail=f"No balance sheet found for {ticker}")
    
    return {
        "ticker": ticker.upper(),
        "fiscal_year": fiscal_year,
        "fiscal_period": fiscal_period,
        "statement_type": "Statement of Financial Position",
        "data": format_financial_data(rows, format == "detailed", currency)
    }

@app.get("/cash-flow/{ticker}/latest")
def get_latest_cash_flow(
    ticker: str,
    format: str = Query("standard", description="Response format: standard or detailed"),
    currency: str = Query("actual", description="Currency format: actual, millions, or billions")
):
    """Get the latest cash flow statement"""
    conn = get_connection()
    latest = get_latest_period(conn, ticker)
    if not latest:
        raise HTTPException(status_code=404, detail=f"No data found for {ticker}")
    
    fiscal_year, fiscal_period, _ = latest
    
    cur = conn.cursor()
    cur.execute("""
        SELECT s.tag, s.value, s.unit, s.start_date, s.end_date, s.fiscal_year, s.fiscal_period,
               s.standard_label, s.documentation, s.financial_statement
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s AND s.fiscal_year = %s AND s.fiscal_period = %s
              AND s.financial_statement = 'Statement of Cash Flows'
        ORDER BY ABS(s.value) DESC
    """, (ticker.upper(), fiscal_year, fiscal_period))
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail=f"No cash flow statement found for {ticker}")
    
    return {
        "ticker": ticker.upper(),
        "fiscal_year": fiscal_year,
        "fiscal_period": fiscal_period,
        "statement_type": "Statement of Cash Flows",
        "data": format_financial_data(rows, format == "detailed", currency)
    }

@app.get("/equity-statement/{ticker}/latest")
def get_latest_equity_statement(
    ticker: str,
    format: str = Query("standard", description="Response format: standard or detailed"),
    currency: str = Query("actual", description="Currency format: actual, millions, or billions")
):
    """Get the latest stockholders equity statement"""
    conn = get_connection()
    latest = get_latest_period(conn, ticker)
    if not latest:
        raise HTTPException(status_code=404, detail=f"No data found for {ticker}")
    
    fiscal_year, fiscal_period, _ = latest
    
    cur = conn.cursor()
    cur.execute("""
        SELECT s.tag, s.value, s.unit, s.start_date, s.end_date, s.fiscal_year, s.fiscal_period,
               s.standard_label, s.documentation, s.financial_statement
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s AND s.fiscal_year = %s AND s.fiscal_period = %s
              AND s.financial_statement = 'Statement of Stockholders Equity'
        ORDER BY ABS(s.value) DESC
    """, (ticker.upper(), fiscal_year, fiscal_period))
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail=f"No equity statement found for {ticker}")
    
    return {
        "ticker": ticker.upper(),
        "fiscal_year": fiscal_year,
        "fiscal_period": fiscal_period,
        "statement_type": "Statement of Stockholders Equity",
        "data": format_financial_data(rows, format == "detailed", currency)
    }

# Latest by Period Type
@app.get("/income-statement/{ticker}/latest-annual")
def get_latest_annual_income_statement(
    ticker: str,
    format: str = Query("standard", description="Response format: standard or detailed"),
    currency: str = Query("actual", description="Currency format: actual, millions, or billions")
):
    """Get the most recent annual income statement"""
    conn = get_connection()
    latest = get_latest_period(conn, ticker, "annual")
    if not latest:
        raise HTTPException(status_code=404, detail=f"No annual data found for {ticker}")
    
    fiscal_year, fiscal_period, _ = latest
    
    cur = conn.cursor()
    cur.execute("""
        SELECT s.tag, s.value, s.unit, s.start_date, s.end_date, s.fiscal_year, s.fiscal_period,
               s.standard_label, s.documentation, s.financial_statement
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s AND s.fiscal_year = %s AND s.fiscal_period = %s
              AND s.financial_statement = 'Statement of Income'
        ORDER BY ABS(s.value) DESC
    """, (ticker.upper(), fiscal_year, fiscal_period))
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail=f"No annual income statement found for {ticker}")
    
    return {
        "ticker": ticker.upper(),
        "fiscal_year": fiscal_year,
        "fiscal_period": fiscal_period,
        "period_type": "annual",
        "statement_type": "Statement of Income",
        "data": format_financial_data(rows, format == "detailed", currency)
    }

@app.get("/income-statement/{ticker}/latest-quarterly")
def get_latest_quarterly_income_statement(
    ticker: str,
    format: str = Query("standard", description="Response format: standard or detailed"),
    currency: str = Query("actual", description="Currency format: actual, millions, or billions")
):
    """Get the most recent quarterly income statement"""
    conn = get_connection()
    latest = get_latest_period(conn, ticker, "quarterly")
    if not latest:
        raise HTTPException(status_code=404, detail=f"No quarterly data found for {ticker}")
    
    fiscal_year, fiscal_period, _ = latest
    
    cur = conn.cursor()
    cur.execute("""
        SELECT s.tag, s.value, s.unit, s.start_date, s.end_date, s.fiscal_year, s.fiscal_period,
               s.standard_label, s.documentation, s.financial_statement
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s AND s.fiscal_year = %s AND s.fiscal_period = %s
              AND s.financial_statement = 'Statement of Income'
        ORDER BY ABS(s.value) DESC
    """, (ticker.upper(), fiscal_year, fiscal_period))
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail=f"No quarterly income statement found for {ticker}")
    
    return {
        "ticker": ticker.upper(),
        "fiscal_year": fiscal_year,
        "fiscal_period": fiscal_period,
        "period_type": "quarterly",
        "statement_type": "Statement of Income",
        "data": format_financial_data(rows, format == "detailed", currency)
    }


# Quarter-Based Range Endpoints
@app.get("/income-statement/{ticker}/quarters")
def get_income_statement_quarters(
    ticker: str,
    count: int = Query(4, description="Number of quarters to retrieve"),
    format: str = Query("standard", description="Response format: standard or detailed"),
    currency: str = Query("actual", description="Currency format: actual, millions, or billions")
):
    """Get income statement data for the last N quarters"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Get the last N quarters
    cur.execute("""
        SELECT DISTINCT s.fiscal_year, s.fiscal_period, MAX(s.end_date) as end_date
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s AND s.fiscal_period != 'FY'
        GROUP BY s.fiscal_year, s.fiscal_period
        ORDER BY end_date DESC
        LIMIT %s
    """, (ticker.upper(), count))
    
    periods = cur.fetchall()
    if not periods:
        raise HTTPException(status_code=404, detail=f"No quarterly data found for {ticker}")
    
    result_periods = []
    
    for fiscal_year, fiscal_period, end_date in periods:
        cur.execute("""
            SELECT s.tag, s.value, s.unit, s.start_date, s.end_date, s.fiscal_year, s.fiscal_period,
                   s.standard_label, s.documentation, s.financial_statement
            FROM statements s
            JOIN companies c ON c.id = s.company_id
            WHERE c.ticker = %s AND s.fiscal_year = %s AND s.fiscal_period = %s
                  AND s.financial_statement = 'Statement of Income'
            ORDER BY ABS(s.value) DESC
        """, (ticker.upper(), fiscal_year, fiscal_period))
        
        rows = cur.fetchall()
        if rows:
            period_data = {
                "fiscal_year": fiscal_year,
                "fiscal_period": fiscal_period,
                "end_date": str(end_date),
                "data": format_financial_data(rows, format == "detailed", currency)
            }
            result_periods.append(period_data)
    
    cur.close()
    conn.close()
    
    return {
        "ticker": ticker.upper(),
        "statement_type": "Statement of Income",
        "period_type": "quarterly",
        "periods_requested": count,
        "periods_returned": len(result_periods),
        "periods": result_periods
    }

@app.get("/balance-sheet/{ticker}/quarters")
def get_balance_sheet_quarters(
    ticker: str,
    count: int = Query(4, description="Number of quarters to retrieve"),
    format: str = Query("standard", description="Response format: standard or detailed"),
    currency: str = Query("actual", description="Currency format: actual, millions, or billions")
):
    """Get balance sheet data for the last N quarters"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT DISTINCT s.fiscal_year, s.fiscal_period, MAX(s.end_date) as end_date
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s AND s.fiscal_period != 'FY'
        GROUP BY s.fiscal_year, s.fiscal_period
        ORDER BY end_date DESC
        LIMIT %s
    """, (ticker.upper(), count))
    
    periods = cur.fetchall()
    if not periods:
        raise HTTPException(status_code=404, detail=f"No quarterly data found for {ticker}")
    
    result_periods = []
    
    for fiscal_year, fiscal_period, end_date in periods:
        cur.execute("""
            SELECT s.tag, s.value, s.unit, s.start_date, s.end_date, s.fiscal_year, s.fiscal_period,
                   s.standard_label, s.documentation, s.financial_statement
            FROM statements s
            JOIN companies c ON c.id = s.company_id
            WHERE c.ticker = %s AND s.fiscal_year = %s AND s.fiscal_period = %s
                  AND s.financial_statement = 'Statement of Financial Position'
            ORDER BY ABS(s.value) DESC
        """, (ticker.upper(), fiscal_year, fiscal_period))
        
        rows = cur.fetchall()
        if rows:
            period_data = {
                "fiscal_year": fiscal_year,
                "fiscal_period": fiscal_period,
                "end_date": str(end_date),
                "data": format_financial_data(rows, format == "detailed", currency)
            }
            result_periods.append(period_data)
    
    cur.close()
    conn.close()
    
    return {
        "ticker": ticker.upper(),
        "statement_type": "Statement of Financial Position",
        "period_type": "quarterly",
        "periods_requested": count,
        "periods_returned": len(result_periods),
        "periods": result_periods
    }

@app.get("/cash-flow/{ticker}/quarters")
def get_cash_flow_quarters(
    ticker: str,
    count: int = Query(4, description="Number of quarters to retrieve"),
    format: str = Query("standard", description="Response format: standard or detailed"),
    currency: str = Query("actual", description="Currency format: actual, millions, or billions")
):
    """Get cash flow data for the last N quarters"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT DISTINCT s.fiscal_year, s.fiscal_period, MAX(s.end_date) as end_date
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s AND s.fiscal_period != 'FY'
        GROUP BY s.fiscal_year, s.fiscal_period
        ORDER BY end_date DESC
        LIMIT %s
    """, (ticker.upper(), count))
    
    periods = cur.fetchall()
    if not periods:
        raise HTTPException(status_code=404, detail=f"No quarterly data found for {ticker}")
    
    result_periods = []
    
    for fiscal_year, fiscal_period, end_date in periods:
        cur.execute("""
            SELECT s.tag, s.value, s.unit, s.start_date, s.end_date, s.fiscal_year, s.fiscal_period,
                   s.standard_label, s.documentation, s.financial_statement
            FROM statements s
            JOIN companies c ON c.id = s.company_id
            WHERE c.ticker = %s AND s.fiscal_year = %s AND s.fiscal_period = %s
                  AND s.financial_statement = 'Statement of Cash Flows'
            ORDER BY ABS(s.value) DESC
        """, (ticker.upper(), fiscal_year, fiscal_period))
        
        rows = cur.fetchall()
        if rows:
            period_data = {
                "fiscal_year": fiscal_year,
                "fiscal_period": fiscal_period,
                "end_date": str(end_date),
                "data": format_financial_data(rows, format == "detailed", currency)
            }
            result_periods.append(period_data)
    
    cur.close()
    conn.close()
    
    return {
        "ticker": ticker.upper(),
        "statement_type": "Statement of Cash Flows",
        "period_type": "quarterly",
        "periods_requested": count,
        "periods_returned": len(result_periods),
        "periods": result_periods
    }


# Year-Based Range Endpoints
@app.get("/income-statement/{ticker}/years")
def get_income_statement_years(
    ticker: str,
    count: int = Query(5, description="Number of years to retrieve"),
    format: str = Query("standard", description="Response format: standard or detailed"),
    currency: str = Query("actual", description="Currency format: actual, millions, or billions")
):
    """Get annual income statement data for the last N years"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT DISTINCT s.fiscal_year, MAX(s.end_date) as end_date
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s AND s.fiscal_period = 'FY'
        GROUP BY s.fiscal_year
        ORDER BY s.fiscal_year DESC
        LIMIT %s
    """, (ticker.upper(), count))
    
    years = cur.fetchall()
    if not years:
        raise HTTPException(status_code=404, detail=f"No annual data found for {ticker}")
    
    result_periods = []
    
    for fiscal_year, end_date in years:
        cur.execute("""
            SELECT s.tag, s.value, s.unit, s.start_date, s.end_date, s.fiscal_year, s.fiscal_period,
                   s.standard_label, s.documentation, s.financial_statement
            FROM statements s
            JOIN companies c ON c.id = s.company_id
            WHERE c.ticker = %s AND s.fiscal_year = %s AND s.fiscal_period = 'FY'
                  AND s.financial_statement = 'Statement of Income'
            ORDER BY ABS(s.value) DESC
        """, (ticker.upper(), fiscal_year))
        
        rows = cur.fetchall()
        if rows:
            period_data = {
                "fiscal_year": fiscal_year,
                "fiscal_period": "FY",
                "end_date": str(end_date),
                "data": format_financial_data(rows, format == "detailed", currency)
            }
            result_periods.append(period_data)
    
    cur.close()
    conn.close()
    
    return {
        "ticker": ticker.upper(),
        "statement_type": "Statement of Income",
        "period_type": "annual",
        "periods_requested": count,
        "periods_returned": len(result_periods),
        "periods": result_periods
    }

@app.get("/balance-sheet/{ticker}/years")
def get_balance_sheet_years(
    ticker: str,
    count: int = Query(5, description="Number of years to retrieve"),
    format: str = Query("standard", description="Response format: standard or detailed"),
    currency: str = Query("actual", description="Currency format: actual, millions, or billions")
):
    """Get annual balance sheet data for the last N years"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT DISTINCT s.fiscal_year, MAX(s.end_date) as end_date
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s AND s.fiscal_period = 'FY'
        GROUP BY s.fiscal_year
        ORDER BY s.fiscal_year DESC
        LIMIT %s
    """, (ticker.upper(), count))
    
    years = cur.fetchall()
    if not years:
        raise HTTPException(status_code=404, detail=f"No annual data found for {ticker}")
    
    result_periods = []
    
    for fiscal_year, end_date in years:
        cur.execute("""
            SELECT s.tag, s.value, s.unit, s.start_date, s.end_date, s.fiscal_year, s.fiscal_period,
                   s.standard_label, s.documentation, s.financial_statement
            FROM statements s
            JOIN companies c ON c.id = s.company_id
            WHERE c.ticker = %s AND s.fiscal_year = %s AND s.fiscal_period = 'FY'
                  AND s.financial_statement = 'Statement of Financial Position'
            ORDER BY ABS(s.value) DESC
        """, (ticker.upper(), fiscal_year))
        
        rows = cur.fetchall()
        if rows:
            period_data = {
                "fiscal_year": fiscal_year,
                "fiscal_period": "FY",
                "end_date": str(end_date),
                "data": format_financial_data(rows, format == "detailed", currency)
            }
            result_periods.append(period_data)
    
    cur.close()
    conn.close()
    
    return {
        "ticker": ticker.upper(),
        "statement_type": "Statement of Financial Position",
        "period_type": "annual",
        "periods_requested": count,
        "periods_returned": len(result_periods),
        "periods": result_periods
    }


# Flexible Date Range Endpoints  
@app.get("/income-statement/{ticker}/range")
def get_income_statement_range(
    ticker: str,
    from_year: int = Query(..., alias="from", description="Starting fiscal year"),
    to_year: int = Query(..., alias="to", description="Ending fiscal year"),
    format: str = Query("standard", description="Response format: standard or detailed"),
    currency: str = Query("actual", description="Currency format: actual, millions, or billions")
):
    """Get income statement data for a specific year range"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT DISTINCT s.fiscal_year, s.fiscal_period, MAX(s.end_date) as end_date
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s AND s.fiscal_year BETWEEN %s AND %s
        GROUP BY s.fiscal_year, s.fiscal_period
        ORDER BY s.fiscal_year DESC, s.end_date DESC
    """, (ticker.upper(), from_year, to_year))
    
    periods = cur.fetchall()
    if not periods:
        raise HTTPException(status_code=404, detail=f"No data found for {ticker} between {from_year} and {to_year}")
    
    result_periods = []
    
    for fiscal_year, fiscal_period, end_date in periods:
        cur.execute("""
            SELECT s.tag, s.value, s.unit, s.start_date, s.end_date, s.fiscal_year, s.fiscal_period,
                   s.standard_label, s.documentation, s.financial_statement
            FROM statements s
            JOIN companies c ON c.id = s.company_id
            WHERE c.ticker = %s AND s.fiscal_year = %s AND s.fiscal_period = %s
                  AND s.financial_statement = 'Statement of Income'
            ORDER BY ABS(s.value) DESC
        """, (ticker.upper(), fiscal_year, fiscal_period))
        
        rows = cur.fetchall()
        if rows:
            period_data = {
                "fiscal_year": fiscal_year,
                "fiscal_period": fiscal_period,
                "end_date": str(end_date),
                "data": format_financial_data(rows, format == "detailed", currency)
            }
            result_periods.append(period_data)
    
    cur.close()
    conn.close()
    
    return {
        "ticker": ticker.upper(),
        "statement_type": "Statement of Income",
        "date_range": f"{from_year} to {to_year}",
        "periods_returned": len(result_periods),
        "periods": result_periods
    }

@app.get("/balance-sheet/{ticker}/range")
def get_balance_sheet_range(
    ticker: str,
    from_year: int = Query(..., alias="from", description="Starting fiscal year"),
    to_year: int = Query(..., alias="to", description="Ending fiscal year"),
    format: str = Query("standard", description="Response format: standard or detailed"),
    currency: str = Query("actual", description="Currency format: actual, millions, or billions")
):
    """Get balance sheet data for a specific year range"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT DISTINCT s.fiscal_year, s.fiscal_period, MAX(s.end_date) as end_date
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s AND s.fiscal_year BETWEEN %s AND %s
        GROUP BY s.fiscal_year, s.fiscal_period
        ORDER BY s.fiscal_year DESC, s.end_date DESC
    """, (ticker.upper(), from_year, to_year))
    
    periods = cur.fetchall()
    if not periods:
        raise HTTPException(status_code=404, detail=f"No data found for {ticker} between {from_year} and {to_year}")
    
    result_periods = []
    
    for fiscal_year, fiscal_period, end_date in periods:
        cur.execute("""
            SELECT s.tag, s.value, s.unit, s.start_date, s.end_date, s.fiscal_year, s.fiscal_period,
                   s.standard_label, s.documentation, s.financial_statement
            FROM statements s
            JOIN companies c ON c.id = s.company_id
            WHERE c.ticker = %s AND s.fiscal_year = %s AND s.fiscal_period = %s
                  AND s.financial_statement = 'Statement of Financial Position'
            ORDER BY ABS(s.value) DESC
        """, (ticker.upper(), fiscal_year, fiscal_period))
        
        rows = cur.fetchall()
        if rows:
            period_data = {
                "fiscal_year": fiscal_year,
                "fiscal_period": fiscal_period,
                "end_date": str(end_date),
                "data": format_financial_data(rows, format == "detailed", currency)
            }
            result_periods.append(period_data)
    
    cur.close()
    conn.close()
    
    return {
        "ticker": ticker.upper(),
        "statement_type": "Statement of Financial Position",
        "date_range": f"{from_year} to {to_year}",
        "periods_returned": len(result_periods),
        "periods": result_periods
    }

@app.get("/cash-flow/{ticker}/range")
def get_cash_flow_range(
    ticker: str,
    from_year: int = Query(..., alias="from", description="Starting fiscal year"),
    to_year: int = Query(..., alias="to", description="Ending fiscal year"),
    format: str = Query("standard", description="Response format: standard or detailed"),
    currency: str = Query("actual", description="Currency format: actual, millions, or billions")
):
    """Get cash flow data for a specific year range"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT DISTINCT s.fiscal_year, s.fiscal_period, MAX(s.end_date) as end_date
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s AND s.fiscal_year BETWEEN %s AND %s
        GROUP BY s.fiscal_year, s.fiscal_period
        ORDER BY s.fiscal_year DESC, s.end_date DESC
    """, (ticker.upper(), from_year, to_year))
    
    periods = cur.fetchall()
    if not periods:
        raise HTTPException(status_code=404, detail=f"No data found for {ticker} between {from_year} and {to_year}")
    
    result_periods = []
    
    for fiscal_year, fiscal_period, end_date in periods:
        cur.execute("""
            SELECT s.tag, s.value, s.unit, s.start_date, s.end_date, s.fiscal_year, s.fiscal_period,
                   s.standard_label, s.documentation, s.financial_statement
            FROM statements s
            JOIN companies c ON c.id = s.company_id
            WHERE c.ticker = %s AND s.fiscal_year = %s AND s.fiscal_period = %s
                  AND s.financial_statement = 'Statement of Cash Flows'
            ORDER BY ABS(s.value) DESC
        """, (ticker.upper(), fiscal_year, fiscal_period))
        
        rows = cur.fetchall()
        if rows:
            period_data = {
                "fiscal_year": fiscal_year,
                "fiscal_period": fiscal_period,
                "end_date": str(end_date),
                "data": format_financial_data(rows, format == "detailed", currency)
            }
            result_periods.append(period_data)
    
    cur.close()
    conn.close()
    
    return {
        "ticker": ticker.upper(),
        "statement_type": "Statement of Cash Flows",
        "date_range": f"{from_year} to {to_year}",
        "periods_returned": len(result_periods),
        "periods": result_periods
    }

@app.get("/company-metrics/{ticker}")
def get_company_metrics(ticker: str):
    """Get key financial metrics for company overview"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Get the latest annual data for calculations
    latest = get_latest_period(conn, ticker, "annual")
    if not latest:
        raise HTTPException(status_code=404, detail=f"No annual data found for {ticker}")
    
    fiscal_year, fiscal_period, _ = latest
    
    # Get current year data
    cur.execute("""
        SELECT s.tag, s.value, s.unit
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s AND s.fiscal_year = %s AND s.fiscal_period = %s
    """, (ticker.upper(), fiscal_year, fiscal_period))
    
    current_data = {tag: float(value) for tag, value, unit in cur.fetchall()}
    
    # Get previous year data for growth calculations
    prev_year = fiscal_year - 1
    cur.execute("""
        SELECT s.tag, s.value, s.unit
        FROM statements s
        JOIN companies c ON c.id = s.company_id
        WHERE c.ticker = %s AND s.fiscal_year = %s AND s.fiscal_period = 'FY'
    """, (ticker.upper(), prev_year))
    
    prev_data = {tag: float(value) for tag, value, unit in cur.fetchall()}
    
    cur.close()
    conn.close()
    
    # Calculate metrics
    metrics = {}
    
    # Revenue and Revenue Growth
    revenue_current = current_data.get('RevenueFromContractWithCustomerExcludingAssessedTax', 0)
    revenue_prev = prev_data.get('RevenueFromContractWithCustomerExcludingAssessedTax', 0)
    if revenue_prev > 0:
        revenue_growth = ((revenue_current - revenue_prev) / revenue_prev) * 100
    else:
        revenue_growth = 0
    
    metrics['revenue'] = revenue_current
    metrics['revenue_growth'] = revenue_growth
    
    # Free Cash Flow (Operating Cash Flow - Capital Expenditures)
    operating_cf = current_data.get('NetCashProvidedByUsedInOperatingActivities', 0)
    capex = current_data.get('PaymentsToAcquirePropertyPlantAndEquipment', 0)
    free_cash_flow = operating_cf - abs(capex)  # capex is usually negative
    metrics['free_cash_flow'] = free_cash_flow
    
    # Net Profit Margin
    net_income = current_data.get('NetIncomeLoss', 0)
    if revenue_current > 0:
        net_margin = (net_income / revenue_current) * 100
    else:
        net_margin = 0
    metrics['net_margin'] = net_margin
    
    # Return on Equity (ROE)
    stockholders_equity = current_data.get('StockholdersEquity', 0)
    if stockholders_equity > 0:
        roe = (net_income / stockholders_equity) * 100
    else:
        roe = 0
    metrics['roe'] = roe
    
    # Debt-to-Equity Ratio
    total_debt = current_data.get('LongTermDebt', 0) + current_data.get('ShortTermBorrowings', 0)
    if stockholders_equity > 0:
        debt_to_equity = total_debt / stockholders_equity
    else:
        debt_to_equity = 0
    metrics['debt_to_equity'] = debt_to_equity
    
    return {
        "ticker": ticker.upper(),
        "fiscal_year": fiscal_year,
        "metrics": metrics
    }
