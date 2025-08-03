# Additional Enhanced Endpoints - To be added to main.py

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