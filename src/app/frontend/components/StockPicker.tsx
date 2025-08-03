import { useState, useRef, useEffect } from 'react';
import { Company, SidebarProps } from './types';

const companies: Company[] = [
    { name: "McDonald's", symbol: "MCD" },
    { name: "Starbucks", symbol: "SBUX" },
    { name: "Yum! Brands (KFC, Taco Bell, Pizza Hut)", symbol: "YUM" },
    { name: "Restaurant Brands International (Burger King, Tim Hortons, Popeyes)", symbol: "QSR" },
    { name: "Domino's", symbol: "DPZ" },
    { name: "Google (Alphabet Inc.)", symbol: "GOOG" },
    { name: "Amazon", symbol: "AMZN" }
];

export default function Sidebar({
    selectedStocks,
    currentStock,
    onRemoveStock,
    onAddStock,
    onStockClick
}: SidebarProps) {
    const [showStockList, setShowStockList] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    const handleAddStock = (company: Company) => {
        onAddStock(company);
        setShowStockList(false); // Hide the list after adding
    };

    const toggleStockList = () => {
        setShowStockList(!showStockList);
    };

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setShowStockList(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);


    return (
        <div className="w-full bg-[#1a1a1a] border-b border-[#333333] p-4">
            <div className="flex items-center gap-6">
                {/* Add Stock Button */}
                <div className="relative" ref={dropdownRef}>
                    <button
                        onClick={toggleStockList}
                        className="flex items-center justify-center w-10 h-10 bg-[#1a1a1a] border border-[#333333] rounded-lg text-white hover:bg-[#2a2a2a] focus:ring-1 focus:ring-[#7EE081] transition"
                    >
                        <span className="text-lg font-bold">+</span>
                    </button>
                    
                    {/* Stock List Dropdown */}
                    {showStockList && (
                        <div className="absolute top-12 left-0 z-50 w-80 bg-[#1a1a1a] border border-[#333333] rounded-lg shadow-lg max-h-60 overflow-y-auto">
                            {companies.map((company) => (
                                <div
                                    key={company.symbol}
                                    onClick={() => handleAddStock(company)}
                                    className="px-4 py-3 cursor-pointer hover:bg-[#2a2a2a] border-b border-[#333333] last:border-b-0 transition"
                                >
                                    <div className="font-medium text-sm text-white">
                                        {company.name}
                                    </div>
                                    <div className="text-xs text-[#666666]">
                                        ({company.symbol})
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Selected Stocks */}
                <div className="flex items-center gap-4 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                        {selectedStocks.map((stock) => (
                            <div
                                key={stock.symbol}
                                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg cursor-pointer transition ${
                                    currentStock?.symbol === stock.symbol 
                                    ? 'bg-[#333333] text-white border border-[#7EE081]'
                                    : 'bg-[#1a1a1a] border border-[#333333] hover:bg-[#2a2a2a]' 
                                }`}
                                onClick={() => onStockClick(stock)}
                            >
                                <div className="flex items-center gap-1">
                                    <span className="font-medium text-sm text-white">
                                        {stock.name}
                                    </span>
                                    <span className="text-xs text-[#666666]">
                                        ({stock.symbol})
                                    </span>
                                </div>
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation(); // Prevent click from triggering onStockClick
                                        onRemoveStock(stock.symbol);
                                    }}
                                    className="text-[#666666] hover:text-red-400 text-sm font-bold ml-1"
                                >
                                    ×
                                </button>
                            </div>
                        ))}
                        {selectedStocks.length === 0 && (
                            <span className="text-[#666666] text-sm italic">
                                No stocks selected
                            </span>
                        )}
                    </div>
                </div>
            </div>
        </div>    
    );
}