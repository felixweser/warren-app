import { useState, useEffect } from 'react';

interface StockNewsProps {
  currentStock?: any;
}

interface NewsItem {
  id: string;
  headline: string;
  summary: string;
  source: string;
  publishedAt: string;
  url: string;
  sentiment: 'positive' | 'negative' | 'neutral';
}

export default function StockNews({ currentStock }: StockNewsProps) {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Mock news data for demonstration
  const getMockNews = (ticker: string): NewsItem[] => {
    const mockNews: { [key: string]: NewsItem[] } = {
      'GOOGL': [
        {
          id: '1',
          headline: 'Alphabet Reports Strong Q4 Earnings Driven by Cloud Growth',
          summary: 'Google parent company Alphabet exceeded analyst expectations with robust cloud revenue growth and improved AI capabilities across its product suite.',
          source: 'Financial Times',
          publishedAt: '2024-02-01T14:30:00Z',
          url: '#',
          sentiment: 'positive'
        },
        {
          id: '2',
          headline: 'EU Regulators Investigate Google\'s AI Practices',
          summary: 'European Union authorities are examining Google\'s artificial intelligence development practices and data usage policies under new digital regulations.',
          source: 'Reuters',
          publishedAt: '2024-01-28T09:15:00Z',
          url: '#',
          sentiment: 'negative'
        },
        {
          id: '3',
          headline: 'Google Expands Cloud Infrastructure in Asia Pacific',
          summary: 'Alphabet announces significant investment in new data centers across Asia Pacific region to support growing enterprise demand.',
          source: 'Bloomberg',
          publishedAt: '2024-01-25T16:45:00Z',
          url: '#',
          sentiment: 'positive'
        },
        {
          id: '4',
          headline: 'Analysts Maintain Buy Rating on Alphabet Stock',
          summary: 'Major investment firms maintain positive outlook on Alphabet shares citing strong fundamentals and AI market positioning.',
          source: 'MarketWatch',
          publishedAt: '2024-01-22T11:20:00Z',
          url: '#',
          sentiment: 'positive'
        }
      ],
      'AAPL': [
        {
          id: '1',
          headline: 'Apple Reports Record iPhone Sales in Holiday Quarter',
          summary: 'Apple exceeded expectations with strong iPhone 15 sales and growing services revenue, though China sales showed some weakness.',
          source: 'Wall Street Journal',
          publishedAt: '2024-02-01T16:00:00Z',
          url: '#',
          sentiment: 'positive'
        },
        {
          id: '2',
          headline: 'Vision Pro Launch Signals Apple\'s AR/VR Ambitions',
          summary: 'Apple\'s new Vision Pro headset represents a major bet on spatial computing and mixed reality technologies.',
          source: 'TechCrunch',
          publishedAt: '2024-01-30T10:30:00Z',
          url: '#',
          sentiment: 'neutral'
        }
      ]
    };

    return mockNews[ticker] || [
      {
        id: '1',
        headline: `Latest ${ticker} Market Analysis`,
        summary: `Recent developments and market sentiment analysis for ${ticker} stock performance and future outlook.`,
        source: 'Market News',
        publishedAt: new Date().toISOString(),
        url: '#',
        sentiment: 'neutral'
      }
    ];
  };

  useEffect(() => {
    const fetchNews = async () => {
      if (!currentStock?.symbol) return;
      
      setLoading(true);
      setError(null);
      
      try {
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // In a real implementation, you would call a news API here
        // const response = await fetch(`/api/news/${currentStock.symbol}`);
        // const data = await response.json();
        
        const mockNews = getMockNews(currentStock.symbol);
        setNews(mockNews);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch news');
        console.error('Error fetching news:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchNews();
  }, [currentStock?.symbol]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'text-green';
      case 'negative': return 'text-red-400';
      default: return 'text-slate-400';
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return '↗';
      case 'negative': return '↘';
      default: return '→';
    }
  };

  if (!currentStock?.symbol) {
    return (
      <div className="w-1/2 mt-8 p-6 bg-[#1a1a1a] border border-[#333333] rounded-2xl shadow-lg">
        <h2 className="text-xl font-bold text-slate-50 mb-4">Latest News</h2>
        <div className="flex justify-center items-center h-32">
          <div className="text-slate-400">Select a company to view latest news</div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-1/2 pt-4 mt-4 bg-[#1a1a1a] rounded-2xl float-left">
      <h2 className="text-xl font-bold text-slate-50 mb-4 px-4">
        Latest News - {currentStock.symbol}
      </h2>
      
      {loading && (
        <div className="flex justify-center items-center h-32">
          <div className="text-slate-400">Loading news...</div>
        </div>
      )}
      
      {error && (
        <div className="flex justify-center items-center h-32">
          <div className="text-red-400">Error: {error}</div>
        </div>
      )}
      
      {!loading && !error && news.length > 0 && (
        <div className="space-y-4 bg-[#2a2a2a] border border-[#333333] rounded-lg max-h-96 overflow-y-auto">
          {news.map((article) => (
            <div 
              key={article.id}
              className="p-4 bg-[#2a2a2a] rounded-lg   cursor-pointer"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <h3 className="text-slate-50 font-semibold text-sm leading-tight mb-2">
                    {article.headline}
                  </h3>
                  <p className="text-slate-400 text-xs leading-relaxed mb-3">
                    {article.summary}
                  </p>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-500">{article.source}</span>
                      <span className="text-xs text-slate-600">•</span>
                      <span className="text-xs text-slate-500">{formatDate(article.publishedAt)}</span>
                    </div>
                    <div className={`flex items-center gap-1 ${getSentimentColor(article.sentiment)}`}>
                      <span className="text-xs">{getSentimentIcon(article.sentiment)}</span>
                      <span className="text-xs capitalize">{article.sentiment}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {!loading && !error && news.length === 0 && (
        <div className="flex justify-center items-center h-32">
          <div className="text-slate-400">No news available</div>
        </div>
      )}
      
      <div className=" mt-4 px-4 text-xs text-slate-50 border-t border-[#333333]">
        <div className="text-xs text-slate-500 ">
          News sentiment: 
          <span className="text-green-400 ml-2">↗ Positive</span>
          <span className="text-slate-400 ml-2">→ Neutral</span>
          <span className="text-red-400 ml-2">↘ Negative</span>
        </div>
      </div>
    </div>
  );
}