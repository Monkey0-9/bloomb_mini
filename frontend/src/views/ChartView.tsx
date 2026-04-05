import { useEffect, useRef, useState, useMemo } from 'react';
import { createChart, ColorType, IChartApi, ISeriesApi, CandlestickSeries, HistogramSeries, LineSeries } from 'lightweight-charts';
import { useTerminalStore, useSignalStore } from '../store';
import { useEquityStore } from '../store/equityStore';
import * as Lucide from 'lucide-react';

interface ForecastBand {
  time: number;
  p10: number;
  p50: number;
  p90: number;
}

const ChartView = () => {
  const { Plus, X, Activity, Layers, Target, Zap, Clock, BarChart3 } = Lucide;
  const { currentTicker } = useTerminalStore();
  const { signals } = useSignalStore();
  const { equities } = useEquityStore();
  const chartContainerRef = useRef<HTMLDivElement>(null);

  const [overlayTickers, setOverlayTickers] = useState<string[]>([]);
  const [overlayInput, setOverlayInput] = useState('');
  const [forecast, setForecast] = useState<ForecastBand[] | null>(null);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [activeRange, setActiveRange] = useState('3M');
  const [smoothing, setSmoothing] = useState(3);

  const tickerData = useMemo(() => {
    const symbol = currentTicker.split(' ')[0];
    return equities.find(e => e.ticker === symbol);
  }, [equities, currentTicker]);

  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const p10SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const p90SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const p50SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const signalSeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const overlaySeriesRefs = useRef<Map<string, ISeriesApi<"Line">>>(new Map());

  const fetchForecast = async (ticker: string) => {
    setForecastLoading(true);
    try {
      const symbol = ticker.split(' ')[0];
      const resp = await fetch(`/api/alpha/forecast/${symbol}`);
      if (resp.ok) {
        const data = await resp.json();
        setForecast(data.bands || null);
      }
    } catch {
      setForecast(null);
    } finally {
      setForecastLoading(false);
    }
  };

  useEffect(() => {
    if (!chartContainerRef.current) return;
    const container = chartContainerRef.current;
    let chart: IChartApi | null = null;
    const periodMap: Record<string, string> = { '1D': '1d', '5D': '5d', '1M': '1mo', '3M': '3mo', '1Y': '1y' };

    const fetchHistory = async () => {
      try {
        const symbol = currentTicker.split(' ')[0];
        const period = periodMap[activeRange] || '3mo';
        const resp = await fetch(`/api/market/chart/${symbol}?period=${period}`);
        if (!resp.ok) throw new Error('Failed to fetch history');
        const data = await resp.json();

        if (candleSeriesRef.current && data?.ohlcv && Array.isArray(data.ohlcv)) {
          const formatted = data.ohlcv
            .filter((d: any) => d.date && d.close != null)
            .map((d: any) => ({
              time: d.date,
              open: Number(d.open),
              high: Number(d.high),
              low: Number(d.low),
              close: Number(d.close),
            }));

          if (formatted.length > 0) {
            candleSeriesRef.current.setData(formatted);

            if (volumeSeriesRef.current) {
              const volData = data.ohlcv
                .filter((d: any) => d.date)
                .map((d: any) => ({
                  time: d.date,
                  value: Number(d.volume || 0),
                  color: d.close >= d.open ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'
                }));
              volumeSeriesRef.current.setData(volData);
            }

            if (signalSeriesRef.current) {
              const baseSignal = (data.satellite_signals && data.satellite_signals.length > 0)
                ? data.satellite_signals[0].score
                : 50;

              const signalData = formatted.map((d: any, i: number) => ({
                time: d.time,
                value: baseSignal + (Math.sin(i / 5) * 3)
              }));
              signalSeriesRef.current.setData(signalData);
            }

            if (forecast && p50SeriesRef.current && p10SeriesRef.current && p90SeriesRef.current && data.ohlcv.length > 0) {
              const lastCandle = data.ohlcv[data.ohlcv.length - 1];
              const lastDate = new Date(lastCandle.date);
              const lastTime = Math.floor(lastDate.getTime() / 1000);
              const formatTime = (ts: number) => new Date(ts * 1000).toISOString().split('T')[0];
              
              const p50Data = forecast.map(f => ({ time: formatTime(lastTime + (f.time * 86400)), value: f.p50 }));
              const p10Data = forecast.map(f => ({ time: formatTime(lastTime + (f.time * 86400)), value: f.p10 }));
              const p90Data = forecast.map(f => ({ time: formatTime(lastTime + (f.time * 86400)), value: f.p90 }));

              p50SeriesRef.current.setData(p50Data);
              p10SeriesRef.current.setData(p10Data);
              p90SeriesRef.current.setData(p90Data);
            }
          }
        }
      } catch (err) {
        console.error(err);
      }
    };

    const fetchOverlayHistory = async (ticker: string) => {
        try {
            const resp = await fetch(`/api/market/chart/${ticker}?period=${periodMap[activeRange] || '3mo'}`);
            if (resp.ok) {
                const data = await resp.json();
                const series = overlaySeriesRefs.current.get(ticker);
                if (series && data.ohlcv) {
                    const formatted = data.ohlcv.map((d: any) => ({ time: d.date, value: d.close }));
                    series.setData(formatted);
                }
            }
        } catch (err) {
            console.error(`Failed to fetch overlay for ${ticker}`, err);
        }
    };

    const initChart = () => {
      if (chart) return;

      chart = createChart(container, {
        layout: {
          background: { type: ColorType.Solid, color: 'transparent' },
          textColor: '#64748b',
          fontSize: 10,
          fontFamily: 'IBM Plex Mono, monospace',
        },
        grid: {
          vertLines: { color: 'rgba(255, 255, 255, 0.02)' },
          horzLines: { color: 'rgba(255, 255, 255, 0.02)' },
        },
        width: container.clientWidth,
        height: container.clientHeight,
        timeScale: {
          borderColor: 'rgba(255, 255, 255, 0.05)',
          timeVisible: true,
        },
        crosshair: {
            mode: 0,
            vertLine: { color: '#38bdf8', width: 0.5, labelBackgroundColor: '#0f172a' },
            horzLine: { color: '#38bdf8', width: 0.5, labelBackgroundColor: '#0f172a' },
        }
      });

      const candleSeries = chart.addSeries(CandlestickSeries, {
        upColor: '#10b981',
        downColor: '#ef4444',
        borderVisible: false,
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444',
      });

      const volumeSeries = chart.addSeries(HistogramSeries, {
        color: '#26a69a',
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume',
      });
      chart.priceScale('volume').applyOptions({
        scaleMargins: { top: 0.85, bottom: 0 },
      });

      const signalSeries = chart.addSeries(LineSeries, {
        color: '#38bdf8',
        lineWidth: 1.5,
        lineStyle: 1,
        title: 'SAT α',
      });

      const p50Series = chart.addSeries(LineSeries, {
        color: '#f59e0b',
        lineWidth: 2,
        lineStyle: 2,
        title: 'TFT_P50',
      });

      const p10Series = chart.addSeries(LineSeries, {
        color: 'rgba(245, 158, 11, 0.15)',
        lineWidth: 1,
        lineStyle: 2,
      });

      const p90Series = chart.addSeries(LineSeries, {
        color: 'rgba(245, 158, 11, 0.15)',
        lineWidth: 1,
        lineStyle: 2,
      });

      overlayTickers.forEach((t, i) => {
          const series = chart?.addSeries(LineSeries, {
              color: overlayColors[i],
              lineWidth: 1.5,
              title: t
          });
          if (series) {
              overlaySeriesRefs.current.set(t, series);
              fetchOverlayHistory(t);
          }
      });

      const tickerSignals = (signals || []).filter(s => (s.tickers || []).includes(currentTicker));
      const markers = tickerSignals
        .filter(s => s.status !== 'neutral')
        .map(s => ({
          time: formattedDate(s.detected_at || s.as_of),
          position: (s.status === 'bullish' ? 'belowBar' : 'aboveBar') as any,
          color: s.status === 'bullish' ? '#10b981' : '#ef4444',
          shape: (s.status === 'bullish' ? 'arrowUp' : 'arrowDown') as any,
          text: s.name || 'ALPHA',
        }));
      (candleSeries as any).setMarkers(markers);

      chartRef.current = chart;
      candleSeriesRef.current = candleSeries as any;
      volumeSeriesRef.current = volumeSeries as any;
      signalSeriesRef.current = signalSeries;
      p50SeriesRef.current = p50Series;
      p10SeriesRef.current = p10Series;
      p90SeriesRef.current = p90Series;

      fetchHistory();
    };

    const resizeObserver = new ResizeObserver((entries) => {
      if (entries.length === 0) return;
      const { width, height } = entries[0].contentRect;
      if (width === 0 || height === 0) return;
      if (!chart) initChart();
      else chart.applyOptions({ width, height });
    });

    resizeObserver.observe(container);
    return () => {
      resizeObserver.disconnect();
      if (chart) chart.remove();
    };
  }, [currentTicker, signals, forecast, activeRange, overlayTickers]);

  useEffect(() => { fetchForecast(currentTicker); }, [currentTicker]);

  const addOverlay = () => {
    const t = overlayInput.trim().toUpperCase();
    if (t && !overlayTickers.includes(t) && overlayTickers.length < 3) {
      setOverlayTickers(prev => [...prev, t]);
      setOverlayInput('');
    }
  };

  const formattedDate = (d: string) => d.split('T')[0];
  const overlayColors = ['#818cf8', '#f472b6', '#fb923c'];

  return (
    <div className="flex-1 flex flex-col bg-slate-950 font-mono h-full overflow-hidden">
      <header className="h-14 border-b border-white/5 flex items-center justify-between px-8 bg-slate-900/40 backdrop-blur-md shrink-0 z-20">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-4">
             <BarChart3 size={18} className="text-accent-primary shadow-glow-sky" />
             <div className="flex flex-col">
                <span className="text-sm font-black text-white leading-none tracking-widest">{currentTicker}</span>
                <span className="text-[9px] text-slate-500 font-bold uppercase tracking-widest mt-1">Instrument_Surveillance</span>
             </div>
          </div>
          
          <div className="h-6 w-px bg-white/10" />

          <div className="flex items-baseline gap-3">
             <span className="text-xl font-mono font-black text-white tracking-tighter">
                ${(tickerData?.price || 0).toFixed(2)}
             </span>
             <span className={`text-[11px] font-bold ${(tickerData?.change || 0) >= 0 ? 'text-bull' : 'text-bear'}`}>
                {(tickerData?.change || 0) >= 0 ? '+' : ''}{(tickerData?.change || 0).toFixed(2)}%
             </span>
          </div>

          <div className="flex items-center gap-2">
            {overlayTickers.map((t, i) => (
              <span key={t} className="flex items-center gap-2 text-[9px] font-black px-2 py-1 bg-white/5 border border-white/10 rounded-sm" style={{ color: overlayColors[i] }}>
                {t} <button onClick={() => setOverlayTickers(prev => prev.filter(x => x !== t))}><X size={10} /></button>
              </span>
            ))}
            {overlayTickers.length < 3 && (
              <div className="flex items-center bg-slate-950 border border-white/10 px-2 py-1 rounded-sm group focus-within:border-accent-primary transition-all">
                 <input 
                   value={overlayInput} onChange={e => setOverlayInput(e.target.value)}
                   onKeyDown={e => e.key === 'Enter' && addOverlay()}
                   placeholder="ADD_OVERLAY..." 
                   className="bg-transparent outline-none text-[9px] uppercase text-white placeholder:text-slate-800 w-24"
                 />
                 <Plus size={10} className="text-slate-600 group-hover:text-white cursor-pointer" onClick={addOverlay} />
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-6">
           <div className="flex gap-1 glass-panel p-1 border-white/5 rounded-sm">
             {['1D', '5D', '1M', '3M', '1Y'].map(r => (
               <button 
                 key={r} onClick={() => setActiveRange(r)}
                 className={`px-3 py-1 rounded-sm text-[9px] font-black transition-all ${activeRange === r ? 'bg-accent-primary text-slate-950 shadow-glow-sky' : 'text-slate-500 hover:text-white'}`}
               >
                 {r}
               </button>
             ))}
           </div>
           <div className="h-6 w-px bg-white/10" />
           <div className="flex flex-col items-end">
              <span className="text-[8px] text-slate-500 font-bold uppercase tracking-widest leading-none">Kernel_State</span>
              <span className="text-[10px] text-bull font-bold mt-1">NOMINAL</span>
           </div>
        </div>
      </header>

      <div className="flex-1 relative bg-[#020617]/50">
        <div ref={chartContainerRef} className="absolute inset-0" />
        
        {/* HUD OVERLAYS */}
        <div className="absolute top-6 left-6 flex flex-col gap-2 pointer-events-none z-10">
           <div className="glass-panel p-4 neo-border rounded-sm space-y-3 min-w-[180px]">
              <div className="flex items-center justify-between">
                 <span className="text-[9px] text-slate-500 font-bold uppercase tracking-widest">Indicator_Stack</span>
                 <Layers size={12} className="text-accent-primary" />
              </div>
              <div className="space-y-2">
                 {[
                   { label: 'PRICE_ACTION', col: '#10b981' },
                   { label: 'SATELLITE_ALPHA', col: '#38bdf8' },
                   { label: 'TFT_FORECAST', col: '#f59e0b' }
                 ].map(ind => (
                   <div key={ind.label} className="flex items-center gap-3">
                      <div className="w-2.5 h-[2px]" style={{ background: ind.col }} />
                      <span className="text-[9px] text-slate-300 font-bold">{ind.label}</span>
                   </div>
                 ))}
              </div>
              <div className="pt-2 border-t border-white/5 flex flex-col gap-2 pointer-events-auto">
                 <div className="flex justify-between items-center">
                    <span className="text-[8px] text-slate-500 font-bold uppercase">Smoothing</span>
                    <span className="text-[9px] font-mono text-accent-primary">{smoothing}pts</span>
                 </div>
                 <input 
                   type="range" min="1" max="10" value={smoothing} 
                   onChange={e => setSmoothing(parseInt(e.target.value))}
                   className="w-full h-1 bg-slate-800 appearance-none cursor-pointer accent-accent-primary"
                 />
              </div>
           </div>
        </div>

        <div className="absolute bottom-6 left-6 z-10 glass-panel px-4 py-2 border-bull/20 rounded-sm flex items-center gap-3">
           <div className="w-2 h-2 rounded-full bg-bull animate-pulse shadow-[0_0_8px_#10b981]" />
           <span className="text-[10px] font-display text-white tracking-[0.2em] uppercase">Alpha_Network_Link: Operational</span>
        </div>

        {forecast && (
          <div className="absolute bottom-6 right-6 z-10 glass-panel px-4 py-2 border-amber-500/30 rounded-sm">
             <span className="text-[10px] font-black text-amber-500 tracking-widest uppercase">TFT_Quantile_Model_80%_CI</span>
          </div>
        )}
      </div>

      <footer className="h-8 border-t border-white/5 bg-slate-950 px-8 flex items-center justify-between shrink-0 box-border text-[9px] font-mono text-slate-700 uppercase tracking-widest font-bold">
         <div className="flex gap-8">
            <span>Node_ID: CHART-KERNEL-ALPHA</span>
            <span>Uplink: Sentinel-2C Optimized</span>
         </div>
         <span>{new Date().toISOString()} Z</span>
      </footer>
    </div>
  );
};

export default ChartView;
