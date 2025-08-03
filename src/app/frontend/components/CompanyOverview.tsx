interface CompanyOverviewProps {
  currentStock?: any;
}

export default function CompanyOverview({ currentStock }: CompanyOverviewProps) {
  return (
    <div className="p-4 rounded-lg shadow-md">
      <button className="bg-[#1a1a1a] border border-[#333333] hover:bg-[#2a2a2a] text-[#666666] hover:text-white flex items-center gap-2 px-3 py-1.5 rounded-lg cursor-pointer transition">
        <span className="font-medium text-sm">Company Overview Button</span>
      </button>
    </div>
  );
}