"""
Strategic Global Intelligence Layer.
Zero API keys. All data from public domain sources:
- Active conflict zones: ACLED-derived static intelligence + GDELT real-time
- Military infrastructure: Open-source intelligence (OSINT)
- Nuclear facilities: IAEA public records
- Sanctions regimes: OFAC/UN public lists
- Economic chokepoints: maritime + logistics intelligence
"""
from datetime import UTC, datetime

# ── Active Conflict Zones ─────────────────────────────────────────────────
CONFLICT_ZONES = [
    {"id":"UKR","name":"Ukraine-Russia War","lat":48.9,"lon":31.2,"type":"WAR","intensity":"EXTREME",
     "actors":["Russia","Ukraine"],"fatalities_estimate":500000,"displacement_m":14.0,
     "started":"2022-02-24","ticker_impact":["WHEAT","NG","ALU","XOM","GAZP"],"risk_score":98,
     "summary":"Full-scale conventional warfare. Major disruption to grain and energy markets."},
    {"id":"GAZ","name":"Gaza Conflict","lat":31.4,"lon":34.3,"type":"WAR","intensity":"SEVERE",
     "actors":["Israel","Hamas","PIJ"],"fatalities_estimate":42000,"displacement_m":2.0,
     "started":"2023-10-07","ticker_impact":["OIL","GOLD","LMT","RTX","BA"],"risk_score":92,
     "summary":"Urban warfare. Red Sea shipping disruptions. Oil/defence sector impact."},
    {"id":"SDN","name":"Sudan Civil War","lat":15.6,"lon":32.5,"type":"WAR","intensity":"SEVERE",
     "actors":["SAF","RSF"],"fatalities_estimate":15000,"displacement_m":8.0,
     "started":"2023-04-15","ticker_impact":["GOLD","OIL"],"risk_score":88,
     "summary":"Major humanitarian crisis. African commodities under pressure."},
    {"id":"SYR","name":"Syria (Ongoing)","lat":34.8,"lon":38.9,"type":"CONFLICT","intensity":"HIGH",
     "actors":["HTS","SDF","Turkey","Iran","Russia"],"fatalities_estimate":600000,"displacement_m":13.5,
     "started":"2011-03-15","ticker_impact":["OIL","NG","GOLD"],"risk_score":75,
     "summary":"Fragmented conflict. Strategic importance for energy transit and geopolitics."},
    {"id":"ETH","name":"Ethiopia (TPLF/Amhara Tensions)","lat":11.6,"lon":39.6,"type":"CONFLICT","intensity":"MODERATE",
     "actors":["ENDF","TPLF","Fano"],"fatalities_estimate":500000,"displacement_m":4.0,
     "started":"2020-11-04","ticker_impact":["COFFEE","GOLD"],"risk_score":65,
     "summary":"Intermittent conflict affecting Horn of Africa stability and commodity flows."},
    {"id":"YEM","name":"Yemen War","lat":15.6,"lon":48.5,"type":"WAR","intensity":"HIGH",
     "actors":["Houthis","Saudi Coalition","UAE"],"fatalities_estimate":150000,"displacement_m":4.5,
     "started":"2015-03-26","ticker_impact":["OIL","SHIPPING","LMT"],"risk_score":80,
     "summary":"Houthi Red Sea attacks causing global shipping rates to surge 300%."},
    {"id":"MYN","name":"Myanmar Civil War","lat":19.7,"lon":96.1,"type":"WAR","intensity":"HIGH",
     "actors":["Military Junta","PDFs","EAOs"],"fatalities_estimate":50000,"displacement_m":2.7,
     "started":"2021-02-01","ticker_impact":["RARE-EARTH","TIN","TEAK"],"risk_score":70,
     "summary":"Junta vs resistance. Major supply disruption for rare earth minerals."},
    {"id":"MOZ","name":"Mozambique (ISIS-affiliate)","lat":-13.3,"lon":40.7,"type":"CONFLICT","intensity":"MODERATE",
     "actors":["ASWJ","FADM"],"fatalities_estimate":5000,"displacement_m":1.0,
     "started":"2017-10-05","ticker_impact":["LNG","TotalEnergies"],"risk_score":60,
     "summary":"Attacks on LNG infrastructure. Major impact on African gas exports."},
    {"id":"HOT-TWN","name":"Taiwan Strait Tension","lat":24.2,"lon":122.3,"type":"GEOPOLITICAL","intensity":"HIGH",
     "actors":["China PLA","Taiwan ROC"],"fatalities_estimate":0,"displacement_m":0,
     "started":"ongoing","ticker_impact":["TSM","NVDA","AMAT","LRCX","AAPL"],"risk_score":82,
     "summary":"Cross-strait military drills. Semiconductor supply chain under existential threat."},
    {"id":"HOT-KOR","name":"Korean Peninsula","lat":37.9,"lon":126.8,"type":"GEOPOLITICAL","intensity":"MODERATE",
     "actors":["DPRK","ROK","USA"],"fatalities_estimate":0,"displacement_m":0,
     "started":"ongoing","ticker_impact":["SAMSUNG","HYUNDAI","GOLD"],"risk_score":72,
     "summary":"Ongoing nuclear provocation cycle from DPRK affecting regional stability."},
    {"id":"IRN","name":"Iran Regional Proxy Operations","lat":33.9,"lon":50.6,"type":"CONFLICT","intensity":"HIGH",
     "actors":["IRGC","Hezbollah","Houthis","PMF"],"fatalities_estimate":0,"displacement_m":0,
     "started":"ongoing","ticker_impact":["OIL","GOLD","LMT","RTX"],"risk_score":84,
     "summary":"Multi-front proxy operations. Strait of Hormuz 20% of global oil flow at risk."},
    {"id":"MLI","name":"Sahel Crisis (Mali/Burkina/Niger)","lat":16.2,"lon":2.8,"type":"CONFLICT","intensity":"HIGH",
     "actors":["Wagner/Africa Corps","AQ-Sahel","JNIM"],"fatalities_estimate":25000,"displacement_m":2.0,
     "started":"2012-01-17","ticker_impact":["GOLD","URANIUM","COTTON"],"risk_score":68,
     "summary":"Sahel collapse. Uranium and gold supply affected. French departure accelerating instability."},
]

# ── Military Bases (OSINT-compiled) ──────────────────────────────────────────
MILITARY_BASES = [
    {"id":"RAM","name":"Ramstein Air Base","country":"Germany","lat":49.44,"lon":7.60,"operator":"USAF","type":"AIR","significance":"NATO Hub"},
    {"id":"KAD","name":"Kadena Air Base","country":"Japan","lat":26.35,"lon":127.77,"operator":"USAF","type":"AIR","significance":"Pacific Deterrence"},
    {"id":"DGO","name":"Camp Lemonnier","country":"Djibouti","lat":11.55,"lon":43.16,"operator":"USAF/USN","type":"JOINT","significance":"Horn of Africa Ops"},
    {"id":"AIN","name":"Al Udeid Air Base","country":"Qatar","lat":25.12,"lon":51.31,"operator":"USAF","type":"AIR","significance":"CENTCOM HQ"},
    {"id":"GUA","name":"Anderson AFB Guam","country":"Guam","lat":13.58,"lon":144.93,"operator":"USAF","type":"AIR","significance":"Pacific Strike"},
    {"id":"FDK","name":"Futenma Air Station","country":"Japan","lat":26.27,"lon":127.75,"operator":"USMC","type":"MARINE","significance":"Japan Deterrence"},
    {"id":"RKV","name":"RAF Lakenheath","country":"UK","lat":52.41,"lon":0.56,"operator":"USAF","type":"AIR","significance":"F-35 Strike Wing"},
    {"id":"INC","name":"Incirlik Air Base","country":"Turkey","lat":37.00,"lon":35.43,"operator":"USAF","type":"AIR","significance":"NATO Southern Flank"},
    {"id":"BAS","name":"Diego Garcia","country":"BIOT","lat":-7.31,"lon":72.42,"operator":"USAF/USN","type":"STRATEGIC","significance":"Indian Ocean Power Projection"},
    {"id":"PPT","name":"Pearl Harbor-Hickam","country":"USA","lat":21.35,"lon":-157.94,"operator":"USN/USAF","type":"NAVAL","significance":"INDOPACOM HQ"},
    {"id":"KAB","name":"Khmeimim Air Base","country":"Syria","lat":35.40,"lon":37.24,"operator":"Russian VKS","type":"AIR","significance":"Russian Middle East Presence"},
    {"id":"TAR","name":"Tartus Naval Base","country":"Syria","lat":34.89,"lon":35.87,"operator":"Russian Navy","type":"NAVAL","significance":"Only Russian Mediterranean Port"},
    {"id":"SAN","name":"Sanya Naval Base","country":"China","lat":18.24,"lon":109.56,"operator":"PLAN","type":"NAVAL","significance":"Nuclear Submarine Base"},
    {"id":"ADN","name":"Aden-Mukalla Garrison","country":"Yemen","lat":12.78,"lon":45.04,"operator":"Saudi-led Coalition","type":"JOINT","significance":"Red Sea Ops"},
    {"id":"ERT","name":"Erebuni Air Base","country":"Armenia","lat":40.12,"lon":44.47,"operator":"Russian VKS","type":"AIR","significance":"South Caucasus"},
]

# ── Nuclear Infrastructure ────────────────────────────────────────────────────
NUCLEAR_SITES = [
    {"id":"ZPO","name":"Zaporizhzhia NPP","country":"Ukraine","lat":47.51,"lon":34.59,"type":"POWER","status":"OCCUPIED","risk":"CRITICAL","reactors":6},
    {"id":"BUS","name":"Bushehr NPP","country":"Iran","lat":28.83,"lon":50.90,"type":"POWER","status":"ACTIVE","risk":"HIGH","reactors":1},
    {"id":"YGN","name":"Yongbyon Complex","country":"DPRK","lat":39.79,"lon":125.75,"type":"WEAPON","status":"ACTIVE","risk":"CRITICAL","reactors":1},
    {"id":"DIM","name":"Dimona Research Centre","country":"Israel","lat":31.00,"lon":35.15,"type":"WEAPON","status":"CLASSIFIED","risk":"HIGH","reactors":1},
    {"id":"KGA","name":"Khushab Reactor","country":"Pakistan","lat":32.07,"lon":72.20,"type":"WEAPON","status":"ACTIVE","risk":"HIGH","reactors":4},
    {"id":"SRV","name":"Seversk (Tomsk-7)","country":"Russia","lat":56.60,"lon":84.88,"type":"WEAPON","status":"ACTIVE","risk":"HIGH","reactors":5},
    {"id":"CHE","name":"Chernobyl Exclusion Zone","country":"Ukraine","lat":51.39,"lon":30.09,"type":"POWER","status":"DECOMMISSIONED","risk":"MODERATE","reactors":0},
    {"id":"FUK","name":"Fukushima Daiichi","country":"Japan","lat":37.42,"lon":141.03,"type":"POWER","status":"DECOMMISSIONING","risk":"MODERATE","reactors":0},
    {"id":"TRI","name":"Trident Submarine Base","country":"UK","lat":55.99,"lon":-4.76,"type":"WEAPON","status":"ACTIVE","risk":"HIGH","reactors":0},
    {"id":"FDG","name":"Fordo Enrichment Facility","country":"Iran","lat":34.88,"lon":49.37,"type":"WEAPON","status":"ACTIVE","risk":"CRITICAL","reactors":0},
]

# ── Sanctions Regimes ─────────────────────────────────────────────────────────
SANCTIONS_OVERLAYS = [
    {"id":"RUS","name":"Russia Sanctions","type":"COMPREHENSIVE","lat":60.0,"lon":55.0,
     "imposed_by":["USA","EU","UK","Canada","Japan","Australia"],
     "affected_sectors":["Finance","Oil","Gas","Defense","Tech"],
     "ticker_impact":["SBER","GAZP","ROSN","NVTK","XOM","BP"]},
    {"id":"IRN","name":"Iran Sanctions","type":"COMPREHENSIVE","lat":32.0,"lon":53.0,
     "imposed_by":["USA","EU","UN"],
     "affected_sectors":["Oil","Finance","Shipping","Defense"],
     "ticker_impact":["OIL","TANKER","GSK"]},
    {"id":"PRK","name":"North Korea Sanctions","type":"COMPREHENSIVE","lat":39.5,"lon":127.5,
     "imposed_by":["USA","EU","UN"],
     "affected_sectors":["All sectors","Coal","Seafood","Weapons"],
     "ticker_impact":["COAL","RARE-EARTH"]},
    {"id":"VEN","name":"Venezuela Sanctions","type":"TARGETED","lat":8.0,"lon":-66.0,
     "imposed_by":["USA","EU"],
     "affected_sectors":["Oil","Finance","Gold"],
     "ticker_impact":["OIL","GOLD","CVX"]},
    {"id":"MYN","name":"Myanmar Sanctions","type":"TARGETED","lat":19.0,"lon":96.0,
     "imposed_by":["USA","EU","UK"],
     "affected_sectors":["Defense","Finance","Gems"],
     "ticker_impact":["RUBY","JADE","TIN"]},
    {"id":"CHN","name":"China Tech Restrictions","type":"EXPORT_CONTROL","lat":35.0,"lon":105.0,
     "imposed_by":["USA"],
     "affected_sectors":["Semiconductors","AI","Quantum"],
     "ticker_impact":["TSM","NVDA","INTC","ASML","AMAT"]},
    {"id":"BLR","name":"Belarus Sanctions","type":"TARGETED","lat":53.0,"lon":28.0,
     "imposed_by":["USA","EU","UK"],
     "affected_sectors":["Finance","Potash","Transport"],
     "ticker_impact":["POTASH","MOC"]},
]

# ── Economic Chokepoints ──────────────────────────────────────────────────────
CHOKEPOINTS = [
    {"id":"SUEZ","name":"Suez Canal","lat":30.5,"lon":32.3,"type":"MARITIME_CHOKEPOINT",
     "daily_transit_ships":50,"oil_pct_world":12,"cargo_pct_world":30,
     "current_risk":"HIGH","risk_note":"Houthi attacks forcing Cape of Good Hope rerouting",
     "alt_route":"Cape of Good Hope (+14 days, +$500k per voyage)"},
    {"id":"HRM","name":"Strait of Hormuz","lat":26.5,"lon":56.3,"type":"MARITIME_CHOKEPOINT",
     "daily_transit_ships":21,"oil_pct_world":20,"cargo_pct_world":25,
     "current_risk":"HIGH","risk_note":"Iranian naval presence. 20% global oil flow",
     "alt_route":"None — only alternative is Trans-Arabian Pipeline"},
    {"id":"MAL","name":"Strait of Malacca","lat":2.5,"lon":102.0,"type":"MARITIME_CHOKEPOINT",
     "daily_transit_ships":85,"oil_pct_world":15,"cargo_pct_world":40,
     "current_risk":"MODERATE","risk_note":"Piracy risk. China-Taiwan tensions affect transit",
     "alt_route":"Lombok / Sunda Strait (+3 days)"},
    {"id":"BOS","name":"Bosphorus Strait","lat":41.1,"lon":29.1,"type":"MARITIME_CHOKEPOINT",
     "daily_transit_ships":35,"oil_pct_world":3,"cargo_pct_world":10,
     "current_risk":"LOW","risk_note":"Turkey controls access. Montreux Convention restrictions",
     "alt_route":"None for Black Sea traffic"},
    {"id":"GHD","name":"Gibraltar Strait","lat":35.9,"lon":-5.6,"type":"MARITIME_CHOKEPOINT",
     "daily_transit_ships":60,"oil_pct_world":5,"cargo_pct_world":20,
     "current_risk":"LOW","risk_note":"NATO controlled. Stable.",
     "alt_route":"None practical"},
    {"id":"DWK","name":"Danish Straits","lat":55.8,"lon":10.5,"type":"MARITIME_CHOKEPOINT",
     "daily_transit_ships":30,"oil_pct_world":2,"cargo_pct_world":8,
     "current_risk":"LOW","risk_note":"Baltic access. Russian Baltic fleet proximity.",
     "alt_route":"Kiel Canal"},
]

# ── Power Grid / Infrastructure Outages (simulated OSINT) ────────────────────
INFRASTRUCTURE_EVENTS = [
    {"id":"UKR-GRID","name":"Ukrainian Power Grid Attacks","lat":49.0,"lon":31.5,
     "type":"GRID_ATTACK","severity":"CRITICAL","status":"ONGOING",
     "affected_population":15000000,"note":"Systematic attacks on energy infrastructure"},
    {"id":"TX-FREEZE","name":"Texas Grid Vulnerability","lat":30.3,"lon":-97.7,
     "type":"GRID_FRAGILITY","severity":"HIGH","status":"MONITORED",
     "affected_population":29000000,"note":"Seasonal vulnerability in ERCOT"},
    {"id":"SUB-CUT","name":"Baltic Subsea Cable Disruptions","lat":57.5,"lon":18.0,
     "type":"INFRASTRUCTURE","severity":"HIGH","status":"ACTIVE",
     "affected_population":5000000,"note":"Multiple suspected sabotage events 2023-2024"},
    {"id":"IRN-INT","name":"Iran Internet Shutdowns","lat":35.7,"lon":51.4,
     "type":"DIGITAL","severity":"MODERATE","status":"RECURRING",
     "affected_population":85000000,"note":"Pattern: shutdowns during protests"},
]


def get_strategic_intelligence() -> dict:
    """Return the full strategic intelligence picture."""
    ts = datetime.now(UTC).isoformat()
    return {
        "conflicts": CONFLICT_ZONES,
        "military_bases": MILITARY_BASES,
        "nuclear_sites": NUCLEAR_SITES,
        "sanctions": SANCTIONS_OVERLAYS,
        "chokepoints": CHOKEPOINTS,
        "infrastructure_events": INFRASTRUCTURE_EVENTS,
        "generated_at": ts,
        "source": "OSINT/Public Domain Intelligence Synthesis",
    }
