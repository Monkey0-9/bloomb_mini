import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, ShieldAlert, Zap, Box } from 'lucide-react';

const AlertHub = () => {
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    // Initial institutional engagement after 2s
    const timer = setTimeout(() => {
      const loginAlert = {
        id: 'AUTH',
        type: 'SYSTEM',
        title: 'SESSION ESTABLISHED',
        detail: 'HFT Pipeline verified. Zero drift detected in MAERSK/ZIM signals.',
        icon: Zap,
        color: 'text-accent-primary border-accent-primary'
      };
      setAlerts(prev => [loginAlert, ...prev]);
    }, 2000);

    // Dynamic alert generation (every 45s)
    const interval = setInterval(() => {
       const newAlert = {
          id: Date.now(),
          type: 'SIGNAL',
          title: 'ORBITAL ANOMALY',
          detail: 'High vessel density detected in Singapore Sector 4. IC: 0.082',
          icon: Zap,
          color: 'text-bull border-bull'
       };
       setAlerts(prev => [newAlert, ...prev].slice(0, 3));
    }, 45000);

    return () => {
      clearTimeout(timer);
      clearInterval(interval);
    };
  }, []);

  const removeAlert = (id: any) => {
    setAlerts(prev => prev.filter(a => a.id !== id));
  };

  return (
    <div className="fixed bottom-12 right-6 z-[60] flex flex-col gap-3 w-[320px] pointer-events-none">
      <AnimatePresence>
        {alerts.map((alert) => (
          <motion.div
            key={alert.id}
            initial={{ x: 350, opacity: 0, scale: 0.9 }}
            animate={{ x: 0, opacity: 1, scale: 1 }}
            exit={{ x: 350, opacity: 0, scale: 0.8 }}
            className={`pointer-events-auto bg-surface-2/90 backdrop-blur-xl border-l-[3px] ${alert.color} p-4 shadow-2xl relative group overflow-hidden border border-white/5`}
          >
            {/* PROGRESS TIMER */}
            <motion.div 
               initial={{ width: '100%' }}
               animate={{ width: '0%' }}
               transition={{ duration: 15, ease: 'linear' }}
               onAnimationComplete={() => removeAlert(alert.id)}
               className={`absolute bottom-0 left-0 h-[1px] ${alert.color.split(' ')[0]} opacity-30`}
            />

            <div className="flex gap-3">
              <div className={`mt-0.5 ${alert.color.split(' ')[0]}`}>
                 <alert.icon size={14} />
              </div>
              <div className="flex flex-col gap-0.5">
                  <div className="flex justify-between items-start">
                    <span className="type-h1 text-[11px] tracking-wider text-white">{alert.title}</span>
                    <button onClick={() => removeAlert(alert.id)} title="Close Alert" className="text-text-4 hover:text-white transition-colors">
                        <Box size={10} />
                    </button>
                  </div>
                  <p className="type-data-xs text-text-2 leading-tight lowercase tracking-wide italic">{alert.detail}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

export default AlertHub;

