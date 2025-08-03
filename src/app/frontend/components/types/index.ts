// Types for the frontend application

export interface Company {
  name: string;
  symbol: string;
}

export interface SidebarProps {
  selectedStocks: Company[];
  currentStock: Company | null;
  onRemoveStock: (symbol: string) => void;
  onAddStock: (company: Company) => void;
  onStockClick: (company: Company) => void;
}

// Financial statement types that will match our backend API
export interface FinancialDataPoint {
  value: number;
  unit: string;
  label: string;
  fiscal_year: number;
  fiscal_period: string;
  start_date?: string;
  end_date?: string;
  tag?: string;
  documentation?: string;
  financial_statement?: string;
}

export interface StatementData {
  [tag: string]: FinancialDataPoint;
}

export interface PeriodData {
  fiscal_year: number;
  fiscal_period: string;
  end_date: string;
  data: StatementData;
}

export interface FinancialStatement {
  ticker: string;
  statement_type: string;
  period_type?: string;
  periods_requested?: number;
  periods_returned: number;
  periods: PeriodData[];
  date_range?: string;
}

export interface LatestFinancialStatement {
  ticker: string;
  fiscal_year: number;
  fiscal_period: string;
  statement_type: string;
  period_type?: string;
  data: StatementData;
}

export interface AllFinancialStatements {
  ticker: string;
  fiscal_year: number;
  fiscal_period: string;
  statements: {
    "Statement of Income"?: StatementData;
    "Statement of Financial Position"?: StatementData;
    "Statement of Cash Flows"?: StatementData;
    "Statement of Stockholders Equity"?: StatementData;
  };
}