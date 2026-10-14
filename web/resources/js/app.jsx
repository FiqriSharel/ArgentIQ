import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';

const initialRequest = { items: 'T4_BAG,T5_BAG', cities: 'Bridgewatch,Martlock,Caerleon,Lymhurst,Thetford,Fort Sterling', quality: 1 };
const thresholds = { fresh: 60, aging: 360 }; // Provisional; see DATA_SOURCES.md.

function parseTime(value) {
    if (!value) return null;
    const date = new Date(/[Zz]|[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`);
    return Number.isNaN(date.getTime()) ? null : date;
}

function quoteState(price, timestamp, now) {
    if (price === null || timestamp === null) return { label: 'Unavailable', className: 'unavailable', age: null };
    const source = parseTime(timestamp);
    if (!source) return { label: 'Unavailable', className: 'unavailable', age: null };
    const age = Math.floor((now - source.getTime()) / 60000);
    if (age < -5) return { label: 'Clock anomaly', className: 'anomaly', age };
    if (age < thresholds.fresh) return { label: 'Fresh', className: 'fresh', age: Math.max(0, age) };
    if (age <= thresholds.aging) return { label: 'Aging', className: 'aging', age };
    return { label: 'Stale', className: 'stale', age };
}

function QuoteCell({ price, timestamp, now, onlyFresh }) {
    const state = quoteState(price, timestamp, now);
    const shownPrice = onlyFresh && state.className !== 'fresh' ? null : price;
    return <div>
        <div className={shownPrice === null ? 'price muted' : 'price'}>{shownPrice === null ? '—' : Number(shownPrice).toLocaleString()}</div>
        <div className="quote-meta">
            <span className={`status ${state.className}`}>{state.label}</span>
            {state.age !== null && <span>{state.age} min old</span>}
        </div>
        <div className="small">{timestamp ? `${timestamp.replace('T', ' ')} UTC*` : 'No observed quote'}</div>
    </div>;
}

function App() {
    const [data, setData] = useState({ rows: [], server: 'Asia' });
    const [request, setRequest] = useState(initialRequest);
    const [search, setSearch] = useState('');
    const [onlyFresh, setOnlyFresh] = useState(true);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const [evidence, setEvidence] = useState({});
    const [now, setNow] = useState(Date.now());

    async function load() {
        try {
            const response = await fetch('/market-data', { headers: { Accept: 'application/json' } });
            const body = await response.json();
            if (!response.ok) throw new Error(body.message || 'Could not load saved observations.');
            setData(body);
            setError('');
        } catch (err) { setError(err.message); }
    }

    useEffect(() => {
        load();
        const refreshTimer = setInterval(load, 60000); // Reads local SQLite only.
        const ageTimer = setInterval(() => setNow(Date.now()), 30000);
        return () => { clearInterval(refreshTimer); clearInterval(ageTimer); };
    }, []);

    async function refresh(event) {
        event.preventDefault();
        setBusy(true);
        setError('');
        try {
            const token = document.querySelector('meta[name="csrf-token"]').content;
            const response = await fetch('/refresh', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Accept: 'application/json', 'X-CSRF-TOKEN': token },
                body: JSON.stringify(request),
            });
            const body = await response.json();
            if (!response.ok) throw new Error(body.message || 'Refresh failed.');
            setData(body);
            setEvidence({});
            setNow(Date.now());
        } catch (err) { setError(err.message); }
        finally { setBusy(false); }
    }

    async function checkEvidence(row) {
        const key = `${row.item_id}-${row.city}-${row.quality}`;
        setEvidence(current => ({ ...current, [key]: { reason: 'Checking…' } }));
        try {
            const token = document.querySelector('meta[name="csrf-token"]').content;
            const response = await fetch('/evidence', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Accept: 'application/json', 'X-CSRF-TOKEN': token },
                body: JSON.stringify({ item_id: row.item_id, city: row.city, quality: row.quality }),
            });
            const body = await response.json();
            setEvidence(current => ({ ...current, [key]: response.ok ? body : { reason: body.message || 'Check failed.' } }));
        } catch (err) { setEvidence(current => ({ ...current, [key]: { reason: err.message } })); }
    }

    const rows = useMemo(() => data.rows.filter(row => {
        if (! `${row.item_id} ${row.city}`.toLowerCase().includes(search.toLowerCase())) return false;
        if (! onlyFresh) return true;
        return [quoteState(row.sell_price, row.sell_source_at, now), quoteState(row.buy_price, row.buy_source_at, now)]
            .some(state => state.className === 'fresh');
    }), [data.rows, search, onlyFresh, now]);
    const quoteStates = data.rows.flatMap(row => [quoteState(row.sell_price, row.sell_source_at, now), quoteState(row.buy_price, row.buy_source_at, now)]);
    const freshCount = quoteStates.filter(state => state.className === 'fresh').length;
    const unavailableCount = quoteStates.filter(state => state.className === 'unavailable').length;
    const staleCount = quoteStates.filter(state => ['stale', 'anomaly'].includes(state.className)).length;
    const latest = data.rows.map(row => parseTime(row.received_at)).filter(Boolean).sort((a, b) => b - a)[0];

    return <div className="shell">
        <header className="topbar"><div className="brand"><span className="brand-dot" />Argent<strong>IQ</strong></div><div className="top-meta"><span>PERSONAL MARKET WORKSPACE</span><span className="pill">● Asia server</span></div></header>
        <section className="hero"><div><p className="eyebrow">Market intelligence / local edition</p><h1>See the market clearly.</h1><p>Compare observed orders across cities. Every quote shows when AODP last saw it, so an old listing never masquerades as a current opportunity.</p></div><div className="hero-tag">Source: Albion Online Data Project · East</div></section>
        <section className="stats">
            <div className="stat"><div className="stat-label">Market combinations</div><div className="stat-value">{data.rows.length}</div><div className="stat-foot">Item · city · quality rows</div></div>
            <div className="stat"><div className="stat-label">Fresh quotes</div><div className="stat-value">{freshCount}</div><div className="stat-foot">Within provisional 60 min window</div></div>
            <div className="stat"><div className="stat-label">Stale quotes</div><div className="stat-value">{staleCount}</div><div className="stat-foot">Older than 6 hours or clock anomaly</div></div>
            <div className="stat"><div className="stat-label">Unavailable quotes</div><div className="stat-value">{unavailableCount}</div><div className="stat-foot">Missing, never treated as zero</div></div>
        </section>
        <main className="panel">
            <div className="panel-header"><div><h2 className="panel-title">City price comparison</h2><p className="panel-sub">Ask = lowest observed sell order · Bid = highest observed buy order</p></div>
                <form className="toolbar" onSubmit={refresh}>
                    <div className="field"><label htmlFor="items">Item IDs</label><input id="items" className="item-input" value={request.items} onChange={event => setRequest({ ...request, items: event.target.value.toUpperCase() })} required /></div>
                    <div className="field"><label htmlFor="cities">Cities</label><input id="cities" className="city-input" value={request.cities} onChange={event => setRequest({ ...request, cities: event.target.value })} required /></div>
                    <div className="field"><label htmlFor="quality">Quality</label><select id="quality" className="quality-input" value={request.quality} onChange={event => setRequest({ ...request, quality: Number(event.target.value) })}>{[1,2,3,4,5].map(q => <option key={q} value={q}>{q}</option>)}</select></div>
                    <button className="refresh" disabled={busy}>{busy ? 'Refreshing…' : '↻ Refresh prices'}</button>
                </form>
            </div>
            <div className="searchbar"><label htmlFor="search">Filter saved rows</label><input id="search" placeholder="Search item ID or city" value={search} onChange={event => setSearch(event.target.value)} /><label className="check"><input type="checkbox" checked={onlyFresh} onChange={event => setOnlyFresh(event.target.checked)} /> Last hour only</label></div>
            {error && <div className="error" role="alert">{error}</div>}
            {rows.length ? <div className="table-wrap"><table><thead><tr><th>Item</th><th>City</th><th>Quality</th><th>Ask / instant buy cost</th><th>Bid / instant sell quote</th><th>Retrieved</th><th>Java check</th></tr></thead><tbody>{rows.map(row => { const key = `${row.item_id}-${row.city}-${row.quality}`; return <tr key={key}><td className="item-code">{row.item_id}</td><td>{row.city}</td><td>{row.quality}</td><td><QuoteCell price={row.sell_price} timestamp={row.sell_source_at} now={now} onlyFresh={onlyFresh} /></td><td><QuoteCell price={row.buy_price} timestamp={row.buy_source_at} now={now} onlyFresh={onlyFresh} /></td><td><div>{parseTime(row.received_at)?.toLocaleString() || '—'}</div><div className="small">Local time</div></td><td><button className="secondary" onClick={() => checkEvidence(row)}>Check evidence</button>{evidence[key] && <div className="small">{evidence[key].reason}</div>}</td></tr>; })}</tbody></table></div> : <div className="empty">{data.rows.length ? (onlyFresh ? 'No quote under one hour is available in the saved data. Refresh, or contribute the needed market view with the AODP client while playing.' : 'No saved rows match this filter.') : 'No saved observations yet. Select items and refresh prices to begin.'}</div>}
            <div className="notice"><strong>Read this before acting:</strong> These are community-observed orders, not completed sales or guaranteed fills. A fresh page does not make an old source quote fresh. *AODP omits timezone offsets in price dates; quote ages provisionally assume UTC. Extreme prices may be misleading. The Java check only decides whether both quotes are present and recent; it does not calculate profit.</div>
        </main>
        <footer className="footer"><span>Last successful local collection: {latest ? latest.toLocaleString() : 'none yet'}</span><span>ArgentIQ is an independent, personal analysis tool · No automated trading</span></footer>
    </div>;
}

createRoot(document.getElementById('app')).render(<App />);
