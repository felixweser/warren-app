// src/app/page.tsx
import CompanyInfo from "./frontend/components/CompanyInfo";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#0a0a0a]">
      {/* Header with navigation */}
      
      {/* Main application */}
      <CompanyInfo />
    </main>
  );
}