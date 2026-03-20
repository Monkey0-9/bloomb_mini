import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, Box, AlertTriangle } from 'lucide-react';

const AlertHub = () => {
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    const timer = setTimeout(() => {
      const loginAlert = {
        id: 'AUTH',
        type: 'SYSTEM',
        title: 'SESSION ESTABLISHED',
        detail: 'HFT Pipeline verified. Zero drift detected in sector signals.',
        icon: Zap,
        color: 'text-[var(--neon-signal)] border-[var(--neon-signal)]'
      };
      setAlerts(prev => [loginAlert, ...prev]);
    }, 2000);

    const interval = setInterval(() => {
       const newAlert = {
          id: Date.now(),
          type: 'SIGNAL',
          title: 'ORBITAL ANOMALY',
          detail: 'High vessel density detected in Singapore Sector 4. IC: 0.082',
          icon: Zap,
          color: 'text-[var(--neon-bull)] border-[var(--neon-bull)]'
       };
       setAlerts(prev => [newAlert, ...prev].slice(0, 3));
    }, 45000);

    return () => {
      clearTimeout(timer);
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    const handleWsAlert = (e: any) => {
      const msg = e.detail;
      if (msg && msg.emitter === 'OPENSKY_SQUAWK_MONITOR') {
        const newAlert = {
          id: msg.data.id || Date.now() + Math.random(),
          type: 'SQUAWK',
          title: `EMERGENCY SQUAWK: ${msg.data.squawk}`,
          detail: `${msg.data.callsign} · ${msg.data.type} · ${msg.data.lat.toFixed(2)}, ${msg.data.lon.toFixed(2)}`,
          icon: AlertTriangle,
          color: 'text-red-500 border-red-500'
        };
        setAlerts(prev => [newAlert, ...prev].slice(0, 5));
      }
    };
    window.addEventListener('terminal-alert', handleWsAlert);
    return () => window.removeEventListener('terminal-alert', handleWsAlert);
  }, []);

  const removeAlert = (id: any) => {
    setAlerts(prev => prev.filter(a => a.id !== id));
  };

  return (
    <div className="fixed bottom-10 right-4 z-[60] flex flex-col gap-2 w-[300px] pointer-events-none">
      <AnimatePresence>
        {alerts.map((alert) => (
          <motion.div
            key={alert.id}
            initial={{ x: 350, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 350, opacity: 0 }}
            className={`pointer-events-auto bg-[var(--bg-overlay)] backdrop-blur-md border-l-2 ${alert.color.split(' ')[0]} p-3 shadow-2xl relative border border-[var(--border-subtle)]`}
          >
            <motion.div 
               initial={{ width: '100%' }}
               animate={{ width: '0%' }}
               transition={{ duration: 15, ease: 'linear' }}
               onAnimationComplete={() => removeAlert(alert.id)}
               className={`absolute bottom-0 left-0 h-[1px] ${alert.color.split(' ')[1]} opacity-50`}
            />

            <div className="flex gap-2.5">
              <div className={`mt-0.5 ${alert.color.split(' ')[0]}`}>
                 <alert.icon size={12} />
              </div>
              <div className="flex-1 flex flex-col gap-0.5">
                  <div className="flex justify-between items-start">
                    <span className="text-[10px] tracking-widest text-[var(--text-primary)] font-bold uppercase">{alert.title}</span>
                    <button onClick={() => removeAlert(alert.id)} className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors">
                        <Box size={10} />
                    </button>
                  </div>
                  <p className="text-[9px] text-[var(--text-secondary)] leading-tight uppercase font-mono">{alert.detail}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

export default AlertHub;

