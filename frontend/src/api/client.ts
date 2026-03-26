const BASE = "http://localhost:8000"

export const api = {
  aircraft:          () => fetch(`${BASE}/api/aircraft`).then(r=>r.json()),
  aircraftMilitary:  () => fetch(`${BASE}/api/aircraft/military`).then(r=>r.json()),
  aircraftCargo:     () => fetch(`${BASE}/api/aircraft/cargo`).then(r=>r.json()),
  squawkAlerts:      () => fetch(`${BASE}/api/aircraft/squawk`).then(r=>r.json()),
  thermal:           (topN=100) => fetch(`${BASE}/api/thermal?top_n=${topN}`).then(r=>r.json()),
  vessels:           () => fetch(`${BASE}/api/vessels`).then(r=>r.json()),
  darkVessels:       () => fetch(`${BASE}/api/vessels/dark`).then(r=>r.json()),
  conflicts:         () => fetch(`${BASE}/api/conflicts`).then(r=>r.json()),
  chokepoints:       () => fetch(`${BASE}/api/conflicts/chokepoints`).then(r=>r.json()),
  satellites:        () => fetch(`${BASE}/api/satellites`).then(r=>r.json()),
  prices:            (tickers?:string) => fetch(`${BASE}/api/market/prices${tickers?`?tickers=${tickers}`:""}`).then(r=>r.json()),
  chart:             (ticker:string, period="3mo") => fetch(`${BASE}/api/market/chart/${ticker}?period=${period}`).then(r=>r.json()),
  options:           (ticker:string) => fetch(`${BASE}/api/market/options/${ticker}`).then(r=>r.json()),
  earnings:          () => fetch(`${BASE}/api/market/earnings`).then(r=>r.json()),
  macro:             () => fetch(`${BASE}/api/macro`).then(r=>r.json()),
  macroSeries:       (key:string) => fetch(`${BASE}/api/macro/${key}`).then(r=>r.json()),
  news:              (cat?:string) => fetch(`${BASE}/api/news${cat?`?category=${cat}`:""}`).then(r=>r.json()),
  newsSearch:        (q:string) => fetch(`${BASE}/api/news/search?q=${encodeURIComponent(q)}`).then(r=>r.json()),
  intelligence:      () => fetch(`${BASE}/api/intelligence`).then(r=>r.json()),
}

// WebSocket for live aircraft updates
export function connectLive(onMessage: (data:any)=>void): ()=>void {
  const ws = new WebSocket("ws://localhost:8000/ws")
  ws.onmessage = (e) => {
    try { onMessage(JSON.parse(e.data)) } catch {}
  }
  ws.onerror = (e) => console.error("WS error:", e)
  return () => ws.close()
}
