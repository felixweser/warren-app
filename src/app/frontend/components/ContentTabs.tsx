'use client';

import { useState } from 'react';
import { Company } from './types';
import IncomeStatementViewer from './IncomeStatementViewer';
import CompanyOverview from './CompanyOverview';

interface ContentTabsProps {
    currentStock: Company;
}

type TabType = 'overview' | 'income' | 'balance' | 'cashflow' | 'equity';

export default function ContentTabs({ currentStock }: ContentTabsProps) {
    const [activeTab, setActiveTab] = useState<TabType>('overview');

    const tabs = [
        { id: 'overview' as TabType, label: 'Overview' },
        { id: 'income' as TabType, label: 'Income Statement' },
        { id: 'balance' as TabType, label: 'Balance Sheet'},
        { id: 'cashflow' as TabType, label: 'Cash Flow' },
        { id: 'equity' as TabType, label: 'Equity' },
    ];

    const renderTabContent = () => {
        switch (activeTab) {
            case 'overview':
                return <CompanyOverview currentStock={currentStock} />;
            case 'income':
                return <IncomeStatementViewer currentStock={currentStock} />;
            case 'balance':
                return (
                    <div className="p-6 text-center text-[#666666]">
                        <h3 className="text-xl font-semibold text-white mb-4">Balance Sheet</h3>
                        <p>Balance Sheet viewer coming soon...</p>
                    </div>
                );
            case 'cashflow':
                return (
                    <div className="p-6 text-center text-[#666666]">
                        <h3 className="text-xl font-semibold text-white mb-4">Cash Flow Statement</h3>
                        <p>Cash Flow viewer coming soon...</p>
                    </div>
                );
            case 'equity':
                return (
                    <div className="p-6 text-center text-[#666666]">
                        <h3 className="text-xl font-semibold text-white mb-4">Stockholders Equity</h3>
                        <p>Equity statement viewer coming soon...</p>
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <div className="flex flex-col h-full">
            {/* Tab Navigation */}
            <div className="bg-[#1a1a1a]  p-4">
                <div className="flex items-center gap-2 flex-wrap">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg cursor-pointer transition border ${
                                activeTab === tab.id
                                    ? 'bg-[#333333] text-white border border-[#7EE081]'
                                    : 'bg-[#1a1a1a] border border-[#333333] hover:bg-[#2a2a2a] text-[#666666] hover:text-white'
                            }`}
                        >
                            <span className="font-medium text-sm">{tab.label}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-auto">
                {renderTabContent()}
            </div>
        </div>
    );
}