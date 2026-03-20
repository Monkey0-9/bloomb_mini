/**
 * SatTrade 2.0 - Institutional Design Tokens
 * TypeScript mirror of terminal.css for WebGL/Three.js contexts
 */

export const THEME = {
  colors: {
    bgBase: '#070B0F',
    bgSurface: '#0D1117',
    bgCard: '#161B22',
    bgHover: '#1C2128',
    bgOverlay: 'rgba(7, 11, 15, 0.92)',

    neonBull: '#00FF9D',
    neonBear: '#FF4560',
    neonSignal: '#00D4FF',
    neonWarn: '#FFB800',
    neonPurple: '#BD93F9',
    
    neonDimBull: 'rgba(0, 255, 157, 0.12)',
    neonDimBear: 'rgba(255, 69, 96, 0.12)',

    textPrimary: '#E6EDF3',
    textSecondary: '#8B949E',
    textTertiary: '#484F58',
    textData: '#CDD9E5',

    borderSubtle: '#1A2332',
    borderDefault: '#2D3748',
    borderFocus: '#388BFD',
  },

  fonts: {
    data: "'IBM Plex Mono', 'Fira Code', monospace",
    ui: "'Inter', system-ui, sans-serif",
  },

  // GL-specific hex values for Three.js Materials
  gl: {
    bull: 0x00FF9D,
    bear: 0xFF4560,
    signal: 0x00D4FF,
    warn: 0xFFB800,
    purple: 0xBD93F9,
    bgBase: 0x070B0F,
    bgSurface: 0x0D1117,
    borderSubtle: 0x1A2332,
    textData: 0xCDD9E5,
  }
} as const;

export type ThemeType = typeof THEME;
