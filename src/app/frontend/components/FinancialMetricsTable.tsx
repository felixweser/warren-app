import { useState, useEffect } from 'react';

interface FinancialMetricsTableProps {
  currentStock?: any;
}

interface MetricData {
  revenue: number;
  revenue_growth: number;
  free_cash_flow: number;
  net_margin: number;
  roe: number;
  debt_to_equity: number;
}

export default function FinancialMetricsTable({ currentStock }: FinancialMetricsTableProps) {
  const [metrics, setMetrics] = useState<MetricData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch metrics when currentStock changes
  useEffect(() => {
    const fetchMetrics = async () => {
      if (!currentStock?.symbol) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch(`http://localhost:8000/company-metrics/${currentStock.symbol}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch metrics: ${response.statusText}`);
        }
        const data = await response.json();
        setMetrics(data.metrics);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch metrics');
        console.error('Error fetching metrics:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, [currentStock?.symbol]);

  // Helper function to format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Helper function to format percentages
  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  // Create metrics array from fetched data
  const metricsArray = metrics ? [
    {
      name: 'Revenue',
      value: metrics.revenue,
      type: 'revenue',
      format: 'currency'
    },
    {
      name: 'Free Cash Flow',
      value: metrics.free_cash_flow,
      type: 'free_cash_flow', 
      format: 'currency'
    },
    {
      name: 'Net Profit Margin',
      value: metrics.net_margin,
      type: 'net_margin',
      format: 'percentage'
    },
    {
      name: 'Return on Equity (ROE)',
      value: metrics.roe,
      type: 'roe',
      format: 'percentage'
    },
    {
      name: 'Debt-to-Equity Ratio',
      value: metrics.debt_to_equity,
      type: 'debt_to_equity',
      format: 'ratio'
    }
  ] : [];

  const formatValue = (value: number, format: string) => {
    switch (format) {
      case 'currency':
        return formatCurrency(value);
      case 'percentage':
        return formatPercentage(value);
      case 'ratio':
        return value.toFixed(2);
      default:
        return value.toString();
    }
  };

  return (
    <div className="w-1/4 min-h-[500px] overflow-x-auto bg-[#1a1a1a]">
      <h2 className="text-xl font-bold text-slate-50 mb-4 px-4">Key Financial Metrics</h2>
      <div className="w-full min-h-[450px] overflow-x-auto p-4 bg-[#2a2a2a] border border-[#333333] rounded-2xl shadow-lg">
        {loading && (
          <div className="flex justify-center items-center h-32">
            <div className="text-slate-400">Loading metrics...</div>
          </div>
        )}
        
        {error && (
          <div className="flex justify-center items-center h-32">
            <div className="text-red-400">Error: {error}</div>
          </div>
        )}
        
        {!loading && !error && !currentStock?.symbol && (
          <div className="flex justify-center items-center h-32">
            <div className="text-slate-400">Select a company to view metrics</div>
          </div>
        )}
        
        {!loading && !error && metricsArray.length > 0 && (
          <table className="w-full rounded-xl overflow-hidden">
            <tbody>
              {metricsArray.map((metric, index) => (
                <tr key={index} className="hover:bg-[#333333] transition-colors">
                  <td className="px-4 py-4 text-sm text-slate-50">{metric.name}</td>
                  <td className="px-4 py-4 text-sm font-semibold text-slate-50">
                    {formatValue(metric.value, metric.format)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        
        {/* Optional: Add a small legend or note */}
        <div className="mt-8 px-4 text-xs text-slate-50">
          <p>Compared to peers:</p>
          <div className="mt-3 text-xs text-slate-50">
            <span className="text-green-600">●</span> Above Average 
            <span className="text-yellow-600 ml-3">●</span> Average 
            <span className="text-red-600 ml-3">●</span> Below Average
          </div>
        </div>
      </div>
    </div>
  );
}