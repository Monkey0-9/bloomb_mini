import React, { useEffect, useState } from 'react';
import { Rss } from 'lucide-react';
import { useTerminalStore } from '../store';

const NewsTicker = () => {
    const { currentTicker } = useTerminalStore();
    const [news, setNews] = useState<any[]>([]);

    useEffect(() => {
        const fetchNews = async () => {
            try {
                const res = await fetch(`/api/news?ticker=${encodeURIComponent(currentTicker)}`);
                const data = await res.json();
                if (data.news) setNews(data.news);
            } catch (err) {
                console.error('News fetch failed:', err);
            }
        };
        fetchNews();
        const interval = setInterval(fetchNews, 30000); // Pulse every 30s
        return () => clearInterval(interval);
    }, [currentTicker]);

    const headlines = news.length > 0 ? news : [
        { id: 'm1', time: '12:04', source: 'BBG', text: 'MAERSK DIVERTS 14 VESSELS FROM RED SEA TO CAPE OF GOOD HOPE AMID ESCALATING TENSIONS', impact: 'bullish' },
        { id: 'm2', time: '11:42', source: 'RTRS', text: 'ZIM INTEGRATED SHIPPING SERVICES REPORTS UNEXPECTED SURGE IN ASIA-EUROPE FREIGHT RATES', impact: 'bullish' }
    ];

    return (
        <div className="h-8 bg-surface-1 border-t border-border-3 flex items-center px-4 shrink-0 overflow-hidden relative z-10 w-full">
            <div className="flex items-center gap-2 shrink-0 mr-4 z-20 bg-surface-1 py-1 pr-2 border-r border-white/10">
                <Rss className="w-3 h-3 text-accent-primary" />
                <span className="text-[10px] font-bold text-accent-primary tracking-widest uppercase">{currentTicker.split(' ')[0]} NEWS</span>
            </div>
            
            {/* Fade gradients */}
            <div className="absolute inset-y-0 left-[120px] w-8 bg-gradient-to-r from-surface-1 to-transparent z-10"></div>
            <div className="absolute inset-y-0 right-0 w-8 bg-gradient-to-l from-surface-1 to-transparent z-10"></div>

            <div className="flex-1 overflow-hidden relative flex items-center h-full">
                <div className="flex gap-16 whitespace-nowrap items-center animate-news-scroll hover:[animation-play-state:paused]">
                    {headlines.map(item => (
                        <div 
                          key={item.id} 
                          className={`flex items-center gap-3 group transition-all ${item.url ? 'cursor-alias hover:scale-105' : 'cursor-default'}`}
                          onClick={() => item.url && window.open(item.url, '_blank')}
                        >
                            <span className="text-[10px] text-text-4 font-mono group-hover:text-accent-primary transition-colors">{item.time}</span>
                            <span className="text-[9px] text-text-3 font-bold bg-white/5 px-1.5 rounded uppercase">{item.source}</span>
                            <span className={`text-[11px] font-bold tracking-wide uppercase ${item.impact === 'bullish' ? 'text-bull' : item.impact === 'bearish' ? 'text-bear' : 'text-text-1'}`}>
                                {item.text}
                            </span>
                        </div>
                    ))}
                    {/* Loop for seamless scroll */}
                    {headlines.map(item => (
                        <div 
                          key={`${item.id}-loop`} 
                          className={`flex items-center gap-3 group transition-all ${item.url ? 'cursor-alias hover:scale-105' : 'cursor-default'}`}
                          onClick={() => item.url && window.open(item.url, '_blank')}
                        >
                            <span className="text-[10px] text-text-4 font-mono group-hover:text-accent-primary transition-colors">{item.time}</span>
                            <span className="text-[9px] text-text-3 font-bold bg-white/5 px-1.5 rounded uppercase">{item.source}</span>
                            <span className={`text-[11px] font-bold tracking-wide uppercase ${item.impact === 'bullish' ? 'text-bull' : item.impact === 'bearish' ? 'text-bear' : 'text-text-1'}`}>
                                {item.text}
                            </span>
                        </div>
                    ))}
                </div>
            </div>

            <style>{`
                @keyframes news-scroll {
                    0% { transform: translateX(0); }
                    100% { transform: translateX(-50%); }
                }
                .animate-news-scroll {
                    animation: news-scroll 45s linear infinite;
                }
            `}</style>
        </div>
    );
};

export default NewsTicker;
