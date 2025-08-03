'use client';

import { useState, useEffect } from 'react';
import { Company } from './types';
import financialApi from './api/financialModelingPrep';
import Sidebar from './StockPicker';
import ContentTabs from './ContentTabs';


export default function CompanyInfo() {
    const [selectedStocks, setSelectedStocks] = useState<Company[]>([]);
    const [currentStock, setCurrentStock] = useState<Company | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Load available companies from the database on component mount
    useEffect(() => {
        const loadCompanies = async () => {
            try {
                setLoading(true);
                const companies = await financialApi.getCompanies();
                
                // Auto-select first company if available
                if (companies.length > 0) {
                    const firstCompany = companies[0];
                    setSelectedStocks([firstCompany]);
                    setCurrentStock(firstCompany);
                }
            } catch (err) {
                setError('Failed to load companies from database');
                console.error('Error loading companies:', err);
            } finally {
                setLoading(false);
            }
        };

        loadCompanies();
    }, []);

    const handleAddStock = (company: Company) => {
        if (!selectedStocks.find(stock => stock.symbol === company.symbol)) {
            const newSelectedStocks = [...selectedStocks, company];
            setSelectedStocks(newSelectedStocks);
            
            // If no current stock is selected, make this the current one
            if (!currentStock) {
                setCurrentStock(company);
            }
        }
    };

    const handleRemoveStock = (symbol: string) => {
        const newSelectedStocks = selectedStocks.filter(stock => stock.symbol !== symbol);
        setSelectedStocks(newSelectedStocks);
        
        // If we removed the current stock, switch to another one or clear
        if (currentStock?.symbol === symbol) {
            setCurrentStock(newSelectedStocks.length > 0 ? newSelectedStocks[0] : null);
        }
    };

    const handleStockClick = (company: Company) => {
        setCurrentStock(company);
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
                <div className="text-white text-lg">Loading companies...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
                <div className="text-red-400 text-lg max-w-md text-center">
                    <h2 className="text-xl font-bold mb-2">Connection Error</h2>
                    <p>{error}</p>
                    <p className="text-sm mt-4 text-gray-400">
                        Make sure your backend server is running on localhost:8000
                    </p>
                    <button 
                        onClick={() => window.location.reload()} 
                        className="mt-4 px-4 py-2 bg-[#7EE081] text-black rounded hover:bg-[#6BD073] transition-colors"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#1a1a1a]">
            {/* Sidebar for stock selection */}
            <Sidebar
                selectedStocks={selectedStocks}
                currentStock={currentStock}
                onAddStock={handleAddStock}
                onRemoveStock={handleRemoveStock}
                onStockClick={handleStockClick}
            />
            
            {/* Main content area */}
            <div className="flex-1">
                {currentStock ? (
                    <>
                        {/* Company header */}
                        <div className="bg-[#1a1a1a]  p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h1 className="text-3xl font-bold text-white mb-2">
                                        {currentStock.name}
                                    </h1>
                                    <div className="flex items-center gap-4">
                                        <span className="text-[#7EE081] text-lg font-semibold">
                                            {currentStock.symbol}
                                        </span>
                                        <span className="text-[#666666] text-sm">
                                            Financial Data Available
                                        </span>
                                    </div>
                                </div>
                                
                                {/* Status indicator */}
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 bg-[#7EE081] rounded-full"></div>
                                    <span className="text-[#666666] text-sm">Live Data</span>
                                </div>
                            </div>
                        </div>

                        {/* Content tabs and main content */}
                        <ContentTabs currentStock={currentStock} />
                    
                    </>
                ) : (
                    <div className="flex-1 flex items-center justify-center p-8">
                        <div className="text-center">
                            <h2 className="text-2xl font-bold text-white mb-4">
                                Welcome to Graham
                            </h2>
                            <p className="text-[#666666] mb-6 max-w-md">
                                Select a company from the dropdown above to view detailed financial statements, 
                                charts, and analysis.
                            </p>
                            <div className="text-[#666666] text-sm">
                                {selectedStocks.length === 0 ? (
                                    "No companies selected"
                                ) : (
                                    `${selectedStocks.length} company(ies) available`
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}