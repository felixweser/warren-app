// src/app/page.tsx
import CompanyInfo from "./frontend/components/CompanyInfo";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#0a0a0a]">
      {/* Header with navigation */}
      <div className="flex justify-between items-center bg-[#1a1a1a] border-b border-[#333333] px-4 py-3">
        <h1 className="text-2xl font-bold text-slate-50 hover:text-[#7EE081] transition-colors">
          Graham
        </h1>
      </div>
      
      {/* Main application */}
      <CompanyInfo />
    </main>
  );
}