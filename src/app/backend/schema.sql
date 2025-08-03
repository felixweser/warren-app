CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    cik TEXT UNIQUE NOT NULL,
    ticker TEXT,
    name TEXT
);

CREATE TABLE statements (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    tag TEXT,
    taxonomy TEXT,
    unit TEXT,
    value NUMERIC,
    start_date DATE,
    end_date DATE,
    fiscal_year INTEGER,
    fiscal_period TEXT,
    filing_date DATE,
    standard_label TEXT,
    documentation TEXT,
    financial_statement TEXT,
    UNIQUE(company_id, tag, start_date, end_date)
);

CREATE TABLE gaap_elements (
    id SERIAL PRIMARY KEY,
    element_name TEXT UNIQUE NOT NULL,
    standard_label TEXT,
    documentation TEXT,
    financial_statement TEXT
);