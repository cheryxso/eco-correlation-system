import React, { useState, useEffect } from 'react';
import { getTerritories, runCorrelation, runPartialCorrelation, runTimeSeries, runRegression, runComparison } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, ScatterChart, Scatter, ReferenceLine } from 'recharts';
import axios from 'axios';

const API = 'http://localhost:8000';

const ECO_INDICATORS = ['turbidity', 'PM2.5', 'PM10', 'AQI', 'temperature', 'humidity', 'pressure'];
const ECON_INDICATORS = ['gdp', 'salary', 'unemployment', 'enterprises', 'healthcare', 'investments'];

const INDICATOR_LABELS = {
    'turbidity': 'Якість води',
    'PM2.5': 'PM2.5',
    'PM10': 'PM10',
    'AQI': 'Індекс якості повітря',
    'temperature': 'Температура',
    'humidity': 'Вологість',
    'pressure': 'Тиск',
    'gdp': 'ВРП',
    'salary': 'Зарплата',
    'unemployment': 'Безробіття',
    'enterprises': 'Підприємства',
    'healthcare': 'Охорона здоров\'я',
    'investments': 'Інвестиції',
};

const ECO_AVAILABILITY = {
    'turbidity': 'Дані по водним ресурсам є не для всіх міст — лише для річкових постів моніторингу. Якщо для обраного міста даних немає, система використає найближчий регіон.',
    'PM2.5': 'Дані з SaveEcoBot. Є не для всіх міст — для відсутніх використовується найближча станція моніторингу.',
    'PM10': 'Дані з SaveEcoBot. Є не для всіх міст — для відсутніх використовується найближча станція моніторингу.',
    'AQI': 'Дані з SaveEcoBot. Є не для всіх міст — для відсутніх використовується найближча станція моніторингу.',
    'temperature': null,
    'humidity': null,
    'pressure': null,
};

const ECON_AVAILABILITY = {
    'gdp': null,
    'salary': null,
    'unemployment': null,
    'enterprises': null,
    'healthcare': 'Дані по Україні в цілому розподілені рівномірно між регіонами. Є для всіх 25 регіонів, роки 2017-2020.',
    'investments': 'Квартальні дані з 2015 по 2024. Є для всіх 25 регіонів.',
};

const Analysis = () => {
    const [territories, setTerritories] = useState([]);
    const [territoryId, setTerritoryId] = useState('');
    const [ecoIndicator, setEcoIndicator] = useState('turbidity');
    const [econIndicator, setEconIndicator] = useState('unemployment');
    const [controlIndicator, setControlIndicator] = useState('PM10');
    const [multipleEcoIndicators, setMultipleEcoIndicators] = useState([]);
    const [method, setMethod] = useState('correlation');
    const [results, setResults] = useState(null);
    const [matrix, setMatrix] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        getTerritories().then(r => setTerritories(r.data));
    }, []);

    const handleAnalysis = async () => {
        if (!territoryId) { setError('Оберіть територію'); return; }
        setLoading(true); setError(''); setResults(null); setMatrix(null);
        try {
            let response;
            const base = {
                territory_id: parseInt(territoryId),
                eco_indicator: ecoIndicator,
                econ_indicator: econIndicator,
            };
            if (method === 'correlation') {
                response = await runCorrelation({ ...base, apply_bonferroni: true });
            } else if (method === 'partial') {
                response = await runPartialCorrelation({ ...base, control_eco_indicator: controlIndicator });
            } else if (method === 'timeseries') {
                response = await runTimeSeries({ ...base, max_lag: 6, window: 3 });
            } else if (method === 'regression') {
                response = await runRegression(base);
            } else if (method === 'regression_multiple') {
                if (multipleEcoIndicators.length < 2) {
                    setError('Оберіть мінімум 2 екологічних показники для множинної регресії');
                    setLoading(false);
                    return;
                }
                response = await axios.post(
                    `${API}/analysis/regression/multiple`,
                    {
                        territory_id: parseInt(territoryId),
                        eco_indicators: multipleEcoIndicators,
                        econ_indicator: econIndicator,
                    },
                    { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
                );
            } else if (method === 'comparison') {
                response = await runComparison(base);
            }
            setResults(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Помилка аналізу');
        } finally { setLoading(false); }
    };

    const handleMatrix = async () => {
        if (!territoryId) { setError('Оберіть територію'); return; }
        setLoading(true); setError(''); setResults(null); setMatrix(null);
        try {
            const res = await axios.post(
                `${API}/analysis/correlation-matrix?territory_id=${territoryId}`,
                {},
                { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
            );
            setMatrix(res.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Помилка матриці');
        } finally { setLoading(false); }
    };

    const toggleMultipleEco = (indicator) => {
        setMultipleEcoIndicators(prev =>
            prev.includes(indicator)
                ? prev.filter(i => i !== indicator)
                : [...prev, indicator]
        );
    };

    const renderCorrelationChart = (results) => {
        if (!results?.results) return null;
        const data = [
            { method: 'Пірсон', coefficient: Math.abs(results.results.pearson?.coefficient || 0) },
            { method: 'Спірмен', coefficient: Math.abs(results.results.spearman?.coefficient || 0) },
            { method: 'Кендалл', coefficient: Math.abs(results.results.kendall?.coefficient || 0) },
        ];
        return (
            <ResponsiveContainer width="100%" height={250}>
                <BarChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="method" />
                    <YAxis domain={[0, 1]} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="coefficient" fill="#2c5f2e" name="Коефіцієнт" />
                </BarChart>
            </ResponsiveContainer>
        );
    };

    const renderRegressionCharts = (result) => {
        if (!result || !result.residuals) return null;

        const scatterData = result.scatter_data || [];
        const residualData = result.residuals.map((r, i) => ({
            index: i,
            residual: r,
            predicted: result.predicted ? result.predicted[i] : i,
        }));

        return (
            <>
                {scatterData.length > 0 && (
                    <div style={{marginTop:'24px'}}>
                        <h3 style={{color:'#2c5f2e', marginBottom:'8px', fontSize:'15px'}}>
                            Scatter plot з лінією регресії
                        </h3>
                        <p style={{color:'#888', fontSize:'12px', marginBottom:'12px'}}>
                            Крапки — реальні дані, лінія — передбачення моделі.
                        </p>
                        <ResponsiveContainer width="100%" height={280}>
                            <ScatterChart margin={{top:10, right:20, left:0, bottom:10}}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="x" name={INDICATOR_LABELS[ecoIndicator] || ecoIndicator} type="number" />
                                <YAxis dataKey="y" name={INDICATOR_LABELS[econIndicator] || econIndicator} type="number" />
                                <Tooltip cursor={{strokeDasharray:'3 3'}} />
                                <Scatter data={scatterData.filter(d => d.type === 'actual')} fill="#2c5f2e" name="Реальні дані" />
                                <Scatter data={scatterData.filter(d => d.type === 'regression')} fill="#cc0000" line shape="cross" name="Лінія регресії" />
                            </ScatterChart>
                        </ResponsiveContainer>
                    </div>
                )}

                <div style={{marginTop:'24px'}}>
                    <h3 style={{color:'#2c5f2e', marginBottom:'8px', fontSize:'15px'}}>
                        Графік залишків
                    </h3>
                    <p style={{color:'#888', fontSize:'12px', marginBottom:'12px'}}>
                        Залишки — різниця між реальними і передбаченими значеннями. Ідеально — хаотичне розсіювання навколо нуля.
                    </p>
                    <ResponsiveContainer width="100%" height={250}>
                        <ScatterChart margin={{top:10, right:20, left:0, bottom:10}}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="predicted" name="Передбачене значення" type="number" />
                            <YAxis dataKey="residual" name="Залишок" type="number" />
                            <ReferenceLine y={0} stroke="#cc0000" strokeDasharray="4 4" />
                            <Tooltip cursor={{strokeDasharray:'3 3'}} />
                            <Scatter data={residualData} fill="#2c5f2e" name="Залишки" />
                        </ScatterChart>
                    </ResponsiveContainer>
                </div>
            </>
        );
    };

    const getCellColor = (value) => {
        if (value === null || value === undefined) return '#fff';
        const abs = Math.abs(value);
        if (abs >= 0.7) return value > 0 ? '#c8e6c9' : '#ffcdd2';
        if (abs >= 0.5) return value > 0 ? '#dcedc8' : '#ffe0b2';
        if (abs >= 0.3) return value > 0 ? '#f1f8e9' : '#fff3e0';
        return '#fff';
    };

    const ecoWarning = ECO_AVAILABILITY[ecoIndicator];
    const econWarning = ECON_AVAILABILITY[econIndicator];

    return (
        <div style={s.container}>
            <h1 style={s.title}>Кореляційний аналіз</h1>

            {error && <div style={s.error} onClick={() => setError('')}>{error}</div>}

            {(ecoWarning || econWarning) && (
                <div style={s.warningBox}>
                    <b>Увага щодо наявності даних:</b>
                    {ecoWarning && (
                        <div style={{marginTop:'6px'}}>
                            <b>{INDICATOR_LABELS[ecoIndicator]}:</b> {ecoWarning}
                        </div>
                    )}
                    {econWarning && (
                        <div style={{marginTop:'6px'}}>
                            <b>{INDICATOR_LABELS[econIndicator]}:</b> {econWarning}
                        </div>
                    )}
                </div>
            )}

            <div style={s.controls}>
                <div style={s.field}>
                    <label style={s.label}>Територія</label>
                    <select value={territoryId} onChange={e => setTerritoryId(e.target.value)} style={s.select}>
                        <option value="">-- Оберіть --</option>
                        {territories.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                    </select>
                </div>
                <div style={s.field}>
                    <label style={s.label}>Метод аналізу</label>
                    <select value={method} onChange={e => setMethod(e.target.value)} style={s.select}>
                        <option value="correlation">Кореляція (Пірсон/Спірмен/Кендалл)</option>
                        <option value="partial">Часткова кореляція</option>
                        <option value="timeseries">Аналіз часових рядів</option>
                        <option value="regression">Регресійний аналіз (лінійна)</option>
                        <option value="regression_multiple">Множинна регресія</option>
                        <option value="comparison">Порівняння методів</option>
                    </select>
                </div>

                {method !== 'regression_multiple' && (
                    <div style={s.field}>
                        <label style={s.label}>Екологічний показник</label>
                        <select value={ecoIndicator} onChange={e => setEcoIndicator(e.target.value)} style={s.select}>
                            {ECO_INDICATORS.map(i => (
                                <option key={i} value={i}>
                                    {INDICATOR_LABELS[i] || i}{ECO_AVAILABILITY[i] ? ' *' : ''}
                                </option>
                            ))}
                        </select>
                    </div>
                )}

                {method === 'regression_multiple' && (
                    <div style={s.field}>
                        <label style={s.label}>Еко показники (мін. 2)</label>
                        <div style={s.checkboxGroup}>
                            {ECO_INDICATORS.map(i => (
                                <label key={i} style={s.checkboxLabel}>
                                    <input
                                        type="checkbox"
                                        checked={multipleEcoIndicators.includes(i)}
                                        onChange={() => toggleMultipleEco(i)}
                                        style={{marginRight:'6px'}}
                                    />
                                    {INDICATOR_LABELS[i] || i}
                                </label>
                            ))}
                        </div>
                    </div>
                )}

                <div style={s.field}>
                    <label style={s.label}>Економічний показник</label>
                    <select value={econIndicator} onChange={e => setEconIndicator(e.target.value)} style={s.select}>
                        {ECON_INDICATORS.map(i => (
                            <option key={i} value={i}>
                                {INDICATOR_LABELS[i] || i}{ECON_AVAILABILITY[i] ? ' *' : ''}
                            </option>
                        ))}
                    </select>
                </div>

                {method === 'partial' && (
                    <div style={s.field}>
                        <label style={s.label}>Контрольна змінна</label>
                        <select value={controlIndicator} onChange={e => setControlIndicator(e.target.value)} style={s.select}>
                            {ECO_INDICATORS.map(i => (
                                <option key={i} value={i}>{INDICATOR_LABELS[i] || i}</option>
                            ))}
                        </select>
                    </div>
                )}

                <div style={{display:'flex', gap:'8px', alignItems:'flex-end'}}>
                    <button onClick={handleAnalysis} style={s.button} disabled={loading}>
                        {loading ? 'Аналіз...' : 'Запустити аналіз'}
                    </button>
                    <button onClick={handleMatrix} style={s.btnMatrix} disabled={loading}>
                        {loading ? '...' : 'Кореляційна матриця'}
                    </button>
                </div>
            </div>

            {results && (
                <div style={s.results}>
                    <h2 style={s.resultsTitle}>Результати аналізу</h2>
                    <p style={s.meta}>
                        Територія ID: {results.territory_id} |
                        Показники: {results.eco_indicator ? (INDICATOR_LABELS[results.eco_indicator] || results.eco_indicator) : (results.eco_indicators || []).map(i => INDICATOR_LABELS[i] || i).join(', ')} → {INDICATOR_LABELS[results.econ_indicator] || results.econ_indicator} |
                        Спостережень: {results.n_observations}
                    </p>

                    {method === 'correlation' && results.results && (
                        <>
                            {results.results.preparation && (
                                <div style={s.prepBox}>
                                    <b>Підготовка даних:</b>
                                    <span style={{marginLeft:'12px'}}>
                                        Спостережень: {results.results.preparation.original_length}
                                    </span>
                                    {results.results.preparation.x_missing_interpolated > 0 && (
                                        <span style={{marginLeft:'12px', color:'#e65100'}}>
                                            Пропуски (еко): {results.results.preparation.x_missing_interpolated} — заповнено інтерполяцією
                                        </span>
                                    )}
                                    {results.results.preparation.y_missing_interpolated > 0 && (
                                        <span style={{marginLeft:'12px', color:'#e65100'}}>
                                            Пропуски (екон): {results.results.preparation.y_missing_interpolated} — заповнено інтерполяцією
                                        </span>
                                    )}
                                    {results.results.preparation.x_outliers_replaced > 0 && (
                                        <span style={{marginLeft:'12px', color:'#b71c1c'}}>
                                            Викиди IQR (еко): {results.results.preparation.x_outliers_replaced} — замінено медіаною
                                        </span>
                                    )}
                                    {results.results.preparation.y_outliers_replaced > 0 && (
                                        <span style={{marginLeft:'12px', color:'#b71c1c'}}>
                                            Викиди IQR (екон): {results.results.preparation.y_outliers_replaced} — замінено медіаною
                                        </span>
                                    )}
                                    {results.results.preparation.x_missing_interpolated === 0 &&
                                     results.results.preparation.y_missing_interpolated === 0 &&
                                     results.results.preparation.x_outliers_replaced === 0 &&
                                     results.results.preparation.y_outliers_replaced === 0 && (
                                        <span style={{marginLeft:'12px', color:'#2c5f2e'}}>
                                            Пропуски та викиди не виявлені
                                        </span>
                                    )}
                                </div>
                            )}
                            {results.results.normality_check && (
                                <div style={s.normalityBox}>
                                    <b>Тест Шапіро-Вілка (нормальність розподілу):</b>
                                    <span style={{marginLeft:'12px'}}>
                                        Еко: {results.results.normality_check.eco_indicator?.note} (p={results.results.normality_check.eco_indicator?.p_value})
                                    </span>
                                    <span style={{marginLeft:'12px'}}>
                                        Екон: {results.results.normality_check.econ_indicator?.note} (p={results.results.normality_check.econ_indicator?.p_value})
                                    </span>
                                    <div style={{marginTop:'6px', color:'#2c5f2e', fontWeight:'bold'}}>
                                        {results.results.normality_check.recommendation}
                                    </div>
                                </div>
                            )}
                            {renderCorrelationChart(results)}
                            <table style={s.table}>
                                <thead>
                                    <tr style={s.thead}>
                                        <th style={s.th}>Метод</th>
                                        <th style={s.th}>Коефіцієнт</th>
                                        <th style={s.th}>p-value</th>
                                        <th style={s.th}>Значущість</th>
                                        <th style={s.th}>Інтерпретація</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {['pearson', 'spearman', 'kendall'].map(m => (
                                        <tr key={m} style={s.tr}>
                                            <td style={s.td}>{m === 'pearson' ? 'Пірсон' : m === 'spearman' ? 'Спірмен' : 'Кендалл'}</td>
                                            <td style={s.td}>{results.results[m]?.coefficient}</td>
                                            <td style={s.td}>{results.results[m]?.p_value}</td>
                                            <td style={{...s.td, color: results.results[m]?.is_significant ? 'green' : 'red'}}>
                                                {results.results[m]?.is_significant ? 'Так' : 'Ні'}
                                            </td>
                                            <td style={s.td}>{results.results[m]?.interpretation}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </>
                    )}

                    {method === 'partial' && results.result && (
                        <div style={s.resultCard}>
                            <p><b>Метод:</b> Часткова кореляція</p>
                            <p><b>Коефіцієнт:</b> {results.result.coefficient}</p>
                            <p><b>p-value:</b> {results.result.p_value}</p>
                            <p><b>Значущість:</b> {results.result.is_significant ? 'Так' : 'Ні'}</p>
                            <p><b>Контрольна змінна:</b> {results.result.controlled_variable}</p>
                            <p><b>Інтерпретація:</b> {results.result.interpretation}</p>
                        </div>
                    )}

                    {method === 'timeseries' && (
                        <>
                            <div style={s.resultCard}>
                                <p><b>Оптимальний лаг:</b> {results.cross_correlation?.optimal_lag}</p>
                                <p><b>Крос-кореляція:</b> {results.cross_correlation?.interpretation}</p>
                                <p><b>Ковзна кореляція:</b> {results.rolling_correlation?.interpretation}</p>
                            </div>

                            {results.cross_correlation?.correlations_by_lag?.length > 0 && (
                                <div style={{marginTop:'24px'}}>
                                    <h3 style={{color:'#2c5f2e', marginBottom:'8px', fontSize:'15px'}}>
                                        Крос-кореляційна функція (CCF)
                                    </h3>
                                    <p style={{color:'#888', fontSize:'12px', marginBottom:'12px'}}>
                                        Показує силу зв'язку при різних часових зсувах. Негативний лаг — еко показник відстає, позитивний — випереджає.
                                    </p>
                                    <ResponsiveContainer width="100%" height={280}>
                                        <BarChart data={results.cross_correlation.correlations_by_lag} margin={{top:10, right:20, left:0, bottom:10}}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="lag" label={{value:'Лаг', position:'insideBottom', offset:-5}} />
                                            <YAxis domain={[-1, 1]} label={{value:'Кореляція', angle:-90, position:'insideLeft'}} />
                                            <Tooltip formatter={(val) => [val.toFixed(4), 'Кореляція']} labelFormatter={(l) => `Лаг: ${l}`} />
                                            <Bar dataKey="correlation" name="Кореляція" fill="#2c5f2e" radius={[2,2,0,0]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            )}

                            {results.rolling_correlation?.rolling_correlations?.length > 0 && (
                                <div style={{marginTop:'24px'}}>
                                    <h3 style={{color:'#2c5f2e', marginBottom:'8px', fontSize:'15px'}}>
                                        Ковзна кореляція (вікно: {results.rolling_correlation.window_size})
                                    </h3>
                                    <p style={{color:'#888', fontSize:'12px', marginBottom:'12px'}}>
                                        Показує як змінюється сила зв'язку в часі. Стабільна лінія — стійка залежність, коливання — нестабільна.
                                    </p>
                                    <ResponsiveContainer width="100%" height={250}>
                                        <LineChart data={results.rolling_correlation.rolling_correlations} margin={{top:10, right:20, left:0, bottom:10}}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="window_start" label={{value:'Позиція вікна', position:'insideBottom', offset:-5}} />
                                            <YAxis domain={[-1, 1]} label={{value:'Кореляція', angle:-90, position:'insideLeft'}} />
                                            <Tooltip formatter={(val) => [val.toFixed(4), 'Кореляція']} />
                                            <Line type="monotone" dataKey="correlation" stroke="#2c5f2e" strokeWidth={2} dot={{r:4}} name="Ковзна кореляція" />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            )}
                        </>
                    )}

                    {method === 'regression' && results.result && (
                        <>
                            <div style={s.resultCard}>
                                <p><b>Рівняння:</b> {results.result.equation}</p>
                                <p><b>R²:</b> {results.result.r_squared}</p>
                                <p><b>Скоригований R²:</b> {results.result.adj_r_squared}</p>
                                <p><b>F-статистика:</b> {results.result.f_statistic}</p>
                                <p><b>p-value:</b> {results.result.p_value}</p>
                                <p><b>Значущість:</b> {results.result.is_significant ? 'Так' : 'Ні'}</p>
                                <p><b>Стандартна похибка:</b> {results.result.std_error}</p>
                                <p><b>Інтерпретація:</b> {results.result.interpretation}</p>
                            </div>
                            {renderRegressionCharts(results.result)}
                        </>
                    )}

                    {method === 'regression_multiple' && results.result && (
                        <div style={s.resultCard}>
                            <p><b>Метод:</b> Множинна регресія</p>
                            <p><b>R²:</b> {results.result.r_squared}</p>
                            <p><b>Скоригований R²:</b> {results.result.adj_r_squared}</p>
                            <p><b>Спостережень:</b> {results.result.n_observations}</p>
                            <p><b>Інтерпретація:</b> {results.result.interpretation}</p>
                            <div style={{marginTop:'12px'}}>
                                <b>Коефіцієнти:</b>
                                <table style={{...s.table, marginTop:'8px'}}>
                                    <thead>
                                        <tr style={s.thead}>
                                            <th style={s.th}>Показник</th>
                                            <th style={s.th}>Коефіцієнт</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {Object.entries(results.result.coefficients || {}).map(([key, val]) => (
                                            <tr key={key} style={s.tr}>
                                                <td style={s.td}>{key === 'intercept' ? 'Константа' : (INDICATOR_LABELS[key] || key)}</td>
                                                <td style={s.td}>{val}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                            {results.result.vif?.length > 0 && (
                                <div style={{marginTop:'18px'}}>
                                    <b>Перевірка мультиколінеарності (VIF):</b>
                                    <table style={{...s.table, marginTop:'8px'}}>
                                        <thead>
                                            <tr style={s.thead}>
                                                <th style={s.th}>Показник</th>
                                                <th style={s.th}>VIF</th>
                                                <th style={s.th}>Оцінка</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {results.result.vif.map(row => (
                                                <tr key={row.indicator} style={s.tr}>
                                                    <td style={s.td}>{INDICATOR_LABELS[row.indicator] || row.indicator}</td>
                                                    <td style={s.td}>{row.vif}</td>
                                                    <td style={s.td}>{row.interpretation}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    )}

                    {method === 'comparison' && results.result && (
                        <div style={s.resultCard}>
                            <p><b>Узгодженість методів:</b> {results.result.agreement?.level}</p>
                            <p><b>Деталі:</b> {results.result.agreement?.detail}</p>
                            <p><b>Рекомендація:</b> {results.result.recommendation}</p>

                            {results.result.summary_table && (
                                <div style={{marginTop:'16px'}}>
                                    <b>Зведена таблиця методів:</b>
                                    <table style={{...s.table, marginTop:'8px'}}>
                                        <thead>
                                            <tr style={s.thead}>
                                                <th style={s.th}>Метод</th>
                                                <th style={s.th}>Коефіцієнт</th>
                                                <th style={s.th}>p-value</th>
                                                <th style={s.th}>Значущість</th>
                                                <th style={s.th}>Інтерпретація</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {['pearson', 'spearman', 'kendall'].map(m => (
                                                <tr key={m} style={s.tr}>
                                                    <td style={s.td}>{m === 'pearson' ? 'Пірсон' : m === 'spearman' ? 'Спірмен' : 'Кендалл'}</td>
                                                    <td style={s.td}>{results.result.summary_table[m]?.coefficient}</td>
                                                    <td style={s.td}>{results.result.summary_table[m]?.p_value}</td>
                                                    <td style={{...s.td, color: results.result.summary_table[m]?.is_significant ? 'green' : 'red'}}>
                                                        {results.result.summary_table[m]?.is_significant ? 'Так' : 'Ні'}
                                                    </td>
                                                    <td style={s.td}>{results.result.summary_table[m]?.interpretation}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                    <p style={{marginTop:'10px'}}><b>R² лінійної регресії:</b> {results.result.summary_table.regression_r_squared}</p>
                                    <p><b>Рівняння:</b> {results.result.summary_table.regression_equation}</p>
                                </div>
                            )}

                            <div style={{marginTop:'16px'}}>
                                <b>Суперечності між методами:</b>
                                {results.result.conflicts?.length > 0 ? (
                                    <table style={{...s.table, marginTop:'8px'}}>
                                        <thead>
                                            <tr style={s.thead}>
                                                <th style={s.th}>Тип</th>
                                                <th style={s.th}>Опис</th>
                                                <th style={s.th}>Можлива причина</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {results.result.conflicts.map((c, i) => (
                                                <tr key={i} style={s.tr}>
                                                    <td style={s.td}>{c.type}</td>
                                                    <td style={s.td}>{c.description}</td>
                                                    <td style={s.td}>{c.possible_reason}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                ) : (
                                    <p style={{color:'#2c5f2e'}}>Суперечностей не виявлено</p>
                                )}
                            </div>

                            {results.result.ranking?.length > 0 && (
                                <div style={{marginTop:'16px'}}>
                                    <b>Ranking методів за силою коефіцієнта:</b>
                                    <table style={{...s.table, marginTop:'8px'}}>
                                        <thead>
                                            <tr style={s.thead}>
                                                <th style={s.th}>Місце</th>
                                                <th style={s.th}>Метод</th>
                                                <th style={s.th}>Коефіцієнт</th>
                                                <th style={s.th}>Модуль</th>
                                                <th style={s.th}>Висновок</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {results.result.ranking.map(row => (
                                                <tr key={row.method} style={s.tr}>
                                                    <td style={s.td}>{row.rank}</td>
                                                    <td style={s.td}>{row.method_name}</td>
                                                    <td style={s.td}>{row.coefficient}</td>
                                                    <td style={s.td}>{row.abs_coefficient}</td>
                                                    <td style={s.td}>{row.conclusion}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {matrix && (
                <div style={s.results}>
                    <h2 style={s.resultsTitle}>Кореляційна матриця</h2>
                    <p style={s.meta}>
                        Проаналізовано пар: {matrix.total_pairs} |
                        Еко: {matrix.eco_indicators.map(i => INDICATOR_LABELS[i] || i).join(', ')} |
                        Екон: {matrix.econ_indicators.map(i => INDICATOR_LABELS[i] || i).join(', ')}
                    </p>
                    <p style={{fontSize:'12px', color:'#888', marginBottom:'12px'}}>
                        Зелений фон — значуща позитивна кореляція. Рожевий — значуща негативна. Поправка Бонферроні застосована.
                    </p>
                    <div style={{overflowX: 'auto'}}>
                        <table style={s.table}>
                            <thead>
                                <tr style={s.thead}>
                                    <th style={s.th}>Еко показник</th>
                                    <th style={s.th}>Екон показник</th>
                                    <th style={s.th}>N</th>
                                    <th style={s.th}>Пірсон</th>
                                    <th style={s.th}>p (Бонф.)</th>
                                    <th style={s.th}>Значущість</th>
                                    <th style={s.th}>Спірмен</th>
                                    <th style={s.th}>Інтерпретація</th>
                                </tr>
                            </thead>
                            <tbody>
                                {matrix.matrix.map((row, i) => (
                                    <tr key={i} style={{
                                        ...s.tr,
                                        background: getCellColor(row.pearson_significant_bonferroni ? row.pearson : 0)
                                    }}>
                                        <td style={s.td}>{INDICATOR_LABELS[row.eco_indicator] || row.eco_indicator}</td>
                                        <td style={s.td}>{INDICATOR_LABELS[row.econ_indicator] || row.econ_indicator}</td>
                                        <td style={s.td}>{row.n}</td>
                                        <td style={{...s.td, fontWeight:'bold', color: row.pearson > 0.5 ? '#2c5f2e' : row.pearson < -0.5 ? '#cc0000' : '#333'}}>
                                            {row.pearson}
                                        </td>
                                        <td style={s.td}>{row.pearson_p_bonferroni}</td>
                                        <td style={{...s.td, color: row.pearson_significant_bonferroni ? 'green' : '#999'}}>
                                            {row.pearson_significant_bonferroni ? 'Так' : 'Ні'}
                                        </td>
                                        <td style={s.td}>{row.spearman}</td>
                                        <td style={s.td}>{row.interpretation}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
};

const s = {
    container: { padding: '24px', maxWidth: '1200px', margin: '0 auto' },
    title: { color: '#2c5f2e', fontSize: '28px', marginBottom: '24px' },
    error: { background: '#ffe0e0', color: '#cc0000', padding: '12px', borderRadius: '6px', marginBottom: '16px', cursor: 'pointer' },
    warningBox: { background: '#fff3e0', border: '1px solid #ffb74d', padding: '12px 16px', borderRadius: '6px', marginBottom: '16px', fontSize: '13px', lineHeight: '1.8' },
    controls: { background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', marginBottom: '24px', display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'flex-end' },
    field: { minWidth: '200px' },
    label: { display: 'block', marginBottom: '6px', fontSize: '13px', color: '#555', fontWeight: 'bold' },
    select: { width: '100%', padding: '8px 10px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '14px' },
    checkboxGroup: { display: 'flex', flexDirection: 'column', gap: '4px', padding: '8px', border: '1px solid #ddd', borderRadius: '6px', maxHeight: '160px', overflowY: 'auto' },
    checkboxLabel: { fontSize: '13px', color: '#333', cursor: 'pointer', display: 'flex', alignItems: 'center' },
    button: { padding: '10px 24px', background: '#2c5f2e', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '14px', height: '38px' },
    btnMatrix: { padding: '10px 24px', background: '#0066cc', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '14px', height: '38px' },
    results: { background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', marginBottom: '24px' },
    resultsTitle: { color: '#2c5f2e', marginBottom: '8px' },
    meta: { color: '#888', fontSize: '13px', marginBottom: '16px' },
    prepBox: { background: '#fff8e1', border: '1px solid #ffe082', padding: '12px 16px', borderRadius: '6px', marginBottom: '12px', fontSize: '13px', lineHeight: '2' },
    normalityBox: { background: '#f0f7f0', border: '1px solid #c8e6c9', padding: '12px 16px', borderRadius: '6px', marginBottom: '16px', fontSize: '13px' },
    table: { width: '100%', borderCollapse: 'collapse', marginTop: '16px' },
    thead: { background: '#2c5f2e' },
    th: { padding: '10px 12px', color: 'white', textAlign: 'left', fontSize: '13px' },
    tr: { borderBottom: '1px solid #eee' },
    td: { padding: '10px 12px', fontSize: '13px' },
    resultCard: { background: '#f9f9f9', padding: '20px', borderRadius: '8px', lineHeight: '2' },
};

export default Analysis;