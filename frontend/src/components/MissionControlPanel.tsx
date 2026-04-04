import React from 'react';
import { Activity } from 'lucide-react';

const MissionControlPanel = () => {
    const [volume, setVolume] = React.useState(0);
    const [telemetry, setTelemetry] = React.useState(98.2);

    return (
        <div className="flex flex-col border-b border-[var(--border-subtle)] bg-[var(--bg-base)]">
            <div className="px-3 py-1.5 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)] flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Activity size={10} className="text-[var(--neon-bull)] animate-pulse" />
                    <span className="text-[9px] text-[var(--text-secondary)] uppercase tracking-[0.1em] font-bold">Mission Control Live</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1.5">
                        <div className="w-1.5 h-1.5 bg-[var(--neon-bull)] shadow-[0_0_4px_var(--neon-bull)]"></div>
                        <span className="text-[8px] font-mono text-[var(--neon-bull)] uppercase">4K FEED</span>
                    </div>
                    <div className="flex items-center gap-1 border-l border-[var(--border-subtle)] pl-2">
                        <span className="text-[7px] text-[var(--text-tertiary)] uppercase font-mono">VOL</span>
                        <input 
                            type="range" 
                            min="0" max="100" 
                            value={volume} 
                            onChange={(e) => setVolume(parseInt(e.target.value))}
                            className="w-10 h-[2px] bg-[var(--bg-surface)] appearance-none cursor-pointer accent-[var(--neon-bull)]"
                        />
                    </div>
                </div>
            </div>
            
            <div className="aspect-video bg-[#000] relative group overflow-hidden">
                <iframe 
                    className="w-full h-full grayscale-[0.3] contrast-125 brightness-90 group-hover:grayscale-0 group-hover:brightness-100 transition-all pointer-events-none scale-105"
                    src={`https://www.youtube.com/embed/P9C25Un7xaM?autoplay=1&mute=${volume === 0 ? 1 : 0}&controls=0&showinfo=0&rel=0&loop=1&playlist=P9C25Un7xaM`} 
                    title="Earth from Space Live"
                    frameBorder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                />
                <div className="absolute inset-0 pointer-events-none border border-[var(--neon-bull)]/20 shadow-[inset_0_0_40px_rgba(0,0,0,0.5)]"></div>
                
                <div className="absolute bottom-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="px-1.5 py-0.5 bg-black/60 border border-[var(--neon-bull)] text-[7px] text-[var(--neon-bull)] uppercase font-mono">REC</button>
                    <button className="px-1.5 py-0.5 bg-black/60 border border-[var(--border-subtle)] text-[7px] text-white uppercase font-mono">HD</button>
                </div>

                <div className="absolute top-1.5 left-1.5 px-1.5 py-0.5 bg-[var(--bg-overlay)] border border-[var(--border-subtle)] text-[8px] font-mono text-[var(--neon-bull)] uppercase flex items-center gap-1.5">
                    <div className="w-1 h-1 bg-[var(--neon-bull)] animate-pulse"></div>
                    CAM 01 // LEO_ORBITAL_SYNTH
                </div>
            </div>
            
            <div className="p-2.5 bg-[var(--bg-base)] flex flex-col gap-1.5">
                <div className="flex justify-between items-center text-[9px] font-mono">
                    <span className="text-[var(--text-tertiary)] uppercase">Telemetry Sync:</span>
                    <span className="text-[var(--neon-bull)] font-bold">{telemetry}%</span>
                </div>
                <div className="w-full h-1 bg-[var(--bg-surface)] overflow-hidden relative cursor-pointer group">
                    <input 
                        type="range" 
                        min="0" max="100" step="0.1"
                        value={telemetry}
                        onChange={(e) => setTelemetry(parseFloat(e.target.value))}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                    />
                    <div 
                        className="h-full bg-[var(--neon-bull)] shadow-[0_0_8px_var(--neon-bull)] transition-all duration-300"
                        style={{ width: `${telemetry}%` }}
                    ></div>
                </div>
                <div className="flex justify-between mt-0.5">
                    <button onClick={() => setTelemetry(98.2)} className="text-[7px] text-[var(--text-tertiary)] uppercase hover:text-[var(--neon-bull)] font-mono tracking-tighter">RE-SYNC</button>
                    <button className="text-[7px] text-[var(--text-tertiary)] uppercase hover:text-[var(--neon-bull)] font-mono tracking-tighter">DIAGNOSTICS</button>
                </div>
            </div>
        </div>
    );
};

export default MissionControlPanel;
