interface FinancialTrendsProps {
  currentStock?: any;
}

export default function FinancialTrends({ currentStock }: FinancialTrendsProps) {
  return (
    <div className="w-3/4 min-h-[500px] overflow-x-auto bg-[#1a1a1a] ">
    <h2 className="text-xl font-bold text-slate-50 mb-4 px-4">Financial Trends</h2>
    <div className="w-full min-h-[450px]  p-4 bg-[#2a2a2a] border border-[#333333] rounded-2xl transition-all">
        <div className="h-64">
          {/* Placeholder for Line Chart */}
          <div className="flex justify-center items-center h-full text-slate-400">
            {currentStock?.symbol ? (
              <div className="text-center">
                <div className="text-lg mb-2">Chart for {currentStock.symbol}</div>
                <div className="text-sm">Line chart will be implemented here</div>
              </div>
            ) : (
              <div className="text-center">
                <div className="text-lg mb-2">Select a company</div>
                <div className="text-sm">to view financial trends</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}