import React, { useState, useEffect } from 'react';
import { getTerritories, generateReport } from '../services/api';

const ECO_INDICATORS = ['turbidity', 'PM2.5', 'PM10', 'AQI', 'temperature', 'humidity', 'pressure'];
const ECON_INDICATORS = ['gdp', 'salary', 'unemployment', 'enterprises', 'healthcare', 'investments'];

const INDICATOR_LABELS = {
    turbidity: 'Якість води',
    'PM2.5': 'PM2.5',
    PM10: 'PM10',
    AQI: 'Індекс якості повітря',
    temperature: 'Температура',
    humidity: 'Вологість',
    pressure: 'Тиск',
    gdp: 'ВРП',
    salary: 'Зарплата',
    unemployment: 'Безробіття',
    enterprises: 'Підприємства',
    healthcare: 'Охорона здоров’я',
    investments: 'Інвестиції',
};

const Reports = () => {
    const [territories, setTerritories] = useState([]);
    const [territoryId, setTerritoryId] = useState('');
    const [ecoIndicator, setEcoIndicator] = useState('turbidity');
    const [econIndicator, setEconIndicator] = useState('gdp');
    const [multipleEcoIndicators, setMultipleEcoIndicators] = useState(['PM2.5', 'PM10']);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
        getTerritories().then(r => setTerritories(r.data)).catch(() => setTerritories([]));
    }, []);

    const toggleMultipleIndicator = (indicator) => {
        setMultipleEcoIndicators(prev =>
            prev.includes(indicator)
                ? prev.filter(item => item !== indicator)
                : [...prev, indicator]
        );
    };

    const handleGenerate = async () => {
        if (!territoryId) {
            setError('Оберіть територію');
            return;
        }
        if (multipleEcoIndicators.length < 2) {
            setError('Оберіть мінімум 2 екологічні показники для множинної регресії');
            return;
        }

        setLoading(true);
        setError('');
        setSuccess('');

        try {
            const response = await generateReport({
                territory_id: parseInt(territoryId),
                eco_indicator: ecoIndicator,
                econ_indicator: econIndicator,
                multiple_eco_indicators: multipleEcoIndicators,
                include_regression: true,
                include_timeseries: true,
                include_partial: true,
                include_multiple_regression: true,
                include_comparison: true,
            });

            const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `report_${ecoIndicator}_${econIndicator}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
            setSuccess('PDF звіт успішно згенеровано і завантажено');
        } catch (err) {
            setError(err.response?.data?.detail || 'Помилка генерації звіту');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={styles.container}>
            <h1 style={styles.title}>Генерація PDF звітів</h1>

            {error && <div style={styles.error}>{error}</div>}
            {success && <div style={styles.success}>{success}</div>}

            <div style={styles.card}>
                <h2 style={styles.cardTitle}>Налаштування звіту</h2>

                <div style={styles.grid}>
                    <div style={styles.field}>
                        <label style={styles.label}>Територія</label>
                        <select value={territoryId} onChange={e => setTerritoryId(e.target.value)} style={styles.select}>
                            <option value="">Оберіть територію</option>
                            {territories.map(t => (
                                <option key={t.id} value={t.id}>{t.name}</option>
                            ))}
                        </select>
                    </div>

                    <div style={styles.field}>
                        <label style={styles.label}>Екологічний показник для основного аналізу</label>
                        <select value={ecoIndicator} onChange={e => setEcoIndicator(e.target.value)} style={styles.select}>
                            {ECO_INDICATORS.map(i => (
                                <option key={i} value={i}>{INDICATOR_LABELS[i]}</option>
                            ))}
                        </select>
                    </div>

                    <div style={styles.field}>
                        <label style={styles.label}>Економічний показник</label>
                        <select value={econIndicator} onChange={e => setEconIndicator(e.target.value)} style={styles.select}>
                            {ECON_INDICATORS.map(i => (
                                <option key={i} value={i}>{INDICATOR_LABELS[i]}</option>
                            ))}
                        </select>
                    </div>
                </div>

                <div style={styles.multiBox}>
                    <label style={styles.label}>Екологічні показники для множинної регресії</label>
                    <div style={styles.checkboxGrid}>
                        {ECO_INDICATORS.map(i => (
                            <label key={i} style={styles.checkbox}>
                                <input
                                    type="checkbox"
                                    checked={multipleEcoIndicators.includes(i)}
                                    onChange={() => toggleMultipleIndicator(i)}
                                />
                                <span>{INDICATOR_LABELS[i]}</span>
                            </label>
                        ))}
                    </div>
                </div>

                <div style={styles.info}>
                    <h3 style={styles.infoTitle}>Що буде в звіті:</h3>
                    <ul style={styles.infoList}>
                        <li>Інформація про територію та вибрані показники</li>
                        <li>Кореляція Пірсона, Спірмена і Кендалла</li>
                        <li>Часткова кореляція з контрольною змінною</li>
                        <li>Аналіз часових рядів: крос-кореляція і ковзна кореляція</li>
                        <li>Лінійна регресія з рівнянням, R², p-value і залишками</li>
                        <li>Множинна регресія з коефіцієнтами, R² і VIF</li>
                        <li>Порівняння методів, узгодженість, суперечності і ranking</li>
                    </ul>
                </div>

                <button onClick={handleGenerate} style={styles.button} disabled={loading || !territoryId}>
                    {loading ? 'Генерація...' : 'Згенерувати PDF звіт'}
                </button>
            </div>
        </div>
    );
};

const styles = {
    container: { padding: '24px', maxWidth: '900px', margin: '0 auto' },
    title: { color: '#2c5f2e', fontSize: '28px', marginBottom: '24px' },
    error: { background: '#ffe0e0', color: '#cc0000', padding: '12px', borderRadius: '6px', marginBottom: '16px' },
    success: { background: '#e8f5e9', color: '#2c5f2e', padding: '12px', borderRadius: '6px', marginBottom: '16px' },
    card: { background: 'white', padding: '32px', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' },
    cardTitle: { color: '#333', marginBottom: '24px' },
    grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '20px' },
    field: {},
    label: { display: 'block', marginBottom: '6px', fontSize: '13px', color: '#555', fontWeight: 'bold' },
    select: { width: '100%', padding: '8px 10px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '14px' },
    multiBox: { marginBottom: '24px' },
    checkboxGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '8px', border: '1px solid #ddd', borderRadius: '6px', padding: '12px' },
    checkbox: { display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', color: '#333' },
    info: { background: '#f0f7f0', padding: '16px', borderRadius: '6px', marginBottom: '24px' },
    infoTitle: { color: '#2c5f2e', marginBottom: '8px', fontSize: '15px' },
    infoList: { margin: 0, paddingLeft: '20px', color: '#555', fontSize: '14px', lineHeight: '1.8' },
    button: { width: '100%', padding: '14px', background: '#2c5f2e', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '16px', fontWeight: 'bold' },
};

export default Reports;