import { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, IChartApi, ISeriesApi } from 'lightweight-charts';

const ChartView = () => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const areaSeriesRef = useRef<ISeriesApi<"Area"> | null>(null);
  const signalSeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const [activeRange, setActiveRange] = useState('1M');

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const container = chartContainerRef.current;
    let chart: IChartApi | null = null;

    const initChart = () => {
      if (chart) return;
      if (container.clientWidth === 0 || container.clientHeight === 0) return;

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

      const areaSeries = chart.addAreaSeries({
        lineColor: '#00C8FF',
        topColor: 'rgba(0, 200, 255, 0.15)',
        bottomColor: 'rgba(0, 200, 255, 0.01)',
        lineWidth: 2,
      });

      const signalSeries = chart.addLineSeries({
        lineColor: '#00C8FF', 
        lineWidth: 2,
        title: 'SAT SIGNAL',
      });

      areaSeries.setData([
        { time: '2026-02-13', value: 115.40 },
        { time: '2026-02-14', value: 116.20 },
        { time: '2026-02-15', value: 118.20 },
        { time: '2026-02-16', value: 119.50 },
        { time: '2026-02-17', value: 120.30 },
        { time: '2026-02-18', value: 122.40 },
        { time: '2026-02-19', value: 121.10 },
        { time: '2026-02-20', value: 123.00 },
        { time: '2026-02-21', value: 124.20 },
        { time: '2026-02-22', value: 125.80 },
        { time: '2026-02-23', value: 126.10 },
        { time: '2026-02-24', value: 128.40 },
      ]);

      signalSeries.setData([
        { time: '2026-02-13', value: 45 },
        { time: '2026-02-14', value: 82 },
        { time: '2026-02-15', value: 85 },
        { time: '2026-02-16', value: 88 },
        { time: '2026-02-17', value: 89 },
        { time: '2026-02-18', value: 90 },
        { time: '2026-02-19', value: 88 },
        { time: '2026-02-20', value: 85 },
        { time: '2026-02-21', value: 82 },
        { time: '2026-02-22', value: 80 },
        { time: '2026-02-23', value: 78 },
        { time: '2026-02-24', value: 75 },
      ]);

      areaSeries.setMarkers([
        { time: '2026-02-14', position: 'belowBar', color: '#00C8FF', shape: 'circle', text: 'SIGNAL' },
        { time: '2026-02-17', position: 'aboveBar', color: '#00FF9D', shape: 'arrowUp', text: 'E-BEAT' },
      ]);

      chart.timeScale().fitContent();
      chartRef.current = chart;
      areaSeriesRef.current = areaSeries;
      signalSeriesRef.current = signalSeries;
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
  }, []);

  return (
    <div className="flex-1 flex flex-col bg-void overflow-hidden">
      {/* CHART HEADER */}
      <div className="h-11 border-b border-white/5 flex items-center justify-between px-4 shrink-0 bg-surface-1/40">
         <div className="flex items-center gap-4">
            <div className="flex flex-col leading-tight">
               <span className="type-data-hero text-[16px] text-accent-primary font-bold">AMKBY US Equity</span>
               <span className="type-data-xs text-text-4 uppercase tracking-[0.2em]">Maersk — Sat-Monitoring: ACTIVE</span>
            </div>
            <div className="h-6 w-[1px] bg-white/5 mx-2"></div>
            <div className="flex items-baseline gap-2 tabular-nums">
               <span className="type-data-md text-text-0 font-bold">128.40</span>
               <span className="type-data-xs text-bull font-bold">+1.86%</span>
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

      {/* THE CHART CANVAS */}
      <div className="flex-1 relative">
         <div ref={chartContainerRef} className="absolute inset-0" />
         
         {/* LEGEND OVERLAY (TOP LEFT) */}
         <div className="absolute top-4 left-4 flex flex-col gap-1 pointer-events-none z-10 bg-void/40 backdrop-blur-sm p-2 rounded">
            <div className="flex items-center gap-2">
               <div className="w-3 h-[2px] bg-bull"></div>
               <span className="type-data-xs text-text-2">PRICE <span className="text-text-4 ml-2">USD</span></span>
            </div>
            <div className="flex items-center gap-2">
               <div className="w-3 h-[2px] bg-accent-primary"></div>
               <span className="type-data-xs text-accent-primary">SAT SIGNAL <span className="text-text-4 ml-2">Norm. 0-100</span></span>
            </div>
         </div>
         
         {/* SIGNAL ALERT OVERLAY (TOP RIGHT) */}
         <div className="absolute top-4 right-4 z-10 px-3 py-2 bg-surface-1/80 border border-bull/30 rounded-sm backdrop-blur-md">
            <div className="flex items-center gap-2">
               <div className="w-1.5 h-1.5 rounded-full bg-bull shadow-glow-bull"></div>
               <span className="type-h1 text-[10px] text-bull tracking-widest">SIGNAL LEAD: +72H</span>
            </div>
         </div>
      </div>
      
      {/* CHART STATUS FOOTER */}
      <div className="h-8 border-t border-white/5 flex items-center justify-between px-4 bg-void shrink-0">
         <span className="type-data-xs text-text-4 uppercase tracking-[0.2em]">Source: <span className="text-text-2">Sentinel-2A | SAR Radar</span></span>
         <span className="type-data-xs text-text-4 uppercase tracking-[0.2em]">Precision Score: <span className="text-accent-primary">99.4%</span></span>
      </div>
    </div>
  );
};

export default ChartView;
