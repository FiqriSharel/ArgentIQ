import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';

const number = value => Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 });
const sourceDate = value => value?.slice(0, 16) || '—';
const epoch = value => Date.parse(`${value.slice(0, 10)}T${value.slice(11, 19)}Z`);

function HistoryChart({ points }) {
    const valid = points.filter(point => point.average_price !== null);
    if (!valid.length) return <div className="empty">No six-hour history for this selection.</div>;

    const width = 1000;
    const height = 360;
    const left = 75;
    const right = 22;
    const top = 20;
    const bottom = 45;
    const times = valid.map(point => epoch(point.bucket_time_source));
    const prices = valid.map(point => Number(point.average_price));
    const first = Math.min(...times);
    const last = Math.max(...times);
    const low = Math.min(...prices);
    const high = Math.max(...prices);
    const padding = Math.max((high - low) * 0.08, high * 0.03, 1);
    const yMin = Math.max(0, low - padding);
    const yMax = high + padding;
    const x = time => left + ((time - first) / (last - first || 1)) * (width - left - right);
    const y = price => top + ((yMax - price) / (yMax - yMin)) * (height - top - bottom);
    const segments = [];
    let path = '';
    valid.forEach((point, index) => {
        const time = times[index];
        const command = `${path ? 'L' : 'M'}${x(time).toFixed(1)},${y(prices[index]).toFixed(1)}`;
        if (index > 0 && time - times[index - 1] !== 6 * 3600000) {
            segments.push(path);
            path = `M${x(time).toFixed(1)},${y(prices[index]).toFixed(1)}`;
        } else {
            path += command;
        }
    });
    segments.push(path);
    const yTicks = [0, 1, 2, 3, 4].map(index => yMin + (yMax - yMin) * index / 4);

    return <div className="chart-scroll"><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Recorded average sell-order price over time, with breaks for missing buckets and orange circles for observations flagged for review">
        {yTicks.map(value => <g key={value}><line x1={left} x2={width - right} y1={y(value)} y2={y(value)} className="grid-line" /><text x={left - 12} y={y(value) + 4} className="axis-label" textAnchor="end">{number(value)}</text></g>)}
        {segments.map((segment, index) => <path key={index} d={segment} className="history-line" />)}
        {valid.map(point => <circle key={point.bucket_time_source} cx={x(epoch(point.bucket_time_source))} cy={y(Number(point.average_price))} r={point.review_flag ? 5 : 6} className={point.review_flag ? 'flag-point' : 'history-point'}><title>{sourceDate(point.bucket_time_source)} · {number(point.average_price)} silver per item · {number(point.item_amount)} items in bucket{point.review_flag ? ` · ${point.review_flag.replace('_', ' ')}` : ''}</title></circle>)}
        <text x={left} y={height - 12} className="axis-label">{sourceDate(valid[0].bucket_time_source)}</text>
        <text x={width - right} y={height - 12} className="axis-label" textAnchor="end">{sourceDate(valid[valid.length - 1].bucket_time_source)}</text>
    </svg></div>;
}

function App() {
    const [catalogue, setCatalogue] = useState({ items: [], locations: [], qualities: [] });
    const [history, setHistory] = useState(null);
    const [error, setError] = useState('');
    const [busy, setBusy] = useState(false);
    const [search, setSearch] = useState('');
    const [type, setType] = useState('');
    const [foodName, setFoodName] = useState('');
    const [tier, setTier] = useState('');
    const [enchantment, setEnchantment] = useState('');
    const [itemId, setItemId] = useState('T8_MEAL_STEW');
    const [locationId, setLocationId] = useState(2004);
    const [quality, setQuality] = useState(1);
    const [rangeDays, setRangeDays] = useState('all');

    useEffect(() => {
        fetch('/food-catalogue', { headers: { Accept: 'application/json' } })
            .then(async response => { const body = await response.json(); if (!response.ok) throw new Error(body.message); return body; })
            .then(setCatalogue)
            .catch(err => setError(err.message || 'Could not load the food catalogue.'));
    }, []);

    const types = useMemo(() => [...new Set(catalogue.items.map(item => item.food_type_code))].sort(), [catalogue.items]);
    const foodNames = useMemo(() => [...new Set(catalogue.items.filter(item => !type || item.food_type_code === type).map(item => item.display_name))].sort(), [catalogue.items, type]);
    const filtered = useMemo(() => catalogue.items.filter(item =>
        (!search || `${item.display_name} ${item.item_id}`.toLowerCase().includes(search.toLowerCase())) &&
        (!type || item.food_type_code === type) &&
        (!foodName || item.display_name === foodName) &&
        (!tier || Number(item.tier) === Number(tier)) &&
        (!enchantment || Number(item.enchantment) === Number(enchantment))
    ), [catalogue.items, search, type, foodName, tier, enchantment]);

    useEffect(() => {
        if (foodName && !foodNames.includes(foodName)) setFoodName('');
    }, [foodName, foodNames]);

    useEffect(() => {
        if (filtered.length && !filtered.some(item => item.item_id === itemId)) setItemId(filtered[0].item_id);
    }, [filtered, itemId]);

    useEffect(() => {
        if (!itemId || !catalogue.items.length || !filtered.some(item => item.item_id === itemId)) {
            setHistory(null);
            return;
        }
        const controller = new AbortController();
        setBusy(true);
        setHistory(null);
        setError('');
        const params = new URLSearchParams({ item_id: itemId, location_id: String(locationId), quality: String(quality) });
        fetch(`/food-history?${params}`, { signal: controller.signal, headers: { Accept: 'application/json' } })
            .then(async response => { const body = await response.json(); if (!response.ok) throw new Error(body.message); return body; })
            .then(body => { setHistory(body); setBusy(false); })
            .catch(err => { if (err.name !== 'AbortError') { setError(err.message || 'Could not load history.'); setBusy(false); } });
        return () => controller.abort();
    }, [itemId, locationId, quality, catalogue.items, filtered]);

    const points = history?.points || [];
    const latestTime = points.length ? epoch(points[points.length - 1].bucket_time_source) : 0;
    const visiblePoints = rangeDays === 'all' ? points : points.filter(point => epoch(point.bucket_time_source) >= latestTime - Number(rangeDays) * 86400000);
    const flagged = visiblePoints.filter(point => point.review_flag);
    const visibleMissing = visiblePoints.slice(1).reduce((total, point, index) => total + Math.max(0, Math.round((epoch(point.bucket_time_source) - epoch(visiblePoints[index].bucket_time_source)) / (6 * 3600000)) - 1), 0);

    return <div className="shell">
        <header className="topbar"><div className="brand"><span className="brand-dot" />Argent<strong>IQ</strong></div><nav><span>Asia food history</span><a href="/market">Current quotes</a></nav></header>
        <section className="hero"><div><p className="eyebrow">Asia server · prepared meals</p><h1>Food market history</h1><p>Explore recorded six-hour sell-order price averages from the downloaded database snapshot. Select an exact item variant, location, and quality.</p></div><div className="hero-tag">Historical observations only<br />Forecast method to be decided</div></section>
        <main className="panel">
            <div className="panel-heading"><div><h2>Select a food series</h2><p>Catalogue items without history remain selectable.</p></div><span className="count">{catalogue.items.length} catalogue variants</span></div>
            <div className="filters">
                <label>Search food<input value={search} onChange={event => setSearch(event.target.value)} placeholder="Name or item ID" /></label>
                <label>Food type<select value={type} onChange={event => setType(event.target.value)}><option value="">All types</option>{types.map(value => <option key={value}>{value}</option>)}</select></label>
                <label>Food<select value={foodNames.includes(foodName) ? foodName : ''} onChange={event => setFoodName(event.target.value)}><option value="">All foods</option>{foodNames.map(value => <option key={value} value={value}>{value}</option>)}</select></label>
                <label>Tier<select value={tier} onChange={event => setTier(event.target.value)}><option value="">All tiers</option>{[1, 2, 3, 4, 5, 6, 7, 8].map(value => <option key={value} value={value}>T{value}</option>)}</select></label>
                <label>Enchantment<select value={enchantment} onChange={event => setEnchantment(event.target.value)}><option value="">All levels</option>{[0, 1, 2, 3, 4].map(value => <option key={value} value={value}>+{value}</option>)}</select></label>
                <label>Exact item<select value={filtered.some(item => item.item_id === itemId) ? itemId : ''} onChange={event => setItemId(event.target.value)} disabled={!filtered.length}><option value="" disabled>{filtered.length ? 'Choose item' : 'No matching foods'}</option>{filtered.map(item => <option key={item.item_id} value={item.item_id}>{item.display_name} · T{item.tier} +{item.enchantment}</option>)}</select></label>
                <label>Location<select value={locationId} onChange={event => setLocationId(Number(event.target.value))}>{catalogue.locations.map(location => <option key={location.id} value={location.id}>{location.name}</option>)}</select></label>
                <label>Available quality<select value={quality} onChange={event => setQuality(Number(event.target.value))}>{catalogue.qualities.map(value => <option key={value} value={value}>{value}</option>)}</select></label>
            </div>
            {error && <div className="error" role="alert">{error}</div>}
            {catalogue.items.length > 0 && filtered.length === 0 && <div className="empty">No food matches these filters.</div>}
            {busy && <div className="loading">Loading saved history…</div>}
            {history && <section className="results">
                <div className="series-heading"><div><p className="eyebrow">Recorded average sell-order price</p><h2>{history.display_name} <span>· {history.location_name}</span></h2><p className="item-id">{history.item_id} · quality {history.quality} · six-hour buckets</p></div><div className="legend"><span><i className="legend-line" />History</span><span><i className="legend-dot" />Review flag</span></div></div>
                <div className="chart-controls"><label>Chart range <select value={rangeDays} onChange={event => setRangeDays(event.target.value)}><option value="all">All available history</option><option value="90">Last 90 days</option><option value="30">Last 30 days</option><option value="7">Last 7 days</option></select></label><span>Relative to the latest recorded bucket · values below refer to this range</span></div>
                <div className="metrics"><div><strong>{number(visiblePoints.length)}</strong><span>Recorded buckets</span></div><div><strong>{number(visibleMissing)}</strong><span>Missing within displayed span</span></div><div><strong>{number(flagged.length)}</strong><span>Provisional review flags</span></div><div><strong>{points.length ? sourceDate(points[points.length - 1].bucket_time_source) : '—'}</strong><span>Latest source bucket</span></div></div>
                <HistoryChart points={visiblePoints} />
                {points.length > 0 && <div className="latest"><strong>Latest recorded average:</strong> {number(points[points.length - 1].average_price)} silver per item <span>({number(points[points.length - 1].item_amount)} items in bucket)</span></div>}
                {flagged.length > 0 && <details className="flag-list"><summary>Review flagged observations ({flagged.length})</summary><div className="flag-rows">{flagged.slice(-20).reverse().map(point => <div key={point.bucket_time_source}><span>{sourceDate(point.bucket_time_source)}</span><strong>{number(point.average_price)} silver</strong><span>{point.review_flag.replace('_', ' ')}</span></div>)}</div>{flagged.length > 20 && <p>Showing the latest 20 flags.</p>}</details>}
                <div className="notice">Prices are calculated as silver_amount ÷ item_amount, matching the source history API. These are sell-order history statistics, not completed sales. Orange points are flagged when their price is less than half, or more than twice, both immediately adjacent six-hour prices. Flags prompt review; the original observations remain in the chart and database. Line breaks show missing buckets. Source timestamps have no timezone offset. No forecast is displayed yet.</div>
            </section>}
        </main>
        <footer>Source: Albion Online Data Project East database snapshot · <span>Independent personal analysis</span></footer>
    </div>;
}

createRoot(document.getElementById('app')).render(<App />);
