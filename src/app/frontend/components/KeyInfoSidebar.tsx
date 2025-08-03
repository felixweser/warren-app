// Key information sidebar component
interface KeyInfoSidebarProps {
    ticker?: string;
}

export default function KeyInfoSidebar({ ticker }: KeyInfoSidebarProps) {
    return (
        <div className="w-64 bg-[#1a1a1a] border-l border-[#333333] p-4">
            <h3 className="text-white font-semibold mb-4">Key Information</h3>
            {ticker ? (
                <div className="space-y-3">
                    <div>
                        <div className="text-[#666666] text-sm">Symbol</div>
                        <div className="text-white">{ticker}</div>
                    </div>
                    <div className="text-[#666666] text-sm">
                        Additional key metrics coming soon...
                    </div>
                </div>
            ) : (
                <div className="text-[#666666] text-sm">
                    Select a company to view key information
                </div>
            )}
        </div>
    );
}