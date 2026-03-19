import React from 'react';
import { Activity } from 'lucide-react';

const MissionControlPanel = () => {
    return (
        <div className="flex flex-col border-b border-[var(--border-subtle)] bg-[var(--bg-base)]">
            <div className="px-3 py-1.5 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)] flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Activity size={10} className="text-[var(--neon-bull)] animate-pulse" />
                    <span className="text-[9px] text-[var(--text-secondary)] uppercase tracking-[0.1em] font-bold">Mission Control Live</span>
                </div>
                <div className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 bg-[var(--neon-bull)] shadow-[0_0_4px_var(--neon-bull)]"></div>
                    <span className="text-[8px] font-mono text-[var(--neon-bull)] uppercase">4K FEED</span>
                </div>
            </div>
            
            <div className="aspect-video bg-[#000] relative group overflow-hidden">
                <iframe 
                    className="w-full h-full grayscale-[0.3] contrast-125 brightness-90 group-hover:grayscale-0 group-hover:brightness-100 transition-all pointer-events-none scale-105"
                    src="https://www.youtube.com/embed/P9C25Un7xaM?autoplay=1&mute=1&controls=0&showinfo=0&rel=0&loop=1&playlist=P9C25Un7xaM" 
                    title="Earth from Space Live"
                    frameBorder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                />
                <div className="absolute inset-0 pointer-events-none border border-[var(--neon-bull)]/20 shadow-[inset_0_0_40px_rgba(0,0,0,0.5)]"></div>
                <div className="absolute top-1.5 left-1.5 px-1.5 py-0.5 bg-[var(--bg-overlay)] border border-[var(--border-subtle)] text-[8px] font-mono text-[var(--neon-bull)] uppercase flex items-center gap-1.5">
                    <div className="w-1 h-1 bg-[var(--neon-bull)] animate-pulse"></div>
                    CAM 01 // LEO_ORBITAL_SYNTH
                </div>
            </div>
            
            <div className="p-2.5 bg-[var(--bg-base)] flex flex-col gap-1.5">
                <div className="flex justify-between items-center text-[9px] font-mono">
                    <span className="text-[var(--text-tertiary)] uppercase">Telemetry Sync:</span>
                    <span className="text-[var(--neon-bull)] font-bold">98.2%</span>
                </div>
                <div className="w-full h-1 bg-[var(--bg-surface)] overflow-hidden">
                    <div className="h-full bg-[var(--neon-bull)] w-[98%] shadow-[0_0_8px_var(--neon-bull)]"></div>
                </div>
            </div>
        </div>
    );
};

export default MissionControlPanel;
