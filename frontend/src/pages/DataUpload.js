import React, { useState, useEffect, useCallback } from 'react';
import { getTerritories } from '../services/api';
import axios from 'axios';

const API = 'http://localhost:8000';
const authHeaders = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` });

const INDICATOR_LABELS = {
    'PM2.5': 'PM2.5', 'PM10': 'PM10',
    'AQI': 'Індекс якості повітря', 'temperature': 'Температура',
    'humidity': 'Вологість', 'pressure': 'Тиск',
    'turbidity': 'Якість води', 'pH_water': 'pH води',
    'gdp': 'ВРП', 'salary': 'Зарплата', 'unemployment': 'Безробіття',
    'enterprises': 'Підприємства', 'healthcare': 'Охорона здоров\'я',
    'investments': 'Інвестиції', 'real_estate': 'Нерухомість',
};

const DataUpload = () => {
    const [territories, setTerritories] = useState([]);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [city, setCity] = useState('');
    const [ecoStats, setEcoStats] = useState([]);
    const [econStats, setEconStats] = useState([]);
    const [statsLoading, setStatsLoading] = useState(false);
    const [pendingFile, setPendingFile] = useState(null);
    const [popupTerritoryId, setPopupTerritoryId] = useState('');

    const loadStats = useCallback(async () => {
        setStatsLoading(true);
        try {
            const [eco, econ] = await Promise.all([
                axios.get(`${API}/ecological/stats/summary`, { headers: authHeaders() }),
                axios.get(`${API}/economic/stats/summary`, { headers: authHeaders() }),
            ]);
            setEcoStats(eco.data || []);
            setEconStats(econ.data || []);
        } catch (e) { console.error(e); }
        finally { setStatsLoading(false); }
    }, []);

    useEffect(() => {
        getTerritories().then(r => setTerritories(r.data));
        loadStats();
    }, [loadStats]);

    const showSuccess = (msg) => {
        setMessage(msg);
        loadStats();
        setTimeout(() => setMessage(''), 7000);
    };

    const doUpload = async (file, type, tid = null) => {
        const formData = new FormData();
        formData.append('file', file);
        const url = tid
            ? `${API}/${type}/upload/${tid}`
            : `${API}/${type}/upload-auto`;
        const res = await axios.post(url, formData, {
            headers: { ...authHeaders(), 'Content-Type': 'multipart/form-data' }
        });
        return res.data;
    };

    const handleFileChange = async (e, type) => {
        const file = e.target.files[0];
        if (!file) return;
        e.target.value = '';
        setLoading(true); setError('');
        try {
            const formData = new FormData();
            formData.append('file', file);
            const preview = await axios.post(
                `${API}/${type === 'ecological' ? 'ecological' : 'economic'}/preview-csv`,
                formData,
                { headers: { ...authHeaders(), 'Content-Type': 'multipart/form-data' } }
            );
            const cols = (preview.data.columns || []).map(c => c.toLowerCase());
            const hasRegion = cols.some(c =>
                ['region', 'регіон', 'область', 'attributes', 'territory'].includes(c)
            );
            if (hasRegion) {
                const res = await doUpload(file, type, null);
                showSuccess(`Завантажено ${res.imported} записів по регіонах (пропущено: ${res.skipped || 0})`);
            } else {
                setPendingFile({ file, type });
                setPopupTerritoryId('');
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Помилка завантаження');
        } finally { setLoading(false); }
    };

    const handlePopupConfirm = async () => {
        if (!popupTerritoryId || !pendingFile) return;
        setLoading(true); setError('');
        try {
            const res = await doUpload(pendingFile.file, pendingFile.type, popupTerritoryId);
            const tName = territories.find(t => t.id == popupTerritoryId)?.name;
            showSuccess(`Завантажено ${res.imported} записів для ${tName}`);
            setPendingFile(null);
        } catch (err) {
            setError(err.response?.data?.detail || 'Помилка завантаження');
        } finally { setLoading(false); }
    };

    const handleSaveEcoBot = async () => {
        if (!city.trim()) { setError('Введіть назву міста'); return; }
        setLoading(true); setError('');
        try {
            const res = await axios.post(
                `${API}/ecological/fetch-by-city?city=${encodeURIComponent(city.trim())}`,
                {},
                { headers: authHeaders() }
            );
            const data = res.data;
            if (data.success) {
                let note = '';
                if (data.used_nearest && data.nearest_city) {
                    note = ` (дані з найближчої станції: ${data.nearest_city})`;
                }
                showSuccess(
                    `Завантажено ${data.imported} записів для ${city}${note}. ` +
                    `Оновлено міст: ${data.territories_updated || 1}`
                );
                getTerritories().then(r => setTerritories(r.data));
            } else {
                setError(data.error || 'Не вдалось завантажити дані');
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Помилка SaveEcoBot');
        } finally { setLoading(false); }
    };

    const handleDeleteData = async (territoryId, indicator, type) => {
        const label = INDICATOR_LABELS[indicator] || indicator;
        if (!window.confirm(`Видалити всі дані "${label}" для цієї території?`)) return;
        try {
            const res = await axios.delete(
                `${API}/${type}/stats/${territoryId}?indicator=${encodeURIComponent(indicator)}`,
                { headers: authHeaders() }
            );
            showSuccess(`Видалено ${res.data.deleted} записів`);
        } catch (err) {
            setError('Помилка видалення даних');
        }
    };

    const groupByTerritory = (stats) => {
        const grouped = {};
        stats.forEach(row => {
            if (!grouped[row.territory]) grouped[row.territory] = [];
            grouped[row.territory].push(row);
        });
        return grouped;
    };

    const ecoGrouped = groupByTerritory(ecoStats);
    const econGrouped = groupByTerritory(econStats);

    return (
        <div style={s.container}>
            <h1 style={s.title}>Завантаження даних</h1>

            {message && <div style={s.success}>{message}</div>}
            {error && <div style={s.error} onClick={() => setError('')}>{error}</div>}

            {pendingFile && (
                <div style={s.overlay}>
                    <div style={s.popup}>
                        <h3 style={s.popupTitle}>Оберіть територію</h3>
                        <p style={s.popupText}>
                            У файлі <b>{pendingFile.file.name}</b> не знайдено колонку з регіоном.
                            До якої території прив'язати ці дані?
                        </p>
                        <select
                            value={popupTerritoryId}
                            onChange={e => setPopupTerritoryId(e.target.value)}
                            style={s.popupSelect}
                        >
                            <option value="">-- Оберіть територію --</option>
                            {territories.map(t => (
                                <option key={t.id} value={t.id}>{t.name}</option>
                            ))}
                        </select>
                        <div style={s.popupButtons}>
                            <button
                                onClick={handlePopupConfirm}
                                style={s.popupConfirm}
                                disabled={!popupTerritoryId || loading}
                            >
                                {loading ? '...' : 'Завантажити'}
                            </button>
                            <button onClick={() => setPendingFile(null)} style={s.popupCancel}>
                                Скасувати
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div style={s.grid}>
                <div style={s.card}>
                    <h3 style={s.cardTitle}>Екологічні дані (CSV)</h3>
                    <p style={s.cardHint}>Якість води, PM2.5, PM10, індекс якості повітря, температура, вологість, тиск</p>
                    <label style={{ ...s.fileBtn, opacity: loading ? 0.6 : 1 }}>
                        {loading ? 'Завантаження...' : 'Вибрати CSV'}
                        <input type="file" accept=".csv"
                            onChange={e => handleFileChange(e, 'ecological')}
                            style={{ display: 'none' }} disabled={loading} />
                    </label>
                </div>

                <div style={s.card}>
                    <h3 style={s.cardTitle}>Економічні дані (CSV)</h3>
                    <p style={s.cardHint}>ВРП, зарплата, безробіття, підприємства, охорона здоров'я, інвестиції</p>
                    <label style={{ ...s.fileBtn, opacity: loading ? 0.6 : 1 }}>
                        {loading ? 'Завантаження...' : 'Вибрати CSV'}
                        <input type="file" accept=".csv"
                            onChange={e => handleFileChange(e, 'economic')}
                            style={{ display: 'none' }} disabled={loading} />
                    </label>
                </div>

                <div style={s.card}>
                    <h3 style={s.cardTitle}>SaveEcoBot API</h3>
                    <p style={s.cardHint}>Якість повітря: PM2.5, PM10, AQI, температура, вологість, тиск</p>
                    <p style={s.cardHint}>
                        Введіть будь-яке місто України. Якщо станції немає — система знайде
                        найближчу і запише дані до всіх міст цієї області.
                    </p>
                    <input
                        type="text"
                        placeholder="Назва міста (Чернігів, Тростянець, Жашків...)"
                        value={city}
                        onChange={e => setCity(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && handleSaveEcoBot()}
                        style={s.input}
                    />
                    <button
                        onClick={handleSaveEcoBot}
                        style={s.btn}
                        disabled={!city.trim() || loading}
                    >
                        {loading ? 'Завантаження...' : 'Завантажити дані'}
                    </button>
                </div>
            </div>

            <div style={s.statsBox}>
                <div style={s.statsHeader}>
                    <h2 style={s.sectionTitle}>Дані в базі</h2>
                    <button onClick={loadStats} style={s.refreshBtn} disabled={statsLoading}>
                        {statsLoading ? '...' : 'Оновити'}
                    </button>
                </div>
                <div style={s.totals}>
                    {[
                        { num: ecoStats.reduce((acc, r) => acc + r.count, 0).toLocaleString(), label: 'Екологічних' },
                        { num: econStats.reduce((acc, r) => acc + r.count, 0).toLocaleString(), label: 'Економічних' },
                        { num: Object.keys({ ...ecoGrouped, ...econGrouped }).length, label: 'Регіонів' },
                    ].map((item, i) => (
                        <div key={i} style={s.totalCard}>
                            <div style={s.totalNum}>{item.num}</div>
                            <div style={s.totalLabel}>{item.label}</div>
                        </div>
                    ))}
                </div>
                <div style={s.statsGrid}>
                    {[
                        { title: 'Екологічні', grouped: ecoGrouped, dateKey: 'last_date', type: 'ecological' },
                        { title: 'Економічні', grouped: econGrouped, dateKey: 'last_period', type: 'economic' },
                    ].map(({ title, grouped, dateKey, type }) => (
                        <div key={title}>
                            <h3 style={s.statsTitle}>{title}</h3>
                            {Object.keys(grouped).length === 0
                                ? <p style={s.noData}>Даних ще немає</p>
                                : Object.entries(grouped).map(([territory, rows]) => (
                                    <div key={territory} style={s.territoryBlock}>
                                        <div style={s.territoryName}>{territory}</div>
                                        <div style={s.indicatorList}>
                                            {rows.map(row => (
                                                <div key={row.indicator} style={s.indicatorRow}>
                                                    <span style={s.indName}>
                                                        {INDICATOR_LABELS[row.indicator] || row.indicator}
                                                    </span>
                                                    <span style={s.indCount}>{row.count.toLocaleString()}</span>
                                                    {row[dateKey] && <span style={s.indDate}>{row[dateKey]}</span>}
                                                    <button
                                                        style={s.deleteBtn}
                                                        title="Видалити ці дані"
                                                        onClick={() => handleDeleteData(row.territory_id, row.indicator, type)}
                                                    >
                                                        x
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ))
                            }
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

const s = {
    container: { padding: '24px', maxWidth: '1200px', margin: '0 auto' },
    title: { color: '#2c5f2e', fontSize: '28px', marginBottom: '20px' },
    success: { background: '#e8f5e9', color: '#2c5f2e', padding: '12px 16px', borderRadius: '6px', marginBottom: '16px' },
    error: { background: '#ffe0e0', color: '#cc0000', padding: '12px 16px', borderRadius: '6px', marginBottom: '16px', cursor: 'pointer' },
    grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px', marginBottom: '32px' },
    card: { background: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', borderTop: '4px solid #2c5f2e' },
    cardTitle: { color: '#2c5f2e', marginBottom: '8px', fontSize: '15px' },
    cardHint: { color: '#888', fontSize: '12px', marginBottom: '6px' },
    fileBtn: { display: 'block', marginTop: '12px', padding: '10px', background: '#2c5f2e', color: 'white', borderRadius: '6px', cursor: 'pointer', fontSize: '14px', textAlign: 'center' },
    input: { width: '100%', padding: '8px 10px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '14px', marginBottom: '8px', boxSizing: 'border-box' },
    btn: { width: '100%', padding: '10px', background: '#2c5f2e', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '14px' },
    overlay: { position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 },
    popup: { background: 'white', padding: '32px', borderRadius: '12px', width: '420px', boxShadow: '0 20px 60px rgba(0,0,0,0.3)' },
    popupTitle: { color: '#2c5f2e', marginBottom: '12px', fontSize: '18px' },
    popupText: { color: '#555', fontSize: '14px', marginBottom: '16px', lineHeight: '1.6' },
    popupSelect: { width: '100%', padding: '10px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '14px', boxSizing: 'border-box' },
    popupButtons: { display: 'flex', gap: '10px', marginTop: '16px' },
    popupConfirm: { flex: 1, padding: '10px', background: '#2c5f2e', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '14px' },
    popupCancel: { padding: '10px 20px', background: '#eee', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '14px' },
    statsBox: { background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' },
    statsHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' },
    sectionTitle: { color: '#333', fontSize: '18px', margin: 0 },
    refreshBtn: { padding: '6px 16px', background: '#f0f0f0', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '13px' },
    totals: { display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' },
    totalCard: { background: '#f0f7f0', padding: '16px 28px', borderRadius: '8px', textAlign: 'center', borderTop: '3px solid #2c5f2e', minWidth: '130px' },
    totalNum: { fontSize: '28px', fontWeight: 'bold', color: '#2c5f2e' },
    totalLabel: { color: '#666', fontSize: '12px', marginTop: '4px' },
    statsGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' },
    statsTitle: { color: '#2c5f2e', marginBottom: '12px', fontSize: '15px' },
    noData: { color: '#999', fontSize: '13px', fontStyle: 'italic' },
    territoryBlock: { marginBottom: '12px', border: '1px solid #eee', borderRadius: '6px', overflow: 'hidden' },
    territoryName: { background: '#f0f7f0', padding: '7px 12px', fontWeight: 'bold', fontSize: '13px', color: '#2c5f2e' },
    indicatorList: { padding: '6px 12px' },
    indicatorRow: { display: 'flex', alignItems: 'center', gap: '8px', padding: '3px 0', borderBottom: '1px solid #f5f5f5', fontSize: '13px' },
    indName: { flex: 1, color: '#333' },
    indCount: { background: '#2c5f2e', color: 'white', padding: '1px 8px', borderRadius: '10px', fontSize: '12px' },
    indDate: { color: '#999', fontSize: '11px' },
    deleteBtn: { background: 'none', border: 'none', color: '#cc0000', cursor: 'pointer', fontSize: '14px', fontWeight: 'bold', padding: '0 4px', lineHeight: 1 },
};

export default DataUpload;