/** Lawny Formatters */
const Fmt = {
  ACTIVITY_META: {
    mow: { icon: '🔪', label: 'Mow', color: '#40C057' },
    fertilize: { icon: '🧪', label: 'Fertilize', color: '#FAB005' },
    aerate: { icon: '🌬️', label: 'Aerate', color: '#339AF0' },
    dethatch: { icon: '🪥', label: 'Dethatch', color: '#F06595' },
    water: { icon: '💧', label: 'Water', color: '#22B8CF' },
    overseed: { icon: '🌱', label: 'Overseed', color: '#51CF66' },
    weed_control: { icon: '🧹', label: 'Weed Control', color: '#FF6B6B' },
    pest_control: { icon: '🐛', label: 'Pest Control', color: '#CC5DE8' },
    soil_test: { icon: '🧫', label: 'Soil Test', color: '#845EF7' },
    lime: { icon: 'ite', label: 'Lime', color: '#E8D5B7' },
    topdress: { icon: '🏔️', label: 'Topdress', color: '#A0522D' },
    edge: { icon: '✂️', label: 'Edge', color: '#20C997' },
    leaf_cleanup: { icon: '🍂', label: 'Leaf Cleanup', color: '#FFA94D' },
    other: { icon: '📝', label: 'Other', color: '#868E96' },
  },

  activityIcon(type) { return (this.ACTIVITY_META[type] || this.ACTIVITY_META.other).icon; },
  activityLabel(type) { return (this.ACTIVITY_META[type] || this.ACTIVITY_META.other).label; },
  activityColor(type) { return (this.ACTIVITY_META[type] || this.ACTIVITY_META.other).color; },

  healthColor(score) {
    const colors = ['', '#8B4513', '#A0522D', '#B8860B', '#DAA520', '#9ACD32', '#6B8E23', '#52B788', '#40C057', '#2F9E44', '#00E676'];
    return colors[Math.max(1, Math.min(10, score || 5))];
  },

  healthLabel(score) {
    if (!score) return 'Not Rated';
    if (score <= 2) return 'Dead / Bare';
    if (score <= 4) return 'Patchy & Brown';
    if (score <= 5) return 'Average';
    if (score <= 7) return 'Good';
    if (score <= 9) return 'Very Good';
    return 'Championship Turf 🏆';
  },

  healthEmoji(score) {
    if (!score) return '❓';
    if (score <= 2) return '💀';
    if (score <= 4) return '🟤';
    if (score <= 5) return '🟡';
    if (score <= 7) return '🟢';
    if (score <= 9) return '✨';
    return '🏆';
  },

  date(d) {
    if (!d) return '—';
    const dt = new Date(d);
    return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  },

  dateTime(d) {
    if (!d) return '—';
    const dt = new Date(d);
    return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
  },

  relativeDate(d) {
    if (!d) return '—';
    const dt = new Date(d);
    const now = new Date();
    const diff = Math.floor((now - dt) / 86400000);
    if (diff === 0) return 'Today';
    if (diff === 1) return 'Yesterday';
    if (diff < 7) return `${diff} days ago`;
    return this.date(d);
  },

  daysUntil(d) {
    if (!d) return null;
    const dt = new Date(d);
    const now = new Date();
    return Math.ceil((dt - now) / 86400000);
  },

  sqft(n) {
    if (!n) return '0 sqft';
    return `${Math.round(n).toLocaleString()} sqft`;
  },

  temp(f) {
    if (f === null || f === undefined) return '—';
    return `${Math.round(f)}°F`;
  },

  precip(inches) {
    if (inches === null || inches === undefined) return '—';
    return `${inches.toFixed(2)}"`;
  },

  weatherIcon(code) {
    if (code === undefined || code === null) return '🌤️';
    if (code === 0) return '☀️';
    if (code <= 3) return '⛅';
    if (code <= 48) return '🌫️';
    if (code <= 57) return '🌦️';
    if (code <= 67) return '🌧️';
    if (code <= 77) return '❄️';
    if (code <= 82) return '🌧️';
    if (code <= 86) return '🌨️';
    return '⛈️';
  },

  hydrationStatus(delta) {
    if (delta === null || delta === undefined) return { icon: '❓', label: 'Unknown', cls: 'balanced' };
    if (Math.abs(delta) < 0.15) return { icon: '✅', label: 'Well Hydrated', cls: 'balanced' };
    if (delta < -0.5) return { icon: '🏜️', label: 'Significantly Under', cls: 'under-heavy' };
    if (delta < 0) return { icon: '💧', label: 'Slightly Under', cls: 'under' };
    if (delta > 0.5) return { icon: '🌊', label: 'Over-Watered', cls: 'over-heavy' };
    return { icon: '💦', label: 'Slightly Over', cls: 'over' };
  },

  hydrationBarColor(status) {
    const colors = {
      'balanced': 'var(--color-success)',
      'under': 'var(--color-warning)',
      'under-heavy': 'var(--color-danger)',
      'over': 'var(--color-info)',
      'over-heavy': '#7C3AED',
    };
    return colors[status] || 'var(--color-info)';
  },

  droughtIcon(level) {
    if (!level || level === 'None') return '🟢';
    if (level === 'D0') return '🟡';
    if (level === 'D1') return '🟠';
    if (level === 'D2') return '🔴';
    if (level === 'D3') return '⛔';
    if (level === 'D4') return '🚨';
    return '🟢';
  },
};
