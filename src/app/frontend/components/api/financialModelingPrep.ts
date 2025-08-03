// API service for connecting to our enhanced financial backend
import { 
  FinancialStatement, 
  LatestFinancialStatement, 
  AllFinancialStatements,
  Company 
} from '../types';

const BASE_URL = 'http://localhost:8000'; // Update this to match your backend port

class FinancialApiService {
  private async fetchApi<T>(endpoint: string): Promise<T> {
    try {
      const response = await fetch(`${BASE_URL}${endpoint}`);
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status} - ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch ${endpoint}:`, error);
      throw error;
    }
  }

  // Get all companies available in the database
  async getCompanies(): Promise<Company[]> {
    const response = await this.fetchApi<{ticker: string, name: string}[]>('/companies');
    return response.map(company => ({
      symbol: company.ticker,
      name: company.name
    }));
  }

  // Latest Financial Statements
  async getLatestFinancialStatements(ticker: string, format: 'standard' | 'detailed' = 'standard'): Promise<AllFinancialStatements> {
    return this.fetchApi<AllFinancialStatements>(`/financial-statements/${ticker}/latest?format=${format}`);
  }

  async getLatestIncomeStatement(ticker: string, format: 'standard' | 'detailed' = 'standard'): Promise<LatestFinancialStatement> {
    return this.fetchApi<LatestFinancialStatement>(`/income-statement/${ticker}/latest?format=${format}`);
  }

  async getLatestBalanceSheet(ticker: string, format: 'standard' | 'detailed' = 'standard'): Promise<LatestFinancialStatement> {
    return this.fetchApi<LatestFinancialStatement>(`/balance-sheet/${ticker}/latest?format=${format}`);
  }

  async getLatestCashFlow(ticker: string, format: 'standard' | 'detailed' = 'standard'): Promise<LatestFinancialStatement> {
    return this.fetchApi<LatestFinancialStatement>(`/cash-flow/${ticker}/latest?format=${format}`);
  }

  async getLatestEquityStatement(ticker: string, format: 'standard' | 'detailed' = 'standard'): Promise<LatestFinancialStatement> {
    return this.fetchApi<LatestFinancialStatement>(`/equity-statement/${ticker}/latest?format=${format}`);
  }

  // Period-specific latest
  async getLatestAnnualIncomeStatement(ticker: string, format: 'standard' | 'detailed' = 'standard'): Promise<LatestFinancialStatement> {
    return this.fetchApi<LatestFinancialStatement>(`/income-statement/${ticker}/latest-annual?format=${format}`);
  }

  async getLatestQuarterlyIncomeStatement(ticker: string, format: 'standard' | 'detailed' = 'standard'): Promise<LatestFinancialStatement> {
    return this.fetchApi<LatestFinancialStatement>(`/income-statement/${ticker}/latest-quarterly?format=${format}`);
  }

  // Quarter ranges
  async getIncomeStatementQuarters(
    ticker: string, 
    count: number = 4, 
    format: 'standard' | 'detailed' = 'standard',
    currency: 'actual' | 'millions' | 'billions' = 'actual'
  ): Promise<FinancialStatement> {
    return this.fetchApi<FinancialStatement>(`/income-statement/${ticker}/quarters?count=${count}&format=${format}&currency=${currency}`);
  }

  async getBalanceSheetQuarters(
    ticker: string, 
    count: number = 4, 
    format: 'standard' | 'detailed' = 'standard',
    currency: 'actual' | 'millions' | 'billions' = 'actual'
  ): Promise<FinancialStatement> {
    return this.fetchApi<FinancialStatement>(`/balance-sheet/${ticker}/quarters?count=${count}&format=${format}&currency=${currency}`);
  }

  async getCashFlowQuarters(
    ticker: string, 
    count: number = 4, 
    format: 'standard' | 'detailed' = 'standard',
    currency: 'actual' | 'millions' | 'billions' = 'actual'
  ): Promise<FinancialStatement> {
    return this.fetchApi<FinancialStatement>(`/cash-flow/${ticker}/quarters?count=${count}&format=${format}&currency=${currency}`);
  }

  // Year ranges
  async getIncomeStatementYears(
    ticker: string, 
    count: number = 5, 
    format: 'standard' | 'detailed' = 'standard',
    currency: 'actual' | 'millions' | 'billions' = 'actual'
  ): Promise<FinancialStatement> {
    return this.fetchApi<FinancialStatement>(`/income-statement/${ticker}/years?count=${count}&format=${format}&currency=${currency}`);
  }

  async getBalanceSheetYears(
    ticker: string, 
    count: number = 5, 
    format: 'standard' | 'detailed' = 'standard',
    currency: 'actual' | 'millions' | 'billions' = 'actual'
  ): Promise<FinancialStatement> {
    return this.fetchApi<FinancialStatement>(`/balance-sheet/${ticker}/years?count=${count}&format=${format}&currency=${currency}`);
  }

  // Date ranges
  async getIncomeStatementRange(
    ticker: string,
    fromYear: number,
    toYear: number,
    format: 'standard' | 'detailed' = 'standard',
    currency: 'actual' | 'millions' | 'billions' = 'actual'
  ): Promise<FinancialStatement> {
    return this.fetchApi<FinancialStatement>(`/income-statement/${ticker}/range?from=${fromYear}&to=${toYear}&format=${format}&currency=${currency}`);
  }

  async getBalanceSheetRange(
    ticker: string,
    fromYear: number,
    toYear: number,
    format: 'standard' | 'detailed' = 'standard',
    currency: 'actual' | 'millions' | 'billions' = 'actual'
  ): Promise<FinancialStatement> {
    return this.fetchApi<FinancialStatement>(`/balance-sheet/${ticker}/range?from=${fromYear}&to=${toYear}&format=${format}&currency=${currency}`);
  }

  async getCashFlowRange(
    ticker: string,
    fromYear: number,
    toYear: number,
    format: 'standard' | 'detailed' = 'standard',
    currency: 'actual' | 'millions' | 'billions' = 'actual'
  ): Promise<FinancialStatement> {
    return this.fetchApi<FinancialStatement>(`/cash-flow/${ticker}/range?from=${fromYear}&to=${toYear}&format=${format}&currency=${currency}`);
  }

  // Utility method to format large numbers for display
  formatValue(value: number, currency: 'actual' | 'millions' | 'billions' = 'actual'): string {
    if (value === 0) return '0';
    
    switch (currency) {
      case 'millions':
        return `${(value / 1_000_000).toFixed(1)}M`;
      case 'billions':
        return `${(value / 1_000_000_000).toFixed(2)}B`;
      default:
        return value.toLocaleString();
    }
  }
}

// Create a singleton instance
export const financialApi = new FinancialApiService();
export default financialApi;