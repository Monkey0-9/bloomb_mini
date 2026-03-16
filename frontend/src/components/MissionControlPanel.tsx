import React from 'react';
import { Activity } from 'lucide-react';

const MissionControlPanel = () => {
    return (
        <div className="flex flex-col border-b border-white/10 bg-void">
            <div className="px-3 py-2 border-b border-white/10 bg-surface-1/40 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Activity size={12} className="text-accent-primary animate-pulse" />
                    <span className="text-[10px] text-text-2 uppercase tracking-[0.2em] font-bold">Mission Control Live</span>
                </div>
                <div className="flex gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-bull animate-ping"></div>
                    <span className="text-[8px] font-mono text-bull uppercase">4K FEED</span>
                </div>
            </div>
            
            <div className="aspect-video bg-black relative group">
                <iframe 
                    className="w-full h-full grayscale-[0.3] contrast-125 brightness-90 group-hover:grayscale-0 transition-all pointer-events-auto"
                    src="https://www.youtube.com/embed/P9C25Un7xaM?autoplay=1&mute=1&controls=0&showinfo=0&rel=0&loop=1" 
                    title="Space Station Live"
                    frameBorder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                />
                <div className="absolute top-2 left-2 px-1.5 py-0.5 bg-void/60 border border-white/10 text-[8px] font-mono text-text-4 uppercase">CAM 01 // LEO_ORBIT</div>
            </div>
            
            <div className="p-3 bg-void flex flex-col gap-2">
                <div className="flex justify-between items-center text-[9px] font-mono">
                    <span className="text-text-4">SIGNAL STRENGTH:</span>
                    <span className="text-bull font-bold">98.2%</span>
                </div>
                <div className="w-full h-0.5 bg-white/5 overflow-hidden">
                    <div className="h-full bg-accent-primary w-[98%] shadow-[0_0_10px_#00FF9D]"></div>
                </div>
            </div>
        </div>
    );
};

export default MissionControlPanel;
