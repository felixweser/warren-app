import { useState, useEffect } from 'react';

interface CompanyComparisonTableProps {
  currentStock?: any;
}

interface CompanyMetrics {
  ticker: string;
  name: string;
  revenue: number;
  free_cash_flow: number;
  net_margin: number;
  roe: number;
  debt_to_equity: number;
}

export default function CompanyComparisonTable({ currentStock }: CompanyComparisonTableProps) {
  const [companyData, setCompanyData] = useState<CompanyMetrics[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Define peer companies based on selected stock
  const getPeerCompanies = (ticker: string) => {
    const peers: { [key: string]: string[] } = {
      'GOOGL': ['MSFT', 'AAPL', 'META', 'AMZN'],
      'AAPL': ['MSFT', 'GOOGL', 'META', 'NVDA'],
      'MSFT': ['AAPL', 'GOOGL', 'AMZN', 'META'],
      // Add more peer mappings as needed
    };
    return peers[ticker] || ['AAPL', 'MSFT', 'GOOGL']; // Default peers
  };

  useEffect(() => {
    const fetchComparisonData = async () => {
      if (!currentStock?.symbol) return;
      
      setLoading(true);
      setError(null);
      
      try {
        // Get current company + peers
        const allTickers = [currentStock.symbol, ...getPeerCompanies(currentStock.symbol)];
        const promises = allTickers.map(async (ticker) => {
          try {
            const [metricsResponse, companiesResponse] = await Promise.all([
              fetch(`http://localhost:8000/company-metrics/${ticker}`),
              fetch(`http://localhost:8000/companies`)
            ]);
            
            if (metricsResponse.ok) {
              const metricsData = await metricsResponse.json();
              const companiesData = await companiesResponse.json();
              const companyInfo = companiesData.find((c: any) => c.ticker === ticker);
              
              return {
                ticker: ticker,
                name: companyInfo?.name || ticker,
                ...metricsData.metrics
              };
            }
            return null;
          } catch (err) {
            console.warn(`Failed to fetch data for ${ticker}:`, err);
            return null;
          }
        });
        
        const results = await Promise.all(promises);
        const validResults = results.filter(Boolean) as CompanyMetrics[];
        setCompanyData(validResults);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch comparison data');
        console.error('Error fetching comparison data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchComparisonData();
  }, [currentStock?.symbol]);

  // Helper functions for formatting
  const formatCurrency = (value: number) => {
    if (value >= 1e12) return `$${(value / 1e12).toFixed(1)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercentage = (value: number) => `${value.toFixed(1)}%`;
  const formatRatio = (value: number) => value.toFixed(2);

  const metrics = [
    { key: 'revenue', label: 'Revenue', format: 'currency' },
    { key: 'free_cash_flow', label: 'Free Cash Flow', format: 'currency' },
    { key: 'net_margin', label: 'Net Margin', format: 'percentage' },
    { key: 'roe', label: 'Return on Equity', format: 'percentage' },
    { key: 'debt_to_equity', label: 'Debt/Equity Ratio', format: 'ratio' },
  ];

  const formatValue = (value: number, format: string) => {
    switch (format) {
      case 'currency': return formatCurrency(value);
      case 'percentage': return formatPercentage(value);
      case 'ratio': return formatRatio(value);
      default: return value.toString();
    }
  };

  if (!currentStock?.symbol) {
    return (
      <div className="w-full mt-8 p-4 bg-[#1a1a1a] border border-[#333333] rounded-2xl shadow-lg">
        <h2 className="text-xl font-bold text-slate-50 mb-4">Company Comparison</h2>
        <div className="flex justify-center items-center h-32">
          <div className="text-slate-400">Select a company to view peer comparison</div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full mt-4 bg-[#1a1a1a]">
      <h2 className="text-xl font-bold text-slate-50 mb-4 px-4">
        Company Comparison - {currentStock.symbol} vs Peers
      </h2>
      <div>
      
      {loading && (
        <div className="flex justify-center items-center h-32">
          <div className="text-slate-400">Loading comparison data...</div>
        </div>
      )}
      
      {error && (
        <div className="flex justify-center items-center h-32">
          <div className="text-red-400">Error: {error}</div>
        </div>
      )}
      
      {!loading && !error && companyData.length > 0 && (
        <div className="border border-[#333333] rounded-2xl shadow-lg overflow-x-auto">
          <table className="w-full  rounded-xl overflow-hidden shadow-lg bg-[#2a2a2a]">
            <thead>
              <tr className="bg-[#2a2a2a]">
                <th className=" text-left p-4 text-sm font-semibold text-slate-50">
                  
                </th>
                {companyData.map((company, index) => (
                  <th 
                    key={company.ticker} 
                    className={`px-4 py-3 text-center text-sm font-semibold  ${
                      index === 0 ? 'text-[#7EE081]' : 'text-slate-50'
                    }`}
                  >
                    <div className="text-center">{company.ticker}</div>
                    <div className="text-xs font-normal text-slate-400 mt-1 text-center">
                      {company.name}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {metrics.map((metric) => (
                <tr key={metric.key} className="hover:bg-[#333333] transition-colors">
                  <td className="px-4 py-3 text-sm text-slate-50 font-medium ">
                    {metric.label}
                  </td>
                  {companyData.map((company, companyIndex) => {
                    const value = (company as any)[metric.key];
                    return (
                      <td 
                        key={`${company.ticker}-${metric.key}`}
                        className={`px-4 py-3 text-sm text-center ${
                          companyIndex === 0 ? 'font-semibold text-[#7EE081]' : 'text-slate-50'
                        }`}
                      >
                        {value !== undefined ? formatValue(value, metric.format) : 'N/A'}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      {!loading && !error && companyData.length === 0 && (
        <div className="flex justify-center items-center h-32">
          <div className="text-slate-400">No comparison data available</div>
        </div>
      )}
      
        <div className="mt-4 px-4 text-xs text-slate-50">
          <span className="text-[#7EE081]">●</span> Selected Company
          <span className="text-slate-50 ml-4">●</span> Peer Companies
        </div>
      </div>
    </div>
  );
}