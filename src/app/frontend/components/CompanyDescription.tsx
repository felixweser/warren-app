'use client';

import { useState, useEffect } from 'react';
import { Company, AllFinancialStatements } from './types';
import financialApi from './api/financialModelingPrep';

interface CompanyDescriptionProps {
    currentStock: Company;
}

interface KeyInsight {
    title: string;
    value: string;
    description: string;
    trend?: 'positive' | 'negative' | 'neutral';
    icon: string;
    progress?: number;
}

export default function CompanyDescription({ currentStock }: CompanyDescriptionProps) {
    const [financialData, setFinancialData] = useState<AllFinancialStatements | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!currentStock) return;
        loadCompanyData();
    }, [currentStock]);

    const loadCompanyData = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const data = await financialApi.getLatestFinancialStatements(currentStock.symbol, 'standard');
            setFinancialData(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load company data');
            console.error('Error loading company data:', err);
        } finally {
            setLoading(false);
        }
    };

    const formatValue = (value: number): string => {
        if (Math.abs(value) >= 1_000_000_000) {
            return `$${(value / 1_000_000_000).toFixed(2)}B`;
        } else if (Math.abs(value) >= 1_000_000) {
            return `$${(value / 1_000_000).toFixed(1)}M`;
        } else {
            return `$${value.toLocaleString()}`;
        }
    };

    const getKeyInsights = (): KeyInsight[] => {
        if (!financialData) return [];

        const income = financialData.statements["Statement of Income"] || {};
        const balance = financialData.statements["Statement of Financial Position"] || {};

        const insights: KeyInsight[] = [];

        // Revenue insight
        const revenue = income.Revenues?.value || income.RevenueFromContractWithCustomerExcludingAssessedTax?.value;
        if (revenue) {
            insights.push({
                title: "Revenue Performance",
                value: formatValue(revenue),
                description: "Total company revenue demonstrates market reach and business scale",
                trend: revenue > 1_000_000_000 ? 'positive' : 'neutral',
                icon: "📈",
                progress: Math.min((revenue / 10_000_000_000) * 100, 100)
            });
        }

        // Profitability insight
        const netIncome = income.NetIncomeLoss?.value;
        if (netIncome) {
            insights.push({
                title: "Profitability Health",
                value: formatValue(netIncome),
                description: "Net income reflects the company's ability to generate profit",
                trend: netIncome > 0 ? 'positive' : 'negative',
                icon: netIncome > 0 ? "💰" : "⚠️",
                progress: revenue ? Math.min(Math.abs(netIncome / revenue) * 100, 100) : 0
            });
        }

        // Financial strength
        const assets = balance.Assets?.value;
        const liabilities = balance.Liabilities?.value;
        if (assets && liabilities) {
            const debtToAssetRatio = liabilities / assets;
            insights.push({
                title: "Financial Strength",
                value: `${(100 - debtToAssetRatio * 100).toFixed(1)}%`,
                description: "Asset-to-debt ratio indicates financial stability and leverage",
                trend: debtToAssetRatio < 0.6 ? 'positive' : debtToAssetRatio < 0.8 ? 'neutral' : 'negative',
                icon: debtToAssetRatio < 0.6 ? "🛡️" : "⚖️",
                progress: Math.max(0, 100 - debtToAssetRatio * 100)
            });
        }

        // Operating efficiency
        const operatingIncome = income.OperatingIncomeLoss?.value;
        if (operatingIncome && revenue) {
            const operatingMargin = (operatingIncome / revenue) * 100;
            insights.push({
                title: "Operating Efficiency",
                value: `${operatingMargin.toFixed(1)}%`,
                description: "Operating margin shows how efficiently the company runs its core business",
                trend: operatingMargin > 15 ? 'positive' : operatingMargin > 5 ? 'neutral' : 'negative',
                icon: operatingMargin > 15 ? "⚡" : "🔧",
                progress: Math.min(operatingMargin * 5, 100)
            });
        }

        return insights.slice(0, 4); // Limit to top 4 insights
    };

    const getTrendArrow = (trend?: 'positive' | 'negative' | 'neutral') => {
        switch (trend) {
            case 'positive': return <span className="text-[#7EE081] text-lg">↗</span>;
            case 'negative': return <span className="text-red-400 text-lg">↘</span>;
            case 'neutral': return <span className="text-yellow-400 text-lg">→</span>;
            default: return null;
        }
    };

    const getTrendColor = (trend?: 'positive' | 'negative' | 'neutral') => {
        switch (trend) {
            case 'positive': return 'border-l-[#7EE081] bg-gradient-to-r from-[#7EE081]/5 to-transparent';
            case 'negative': return 'border-l-red-400 bg-gradient-to-r from-red-400/5 to-transparent';
            case 'neutral': return 'border-l-yellow-400 bg-gradient-to-r from-yellow-400/5 to-transparent';
            default: return 'border-l-[#333333]';
        }
    };

    if (loading) {
        return (
            <div className="p-8 flex flex-col items-center justify-center min-h-[400px]">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#7EE081] mb-4"></div>
                <div className="text-white text-lg">Loading company insights...</div>
                <div className="text-[#666666] text-sm mt-2">Analyzing financial data</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-8 flex items-center justify-center min-h-[400px]">
                <div className="text-center max-w-md">
                    <div className="text-red-400 text-5xl mb-4">⚠️</div>
                    <h3 className="text-xl font-semibold text-white mb-2">Unable to Load Insights</h3>
                    <p className="text-[#666666] text-sm mb-6">{error}</p>
                    <button 
                        onClick={loadCompanyData}
                        className="px-6 py-3 bg-[#7EE081] text-black rounded-full font-medium hover:bg-[#6BD073] transition-all duration-200 hover:scale-105"
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    const keyInsights = getKeyInsights();

    return (
        <div className="p-8 space-y-10">
            {/* Hero Section */}
            <div className="text-center space-y-4">
                <div className="inline-flex items-center gap-3 px-6 py-3 bg-[#1a1a1a] rounded-full">
                    <div className="w-2 h-2 bg-[#7EE081] rounded-full animate-pulse"></div>
                    <span className="text-[#666666] text-sm font-medium">LIVE FINANCIAL ANALYSIS</span>
                </div>
                
                <h1 className="text-4xl font-bold text-white mb-2">
                    {currentStock.name}
                </h1>
                
                <div className="flex items-center justify-center gap-6 text-[#666666]">
                    <div className="flex items-center gap-2">
                        <span className="text-[#7EE081]">$</span>
                        <span className="font-mono">{currentStock.symbol}</span>
                    </div>
                    {financialData && (
                        <div className="flex items-center gap-2">
                            <span>📊</span>
                            <span>{financialData.fiscal_period} {financialData.fiscal_year}</span>
                        </div>
                    )}
                </div>
            </div>

            {/* Key Insights */}
            {keyInsights.length > 0 && (
                <div className="space-y-6">
                    <div className="text-center">
                        <h2 className="text-2xl font-bold text-white mb-2">Financial Health Overview</h2>
                        <p className="text-[#666666]">Key insights that tell the company's story</p>
                    </div>
                    
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {keyInsights.map((insight, index) => (
                            <div 
                                key={index} 
                                className={`group relative p-6 rounded-2xl border-l-4 ${getTrendColor(insight.trend)} backdrop-blur-sm hover:scale-[1.02] transition-all duration-300 cursor-pointer`}
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <span className="text-2xl">{insight.icon}</span>
                                        <div>
                                            <h3 className="text-lg font-semibold text-white group-hover:text-[#7EE081] transition-colors">
                                                {insight.title}
                                            </h3>
                                        </div>
                                    </div>
                                    {getTrendArrow(insight.trend)}
                                </div>
                                
                                <div className="mb-4">
                                    <div className="text-3xl font-bold text-white mb-2">
                                        {insight.value}
                                    </div>
                                    <p className="text-[#999999] text-sm leading-relaxed">
                                        {insight.description}
                                    </p>
                                </div>
                                
                                {insight.progress !== undefined && (
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-xs text-[#666666]">
                                            <span>Strength Indicator</span>
                                            <span>{insight.progress.toFixed(0)}%</span>
                                        </div>
                                        <div className="w-full bg-[#2a2a2a] rounded-full h-2 overflow-hidden">
                                            <div 
                                                className="h-full bg-gradient-to-r from-[#7EE081] to-[#5BC55B] rounded-full transition-all duration-1000 ease-out"
                                                style={{ width: `${insight.progress}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Quick Stats Summary */}
            {financialData && (
                <div className="bg-gradient-to-br from-[#1a1a1a] to-[#0f0f0f] border border-[#333333] rounded-2xl p-8">
                    <div className="flex items-center gap-3 mb-6">
                        <span className="text-2xl">📋</span>
                        <h3 className="text-xl font-semibold text-white">Data Summary</h3>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <div className="text-center space-y-2">
                            <div className="text-3xl mb-2">🔒</div>
                            <div className="text-[#666666] text-sm">Data Source</div>
                            <div className="text-white font-semibold">SEC XBRL Filings</div>
                            <div className="text-xs text-[#666666]">Regulatory grade accuracy</div>
                        </div>
                        
                        <div className="text-center space-y-2">
                            <div className="text-3xl mb-2">📅</div>
                            <div className="text-[#666666] text-sm">Reporting Period</div>
                            <div className="text-white font-semibold">
                                {financialData.fiscal_period} {financialData.fiscal_year}
                            </div>
                            <div className="text-xs text-[#666666]">Most recent filing</div>
                        </div>
                        
                        <div className="text-center space-y-2">
                            <div className="text-3xl mb-2">📊</div>
                            <div className="text-[#666666] text-sm">Coverage</div>
                            <div className="text-white font-semibold">
                                {Object.keys(financialData.statements).length} Statements
                            </div>
                            <div className="text-xs text-[#666666]">Complete financial picture</div>
                        </div>
                    </div>
                </div>
            )}

            {/* Expandable Details */}
            {financialData && (
                <details className="group">
                    <summary className="cursor-pointer list-none">
                        <div className="flex items-center justify-between p-6 bg-[#1a1a1a] border border-[#333333] rounded-2xl hover:border-[#7EE081]/30 transition-colors">
                            <div className="flex items-center gap-3">
                                <span className="text-xl">📄</span>
                                <span className="text-white font-medium">View Available Statements</span>
                                <span className="px-3 py-1 bg-[#7EE081]/10 text-[#7EE081] rounded-full text-xs font-medium">
                                    {Object.keys(financialData.statements).length} Available
                                </span>
                            </div>
                            <span className="text-[#666666] group-open:rotate-180 transition-transform duration-200">▼</span>
                        </div>
                    </summary>
                    
                    <div className="mt-4 p-6 bg-[#0f0f0f] border border-[#333333] rounded-2xl">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {Object.entries(financialData.statements).map(([statementType, data]) => (
                                <div key={statementType} className="flex items-center justify-between p-4 bg-[#1a1a1a] rounded-xl">
                                    <div>
                                        <h4 className="text-white font-medium">{statementType}</h4>
                                        <p className="text-[#666666] text-sm">
                                            {Object.keys(data).length} line items
                                        </p>
                                    </div>
                                    <div className="w-3 h-3 bg-[#7EE081] rounded-full"></div>
                                </div>
                            ))}
                        </div>
                    </div>
                </details>
            )}
        </div>
    );
}