// Cache status indicator component
export default function CacheStatus() {
    return (
        <div className="flex items-center gap-2 text-sm">
            <div className="w-2 h-2 bg-[#7EE081] rounded-full"></div>
            <span className="text-[#666666]">Live Data</span>
        </div>
    );
}