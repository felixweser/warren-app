import FinancialMetricsTable from './FinancialMetricsTable';
import FinancialTrends from './FinancialTrends';
import CompanyComparisonTable from './CompanyComparisonTable';

interface CompanyOverviewProps {
  currentStock?: any;
}

export default function CompanyOverview({ currentStock }: CompanyOverviewProps) {

  return (
    <div className="w-full px-8 my-4">
      {/* Top row with metrics table and trends */}
      <div className="flex gap-8 justify-center items-start">
        <FinancialMetricsTable currentStock={currentStock} />
        <FinancialTrends currentStock={currentStock} />
      </div>
      
      {/* Bottom row with comparison table */}
      <CompanyComparisonTable currentStock={currentStock} />
    </div>
  );
}