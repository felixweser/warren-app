'use client';

import { useState, useEffect } from 'react';
import { Company, LatestFinancialStatement, FinancialStatement, StatementData } from './types';
import financialApi from './api/financialModelingPrep';

interface IncomeStatementViewerProps {
    currentStock: Company;
}

type ViewMode = 'latest' | 'quarters' | 'years';
type PeriodType = 'quarterly' | 'annual';

export default function IncomeStatementViewer({ currentStock }: IncomeStatementViewerProps) {
    const [viewMode, setViewMode] = useState<ViewMode>('latest');
    const [periodType, setPeriodType] = useState<PeriodType>('quarterly');
    const [latestData, setLatestData] = useState<LatestFinancialStatement | null>(null);
    const [historicalData, setHistoricalData] = useState<FinancialStatement | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!currentStock) return;
        loadData();
    }, [currentStock, viewMode, periodType]);

    const loadData = async () => {
        try {
            setLoading(true);
            setError(null);

            if (viewMode === 'latest') {
                const data = periodType === 'annual' 
                    ? await financialApi.getLatestAnnualIncomeStatement(currentStock.symbol, 'detailed')
                    : await financialApi.getLatestQuarterlyIncomeStatement(currentStock.symbol, 'detailed');
                setLatestData(data);
                setHistoricalData(null);
            } else {
                const data = viewMode === 'quarters'
                    ? await financialApi.getIncomeStatementQuarters(currentStock.symbol, 8, 'detailed', 'millions')
                    : await financialApi.getIncomeStatementYears(currentStock.symbol, 5, 'detailed', 'millions');
                setHistoricalData(data);
                setLatestData(null);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load income statement data');
            console.error('Error loading income statement:', err);
        } finally {
            setLoading(false);
        }
    };

    const formatValue = (value: number): string => {
        if (Math.abs(value) >= 1000) {
            return `$${(value / 1000).toFixed(1)}B`;
        } else {
            return `$${value.toFixed(1)}M`;
        }
    };

    const getTrendIndicator = (current: number, previous?: number) => {
        if (!previous) return null;
        const change = ((current - previous) / Math.abs(previous)) * 100;
        const isPositive = change > 0;
        const isSignificant = Math.abs(change) > 5;
        
        return {
            change: change.toFixed(1),
            isPositive,
            isSignificant,
            arrow: isPositive ? '↗' : '↘',
            color: isPositive ? 'text-[#7EE081]' : 'text-red-400'
        };
    };

    const getMetricIcon = (key: string) => {
        const iconMap: Record<string, string> = {
            'RevenueFromContractWithCustomerExcludingAssessedTax': '💰',
            'Revenues': '💰',
            'CostOfGoodsAndServicesSold': '💸',
            'GrossProfit': '📈',
            'OperatingIncomeLoss': '⚡',
            'NetIncomeLoss': '🎯',
            'EarningsPerShareBasic': '📊',
            'EarningsPerShareDiluted': '📊'
        };
        return iconMap[key] || '📋';
    };

    const getKeyMetrics = (data: StatementData) => {
        const metrics = [
            { key: 'RevenueFromContractWithCustomerExcludingAssessedTax', label: 'Total Revenue', category: 'Revenue' },
            { key: 'Revenues', label: 'Total Revenue', category: 'Revenue' },
            { key: 'CostOfGoodsAndServicesSold', label: 'Cost of Revenue', category: 'Costs' },
            { key: 'CostOfGoodsAndServicesSold', label: 'Cost of Goods Sold', category: 'Costs' },
            { key: 'GrossProfit', label: 'Gross Profit', category: 'Profit' },
            { key: 'OperatingIncomeLoss', label: 'Operating Income', category: 'Profit' },
            { key: 'NetIncomeLoss', label: 'Net Income', category: 'Profit' },
            { key: 'EarningsPerShareBasic', label: 'Basic EPS', category: 'Per Share' },
            { key: 'EarningsPerShareDiluted', label: 'Diluted EPS', category: 'Per Share' },
        ];

        return metrics
            .map(metric => {
                const dataPoint = data[metric.key];
                return dataPoint ? { ...metric, ...dataPoint } : null;
            })
            .filter((metric): metric is NonNullable<typeof metric> => metric !== null);
    };

    const renderLatestStatement = () => {
        if (!latestData) return null;

        const keyMetrics = getKeyMetrics(latestData.data);
        const allDataPoints = Object.entries(latestData.data);

        return (
            <div className="space-y-8">
                {/* Header */}
                <div className="text-center space-y-4">
                    <div className="inline-flex items-center gap-3 px-6 py-3 bg-[#1a1a1a] border border-[#333333] rounded-full">
                        <div className="w-2 h-2 bg-[#7EE081] rounded-full animate-pulse"></div>
                        <span className="text-[#666666] text-sm font-medium">INCOME STATEMENT ANALYSIS</span>
                    </div>
                    
                    <h3 className="text-3xl font-bold text-white">
                        {latestData.statement_type}
                    </h3>
                    
                    <div className="flex items-center justify-center gap-6 text-[#666666]">
                        <div className="flex items-center gap-2">
                            <span>📅</span>
                            <span>{latestData.fiscal_period} {latestData.fiscal_year}</span>
                        </div>
                        {latestData.period_type && (
                            <div className="flex items-center gap-2">
                                <span>📊</span>
                                <span className="capitalize">{latestData.period_type}</span>
                            </div>
                        )}
                    </div>
                </div>

                {/* Key Metrics Showcase */}
                {keyMetrics.length > 0 && (
                    <div className="space-y-6">
                        <div className="text-center">
                            <h4 className="text-2xl font-bold text-white mb-2">Financial Performance</h4>
                            <p className="text-[#666666]">Key metrics that drive the business</p>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {keyMetrics.map((metric, index) => {
                                const icon = getMetricIcon(Object.keys(latestData.data).find(key => 
                                    latestData.data[key].label === metric.label
                                ) || '');
                                
                                const isProfit = metric.key.includes('Income') || metric.key.includes('Profit');
                                const isPositive = metric.value > 0;
                                
                                return (
                                    <div 
                                        key={index} 
                                        className="group relative p-6 bg-gradient-to-br from-[#1a1a1a] to-[#0f0f0f] border border-[#333333] rounded-2xl hover:border-[#7EE081]/30 transition-all duration-300 hover:scale-105"
                                    >
                                        <div className="flex items-start justify-between mb-4">
                                            <div className="flex items-center gap-3">
                                                <span className="text-2xl">{icon}</span>
                                                <div>
                                                    <h5 className="text-white font-semibold group-hover:text-[#7EE081] transition-colors">
                                                        {metric.label}
                                                    </h5>
                                                    <p className="text-[#666666] text-xs">{metric.category}</p>
                                                </div>
                                            </div>
                                            {isProfit && (
                                                <span className={`text-lg ${
                                                    isPositive ? 'text-[#7EE081]' : 'text-red-400'
                                                }`}>
                                                    {isPositive ? '📈' : '📉'}
                                                </span>
                                            )}
                                        </div>
                                        
                                        <div className="space-y-2">
                                            <div className="text-2xl font-bold text-white">
                                                {formatValue(metric.value)}
                                            </div>
                                            <div className="text-[#666666] text-sm">{metric.unit}</div>
                                        </div>
                                        
                                        <div className="absolute inset-0 bg-gradient-to-r from-[#7EE081]/0 to-[#7EE081]/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Progressive Disclosure for All Data */}
                <details className="group">
                    <summary className="cursor-pointer list-none">
                        <div className="flex items-center justify-between p-6 bg-[#1a1a1a] border border-[#333333] rounded-2xl hover:border-[#7EE081]/30 transition-colors">
                            <div className="flex items-center gap-3">
                                <span className="text-xl">📋</span>
                                <span className="text-white font-medium">View All Line Items</span>
                                <span className="px-3 py-1 bg-[#7EE081]/10 text-[#7EE081] rounded-full text-xs font-medium">
                                    {allDataPoints.length} Items
                                </span>
                            </div>
                            <span className="text-[#666666] group-open:rotate-180 transition-transform duration-200">▼</span>
                        </div>
                    </summary>
                    
                    <div className="mt-4 bg-[#0f0f0f] border border-[#333333] rounded-2xl overflow-hidden">
                        <div className="max-h-96 overflow-y-auto">
                            {allDataPoints.map(([tag, dataPoint], index) => {
                                const icon = getMetricIcon(tag);
                                return (
                                    <div 
                                        key={tag} 
                                        className={`flex items-center justify-between p-4 hover:bg-[#1a1a1a] transition-colors ${
                                            index % 2 === 0 ? 'bg-[#0f0f0f]' : 'bg-[#1a1a1a]'
                                        }`}
                                    >
                                        <div className="flex items-center gap-3 flex-1">
                                            <span className="text-lg">{icon}</span>
                                            <div className="flex-1">
                                                <div className="text-white font-medium">
                                                    {dataPoint.label}
                                                </div>
                                                <div className="text-[#666666] text-sm font-mono">{tag}</div>
                                                {dataPoint.documentation && (
                                                    <div className="text-[#666666] text-xs mt-1 max-w-md truncate" 
                                                         title={dataPoint.documentation}>
                                                        {dataPoint.documentation}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-white font-semibold text-lg">
                                                {formatValue(dataPoint.value)}
                                            </div>
                                            <div className="text-[#666666] text-sm">{dataPoint.unit}</div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </details>
            </div>
        );
    };

    const renderHistoricalData = () => {
        if (!historicalData) return null;

        return (
            <div className="space-y-8">
                {/* Header */}
                <div className="text-center space-y-4">
                    <div className="inline-flex items-center gap-3 px-6 py-3 bg-[#1a1a1a] border border-[#333333] rounded-full">
                        <div className="w-2 h-2 bg-[#7EE081] rounded-full animate-pulse"></div>
                        <span className="text-[#666666] text-sm font-medium">HISTORICAL ANALYSIS</span>
                    </div>
                    
                    <h3 className="text-3xl font-bold text-white">
                        Income Statement Trends
                    </h3>
                    
                    <div className="flex items-center justify-center gap-6 text-[#666666]">
                        <div className="flex items-center gap-2">
                            <span>📊</span>
                            <span>{historicalData.periods_returned} periods</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span>📅</span>
                            <span className="capitalize">{historicalData.period_type}</span>
                        </div>
                    </div>
                </div>

                {/* Historical Timeline */}
                <div className="space-y-6">
                    {historicalData.periods.map((period, index) => {
                        const keyMetrics = getKeyMetrics(period.data);
                        const previousPeriod = index < historicalData.periods.length - 1 ? historicalData.periods[index + 1] : null;
                        const previousMetrics = previousPeriod ? getKeyMetrics(previousPeriod.data) : [];
                        
                        return (
                            <div key={index} className="relative">
                                {/* Timeline connector */}
                                {index < historicalData.periods.length - 1 && (
                                    <div className="absolute left-6 top-24 w-0.5 h-16 bg-gradient-to-b from-[#7EE081] to-transparent"></div>
                                )}
                                
                                <div className="bg-gradient-to-br from-[#1a1a1a] to-[#0f0f0f] border border-[#333333] rounded-2xl overflow-hidden hover:border-[#7EE081]/30 transition-colors">
                                    {/* Period Header */}
                                    <div className="bg-[#1a1a1a] border-b border-[#333333] p-6">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-4">
                                                <div className="w-4 h-4 bg-[#7EE081] rounded-full flex-shrink-0"></div>
                                                <div>
                                                    <h4 className="text-xl font-bold text-white">
                                                        {period.fiscal_period} {period.fiscal_year}
                                                    </h4>
                                                    <p className="text-[#666666] text-sm">
                                                        Period ending: {new Date(period.end_date).toLocaleDateString()}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-[#666666] text-sm">Period #{historicalData.periods.length - index}</div>
                                                {index === 0 && (
                                                    <span className="inline-block px-2 py-1 bg-[#7EE081]/10 text-[#7EE081] rounded-full text-xs font-medium mt-1">
                                                        Latest
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                    
                                    {/* Key Metrics */}
                                    {keyMetrics.length > 0 && (
                                        <div className="p-6">
                                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                                {keyMetrics.slice(0, 4).map((metric, metricIndex) => {
                                                    const previousMetric = previousMetrics.find(pm => pm.key === metric.key);
                                                    const trend = getTrendIndicator(metric.value, previousMetric?.value);
                                                    const icon = getMetricIcon(metric.key);
                                                    
                                                    return (
                                                        <div key={metricIndex} className="bg-[#2a2a2a] rounded-xl p-4 hover:bg-[#333333] transition-colors">
                                                            <div className="flex items-start justify-between mb-3">
                                                                <div className="flex items-center gap-2">
                                                                    <span className="text-lg">{icon}</span>
                                                                    <div className="text-[#666666] text-sm font-medium">{metric.label}</div>
                                                                </div>
                                                                {trend && trend.isSignificant && (
                                                                    <div className={`flex items-center gap-1 ${trend.color}`}>
                                                                        <span className="text-sm">{trend.arrow}</span>
                                                                        <span className="text-xs font-medium">{Math.abs(Number(trend.change))}%</span>
                                                                    </div>
                                                                )}
                                                            </div>
                                                            
                                                            <div className="text-white font-bold text-lg">
                                                                {formatValue(metric.value)}
                                                            </div>
                                                            
                                                            {trend && (
                                                                <div className={`text-xs mt-2 ${trend.color}`}>
                                                                    {trend.isPositive ? 'Up' : 'Down'} {Math.abs(Number(trend.change))}% from previous period
                                                                </div>
                                                            )}
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
                
                {/* Summary Insights */}
                <div className="bg-gradient-to-br from-[#1a1a1a] to-[#0f0f0f] border border-[#333333] rounded-2xl p-8">
                    <div className="text-center">
                        <h4 className="text-xl font-bold text-white mb-2">Historical Insights</h4>
                        <p className="text-[#666666] mb-6">
                            Analyzed {historicalData.periods_returned} {historicalData.period_type} periods to identify trends and patterns
                        </p>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="text-center">
                                <div className="text-3xl mb-2">📈</div>
                                <div className="text-[#666666] text-sm">Trend Analysis</div>
                                <div className="text-white font-semibold">Period-over-period comparison</div>
                            </div>
                            
                            <div className="text-center">
                                <div className="text-3xl mb-2">🎯</div>
                                <div className="text-[#666666] text-sm">Performance Tracking</div>
                                <div className="text-white font-semibold">Key metric evolution</div>
                            </div>
                            
                            <div className="text-center">
                                <div className="text-3xl mb-2">🔍</div>
                                <div className="text-[#666666] text-sm">Pattern Recognition</div>
                                <div className="text-white font-semibold">Financial health indicators</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="p-8">
            {/* Controls */}
            <div className="mb-8 flex flex-wrap gap-4 items-center justify-center">
                {/* View Mode */}
                <div className="flex gap-2 p-1 bg-[#1a1a1a] border border-[#333333] rounded-full">
                    {[
                        { value: 'latest', label: 'Latest', icon: '📊' },
                        { value: 'quarters', label: 'Quarters', icon: '📅' },
                        { value: 'years', label: 'Years', icon: '📈' },
                    ].map((option) => (
                        <button
                            key={option.value}
                            onClick={() => setViewMode(option.value as ViewMode)}
                            className={`flex items-center gap-2 px-6 py-3 text-sm font-medium rounded-full transition-all duration-200 ${
                                viewMode === option.value
                                    ? 'bg-[#7EE081] text-black shadow-lg scale-105'
                                    : 'text-[#666666] hover:text-white hover:bg-[#2a2a2a]'
                            }`}
                        >
                            <span>{option.icon}</span>
                            {option.label}
                        </button>
                    ))}
                </div>

                {/* Period Type (for latest view) */}
                {viewMode === 'latest' && (
                    <div className="flex gap-2 p-1 bg-[#1a1a1a] border border-[#333333] rounded-full">
                        {[
                            { value: 'quarterly', label: 'Quarterly', icon: '🗓️' },
                            { value: 'annual', label: 'Annual', icon: '📆' },
                        ].map((option) => (
                            <button
                                key={option.value}
                                onClick={() => setPeriodType(option.value as PeriodType)}
                                className={`flex items-center gap-2 px-6 py-3 text-sm font-medium rounded-full transition-all duration-200 ${
                                    periodType === option.value
                                        ? 'bg-[#7EE081] text-black shadow-lg scale-105'
                                        : 'text-[#666666] hover:text-white hover:bg-[#2a2a2a]'
                                }`}
                            >
                                <span>{option.icon}</span>
                                {option.label}
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* Content */}
            {loading ? (
                <div className="flex flex-col items-center justify-center py-16">
                    <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#7EE081] mb-6"></div>
                    <div className="text-white text-xl font-semibold mb-2">Loading Income Statement</div>
                    <div className="text-[#666666] text-sm">Fetching financial data...</div>
                    <div className="mt-4 flex gap-2">
                        <div className="w-2 h-2 bg-[#7EE081] rounded-full animate-pulse"></div>
                        <div className="w-2 h-2 bg-[#7EE081] rounded-full animate-pulse" style={{animationDelay: '0.1s'}}></div>
                        <div className="w-2 h-2 bg-[#7EE081] rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                    </div>
                </div>
            ) : error ? (
                <div className="flex items-center justify-center py-16">
                    <div className="text-center max-w-md">
                        <div className="text-red-400 text-6xl mb-6">📊</div>
                        <h3 className="text-2xl font-bold text-white mb-3">Data Loading Failed</h3>
                        <p className="text-[#666666] text-sm mb-6 leading-relaxed">{error}</p>
                        <button 
                            onClick={loadData}
                            className="px-8 py-4 bg-[#7EE081] text-black rounded-full font-medium hover:bg-[#6BD073] transition-all duration-200 hover:scale-105 shadow-lg"
                        >
                            Try Loading Again
                        </button>
                    </div>
                </div>
            ) : (
                <div>
                    {viewMode === 'latest' ? renderLatestStatement() : renderHistoricalData()}
                </div>
            )}
        </div>
    );
}