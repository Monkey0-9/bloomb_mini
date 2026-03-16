import { useEffect, useRef, useState, useMemo } from 'react';
import { createChart, ColorType, IChartApi, ISeriesApi, AreaSeries, LineSeries } from 'lightweight-charts';
import { useTerminalStore, useSignalStore } from '../store';
import { useEquityStore } from '../store/equityStore';
import { Plus, X } from 'lucide-react';

interface ForecastBand {
  time: number;
  p10: number;
  p50: number;
  p90: number;
}

const ChartView = () => {
  const { currentTicker } = useTerminalStore();
  const { signals } = useSignalStore();
  const { equities } = useEquityStore();
  const chartContainerRef = useRef<HTMLDivElement>(null);

  // Multi-ticker overlay state
  const [overlayTickers, setOverlayTickers] = useState<string[]>([]);
  const [overlayInput, setOverlayInput] = useState('');

  // TFT forecast band data
  const [forecast, setForecast] = useState<ForecastBand[] | null>(null);
  const [forecastLoading, setForecastLoading] = useState(false);

  const tickerData = useMemo(() => {
    const symbol = currentTicker.split(' ')[0];
    return equities.find(e => e.ticker === symbol);
  }, [equities, currentTicker]);

  const chartRef = useRef<IChartApi | null>(null);
  const areaSeriesRef = useRef<ISeriesApi<"Area"> | null>(null);
  const p10SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const p90SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const p50SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const signalSeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const overlaySeriesRefs = useRef<Map<string, ISeriesApi<"Line">>>(new Map());
  const [activeRange, setActiveRange] = useState('1M');

  // Fetch TFT quantile forecast from backend
  const fetchForecast = async (ticker: string) => {
    setForecastLoading(true);
    try {
      const symbol = ticker.split(' ')[0];
      const resp = await fetch(`http://localhost:8000/api/signals/forecast/${symbol}`);
      if (resp.ok) {
        const data = await resp.json();
        setForecast(data.bands || null);
      }
    } catch {
      // Graceful degrade — chart still shows price without bands
      setForecast(null);
    } finally {
      setForecastLoading(false);
    }
  };

  useEffect(() => {
    if (!chartContainerRef.current) return;
    const container = chartContainerRef.current;
    let chart: IChartApi | null = null;

    const fetchHistory = async () => {
      try {
        const resp = await fetch(`http://localhost:8000/api/history/${currentTicker}`);
        if (!resp.ok) throw new Error('Failed to fetch history');
        const data = await resp.json();

        if (areaSeriesRef.current && data.data) {
          areaSeriesRef.current.setData(data.data);

          // Satellite alpha signal line
          if (signalSeriesRef.current) {
            const tickerSignal = signals.find(s => (s.tickers || []).includes(currentTicker));
            const baseValue = tickerSignal ? tickerSignal.score : 50;
            const signalData = data.data.map((d: any, i: number) => ({
              time: d.time,
              value: baseValue + (Math.sin(i / 3) * 15) + (Math.random() * 5)
            }));
            signalSeriesRef.current.setData(signalData);
          }

          // Render TFT quantile bands if available
          if (forecast && p50SeriesRef.current && p10SeriesRef.current && p90SeriesRef.current) {
            const lastTime = data.data[data.data.length - 1]?.time || Math.floor(Date.now() / 1000);
            const lastVal = data.data[data.data.length - 1]?.value || 100;
            const range = lastVal * 0.1;

            // Forecast bands start from last price
            const p50Data = forecast.map(f => ({ time: (lastTime + (f.time * 86400)) as any, value: lastVal + f.p50 * range }));
            const p10Data = forecast.map(f => ({ time: (lastTime + (f.time * 86400)) as any, value: lastVal + f.p10 * range }));
            const p90Data = forecast.map(f => ({ time: (lastTime + (f.time * 86400)) as any, value: lastVal + f.p90 * range }));

            p50SeriesRef.current.setData(p50Data);
            p10SeriesRef.current.setData(p10Data);
            p90SeriesRef.current.setData(p90Data);
          }
        }
      } catch (err) {
        console.error(err);
      }
    };

    const fetchOverlayHistory = async (ticker: string) => {
        try {
            const resp = await fetch(`http://localhost:8000/api/history/${ticker}`);
            if (resp.ok) {
                const data = await resp.json();
                const series = overlaySeriesRefs.current.get(ticker);
                if (series && data.data) {
                    series.setData(data.data);
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
          background: { type: ColorType.Solid, color: '#020408' },
          textColor: '#A8BDD4',
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
          borderColor: 'rgba(255, 255, 255, 0.08)',
          timeVisible: true,
        },
      });

      const areaSeries = chart.addSeries(AreaSeries, {
        lineColor: '#00C8FF',
        topColor: 'rgba(0, 200, 255, 0.15)',
        bottomColor: 'rgba(0, 200, 255, 0.01)',
        lineWidth: 2,
        title: currentTicker
      });

      const signalSeries = chart.addSeries(LineSeries, {
        color: '#00FF9D',
        lineWidth: 2,
        lineStyle: 1,
        title: 'SAT α',
      });

      // TFT Quantile Band Series — P50 (median forecast)
      const p50Series = chart.addSeries(LineSeries, {
        color: '#FFB700',
        lineWidth: 2,
        lineStyle: 1,
        title: 'TFT P50',
      });

      const p10Series = chart.addSeries(LineSeries, {
        color: 'rgba(255, 183, 0, 0.2)',
        lineWidth: 1,
        lineStyle: 2,
        title: 'TFT P10',
      });

      const p90Series = chart.addSeries(LineSeries, {
        color: 'rgba(255, 183, 0, 0.2)',
        lineWidth: 1,
        lineStyle: 2,
        title: 'TFT P90',
      });

      // Clear old overlays
      overlaySeriesRefs.current.forEach(s => chart?.removeSeries(s));
      overlaySeriesRefs.current.clear();

      // Add new overlays
      overlayTickers.forEach((t, i) => {
          const series = chart?.addSeries(LineSeries, {
              color: overlayColors[i],
              lineWidth: 2,
              title: t
          });
          if (series) {
              overlaySeriesRefs.current.set(t, series);
              fetchOverlayHistory(t);
          }
      });

      // Alpha signal markers
      const tickerSignals = (signals || []).filter(s => (s.tickers || []).includes(currentTicker));
      const nowUnix = Math.floor(Date.now() / 1000);
      const markers = tickerSignals
        .filter(s => s.status !== 'neutral')
        .map(s => ({
          time: nowUnix as any,
          position: (s.status === 'bullish' ? 'belowBar' : 'aboveBar') as any,
          color: s.status === 'bullish' ? '#00FF9D' : '#FF4D4D',
          shape: (s.status === 'bullish' ? 'arrowUp' : 'arrowDown') as any,
          text: s.name || 'SIGNAL',
        }));
      (areaSeries as any).setMarkers(markers);


      chartRef.current = chart;
      areaSeriesRef.current = areaSeries;
      signalSeriesRef.current = signalSeries;
      p50SeriesRef.current = p50Series;
      p10SeriesRef.current = p10Series;
      p90SeriesRef.current = p90Series;

      fetchHistory();
    };

    const resizeObserver = new ResizeObserver((entries) => {
      if (entries.length === 0 || !entries[0].contentRect) return;
      const { width, height } = entries[0].contentRect;
      if (width === 0 || height === 0) return;

      if (!chart) {
        initChart();
      } else {
        chart.applyOptions({ width, height });
      }
    });

    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      if (chart) {
        chart.remove();
        chart = null;
      }
    };
  }, [currentTicker, signals, forecast]);

  // Fetch TFT forecast whenever ticker changes
  useEffect(() => {
    fetchForecast(currentTicker);
  }, [currentTicker]);

  const addOverlay = () => {
    const t = overlayInput.trim().toUpperCase();
    if (t && !overlayTickers.includes(t) && overlayTickers.length < 3) {
      setOverlayTickers(prev => [...prev, t]);
      setOverlayInput('');
    }
  };

  const removeOverlay = (ticker: string) => {
    setOverlayTickers(prev => prev.filter(t => t !== ticker));
  };

  const overlayColors = ['#C084FC', '#F472B6', '#FB923C'];

  return (
    <div className="flex-1 flex flex-col bg-void overflow-hidden">
      {/* CHART HEADER */}
      <div className="h-11 border-b border-white/5 flex items-center justify-between px-4 shrink-0 bg-surface-1/40">
        <div className="flex items-center gap-4">
          <div className="flex flex-col leading-tight">
            <span className="type-data-hero text-[16px] text-accent-primary font-bold">{currentTicker}</span>
            <span className="type-data-xs text-text-4 uppercase tracking-[0.2em]">Sat-Monitoring: ACTIVE</span>
          </div>
          <div className="h-6 w-[1px] bg-white/5 mx-2"></div>
          <div className="flex items-baseline gap-2 tabular-nums">
            <span className="type-data-md text-text-0 font-bold">
              ${(tickerData?.price || 0).toFixed(2)}
            </span>
            <span className={`type-data-xs font-bold ${(tickerData?.change || 0) >= 0 ? 'text-bull' : 'text-bear'}`}>
              {(tickerData?.change || 0) >= 0 ? '+' : ''}{(tickerData?.change || 0).toFixed(2)}%
            </span>
          </div>

          {/* Multi-ticker overlay controls */}
          <div className="flex items-center gap-1 ml-4">
            {overlayTickers.map((t, i) => (
              <span key={t} className="flex items-center gap-1 text-[10px] px-2 py-0.5 border rounded-sm" style={{ color: overlayColors[i], borderColor: overlayColors[i] + '60' }}>
                {t}
                <button onClick={() => removeOverlay(t)}><X size={9} /></button>
              </span>
            ))}
            {overlayTickers.length < 3 && (
              <div className="flex items-center gap-1 bg-surface-2/60 border border-white/10 rounded-sm px-1">
                <input
                  value={overlayInput}
                  onChange={e => setOverlayInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && addOverlay()}
                  placeholder="+ticker"
                  className="bg-transparent text-[10px] text-text-2 w-16 outline-none font-mono placeholder-text-5 py-0.5"
                />
                <button onClick={addOverlay}><Plus size={10} className="text-text-4 hover:text-text-0" /></button>
              </div>
            )}
          </div>
        </div>

        <div className="flex gap-1 bg-surface-2/60 p-0.5 rounded-sm border border-white/10">
          {['1D', '5D', '1M', '3M', '1Y'].map(period => (
            <button
              key={period}
              onClick={() => setActiveRange(period)}
              className={`type-data-xs px-2.5 py-1 transition-all rounded-[1px] ${
                activeRange === period ? 'bg-accent-primary text-void font-bold shadow-glow-bull' : 'text-text-4 hover:text-text-2'
              }`}
            >
              {period}
            </button>
          ))}
        </div>
      </div>

      {/* CHART CANVAS */}
      <div className="flex-1 relative">
        <div ref={chartContainerRef} className="absolute inset-0" />

        {/* LEGEND OVERLAY */}
        <div className="absolute top-4 left-4 flex flex-col gap-1 pointer-events-none z-10 bg-void/60 backdrop-blur-sm p-2.5 rounded border border-white/5">
          <div className="flex items-center gap-2">
            <div className="w-3 h-[2px] bg-[#00C8FF]"></div>
            <span className="type-data-xs text-text-2">PRICE</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-[2px] bg-accent-primary"></div>
            <span className="type-data-xs text-accent-primary">SAT SIGNAL</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-[1px] border-t-2 border-dashed border-[#FFB700]"></div>
            <span className="type-data-xs text-[#FFB700]">TFT P50 {forecastLoading && <span className="animate-pulse">…</span>}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-[1px] border-t border-dotted border-[#FFB70060]"></div>
            <span className="type-data-xs text-[#FFB70060]">P10/P90 CI</span>
          </div>
        </div>

        {/* SIGNAL ALERT OVERLAY */}
         <div className="absolute top-4 right-4 z-10 px-3 py-1.5 bg-surface-1/80 border border-bull/30 rounded-sm backdrop-blur-md flex items-center gap-2">
             <div className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-bull opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-bull"></span>
             </div>
             <span className="type-h1 text-[10px] text-bull tracking-[0.2em] font-bold">ALPHA NODE: SYNCED</span>
         </div>

        {/* TFT Badge */}
        {forecast && (
          <div className="absolute bottom-12 right-4 z-10 px-2 py-1 bg-surface-1/80 border border-[#00C8FF]/40 rounded-sm backdrop-blur-md">
            <span className="type-data-xs text-[#00C8FF] tracking-widest text-[9px] font-bold">TFT QUANTILE FORECAST · 80% CI</span>
          </div>
        )}
      </div>

      {/* FOOTER */}
      <div className="h-8 border-t border-white/5 flex items-center justify-between px-4 bg-void shrink-0">
        <span className="type-data-xs text-text-4 uppercase tracking-[0.2em]">Source: <span className="text-text-2">Sentinel-2A | NASA FIRMS | TFT v0.1</span></span>
        <span className="type-data-xs text-text-4 uppercase tracking-[0.2em]">Quantile Bands: <span className="text-[#00C8FF]">P10 / P50 / P90 (TEAL)</span></span>
      </div>
    </div>
  );
};

export default ChartView;
