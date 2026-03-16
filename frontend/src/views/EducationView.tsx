import React from 'react';
import { BookOpen, Zap, Globe, Shield } from 'lucide-react';

const EducationView = () => {
  return (
    <div className="flex-1 bg-void overflow-y-auto custom-scrollbar p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-12">
          <h1 className="type-h1 text-3xl text-accent-primary tracking-[0.3em] uppercase mb-4">Intelligence Academy</h1>
          <p className="type-ui-md text-text-4 font-medium leading-relaxed uppercase tracking-widest">
            Master the terminal. Understand the data. Achieve Top 1% Global performance.
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          <EducationCard 
            icon={<Globe className="text-bull" />}
            title="Maritime Intelligence"
            description="Learn how to interpret AIS data, berth counts, and port throughput signals to predict global supply chain shifts."
          />
          <EducationCard 
            icon={<Zap className="text-accent-primary" />}
            title="Satellite Alpha"
            description="Deep dive into Sentinel-2 and SAR imagery analysis. Detect economic pivots before they hit the wire."
          />
          <EducationCard 
            icon={<Shield className="text-bear" />}
            title="Risk Management"
            description="Understand the 9 synchronous gates. From VaR 99% to Fat-finger protection, keep your capital safe."
          />
          <EducationCard 
            icon={<BookOpen className="text-text-2" />}
            title="Signal Theory"
            description="The math behind IC/ICIR. Differentiate between noise and high-fidelity intelligence in real-time."
          />
        </div>

        <section className="bg-surface-1 border border-white/5 p-8 rounded-sm mb-12">
          <h2 className="type-h1 text-lg text-text-0 mb-6 tracking-widest uppercase">System Operational Manual</h2>
          <div className="space-y-6">
            <ManualItem 
              step="01" 
              title="Select Ticker" 
              text="Hover over the watchlist or search for a specific entity to load dedicated intelligence overlays." 
            />
            <ManualItem 
              step="02" 
              title="Analyze Globe" 
              text="Switch between Thermal, Optical, and SAR layers to confirm physical activities on the ground." 
            />
            <ManualItem 
              step="03" 
              title="Execute" 
              text="Ensure all Risk Engine gates are green before submitting orders through the broker integration." 
            />
          </div>
        </section>
      </div>
    </div>
  );
};

const EducationCard = ({ icon, title, description }: any) => (
  <div className="bg-surface-1 border border-white/5 p-6 hover:border-accent-primary/50 transition-all group">
    <div className="w-12 h-12 bg-void flex items-center justify-center rounded-sm mb-4 border border-white/10 group-hover:shadow-glow-bull transition-all">
      {icon}
    </div>
    <h3 className="type-h1 text-sm text-text-1 mb-2 tracking-widest uppercase">{title}</h3>
    <p className="type-ui-sm text-text-4 leading-relaxed">{description}</p>
  </div>
);

const ManualItem = ({ step, title, text }: any) => (
  <div className="flex gap-6">
    <span className="type-data-hero text-accent-primary/30 text-2xl font-bold leading-none">{step}</span>
    <div>
      <h4 className="type-h1 text-xs text-text-1 mb-1 tracking-widest uppercase">{title}</h4>
      <p className="type-ui-sm text-text-4">{text}</p>
    </div>
  </div>
);

export default EducationView;
