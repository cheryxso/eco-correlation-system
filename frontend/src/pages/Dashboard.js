import React, { useState, useEffect } from 'react';
import { getTerritories, createTerritory } from '../services/api';
import axios from 'axios';

const API = 'http://localhost:8000';

const Dashboard = () => {
    const [territories, setTerritories] = useState([]);
    const [showForm, setShowForm] = useState(false);
    const [editingTerritory, setEditingTerritory] = useState(null);
    const [formData, setFormData] = useState({ name: '', region: '', latitude: '', longitude: '' });
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [coordsLoading, setCoordsLoading] = useState(false);

    const token = localStorage.getItem('token');
    const headers = { Authorization: `Bearer ${token}` };

    useEffect(() => {
        loadTerritories();
    }, []);

    const loadTerritories = async () => {
        try {
            const response = await getTerritories();
            setTerritories(response.data);
        } catch (err) {
            setError('Помилка завантаження територій');
        }
    };

    const handleOpenCreate = () => {
        setEditingTerritory(null);
        setFormData({ name: '', region: '', latitude: '', longitude: '' });
        setShowForm(true);
    };

    const handleOpenEdit = (t) => {
        setEditingTerritory(t);
        setFormData({
            name: t.name,
            region: t.region || '',
            latitude: t.latitude || '',
            longitude: t.longitude || ''
        });
        setShowForm(true);
    };

    const fetchCoordinates = async (cityName) => {
        if (!cityName) return;
        setCoordsLoading(true);
        try {
            const res = await axios.get(
                'https://nominatim.openstreetmap.org/search',
                {
                    params: {
                        q: `${cityName}, Ukraine`,
                        format: 'json',
                        limit: 1,
                        'accept-language': 'uk'
                    },
                    headers: { 'User-Agent': 'eco-analysis-system' }
                }
            );
            if (res.data.length > 0) {
                const displayName = res.data[0].display_name;
                const parts = displayName.split(',').map(p => p.trim());
                const oblast = parts.find(p => p.toLowerCase().includes('область'));
                const region = oblast || parts[1] || '';

                setFormData(prev => ({
                    ...prev,
                    latitude: parseFloat(res.data[0].lat).toFixed(4),
                    longitude: parseFloat(res.data[0].lon).toFixed(4),
                    region: region
                }));
            }
        } catch (err) {
            console.error(err);
        } finally {
            setCoordsLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const data = {
                name: formData.name,
                region: formData.region,
                latitude: parseFloat(formData.latitude) || null,
                longitude: parseFloat(formData.longitude) || null,
            };
            if (editingTerritory) {
                await axios.put(`${API}/territories/${editingTerritory.id}`, data, { headers });
                setMessage('Територію оновлено!');
            } else {
                await createTerritory(data);
                setMessage('Територію створено!');
            }
            setShowForm(false);
            setEditingTerritory(null);
            setFormData({ name: '', region: '', latitude: '', longitude: '' });
            loadTerritories();
        } catch (err) {
            setError('Помилка збереження території');
        }
    };

    const handleDelete = async (id, name) => {
        if (!window.confirm(`Видалити територію "${name}"?`)) return;
        try {
            await axios.delete(`${API}/territories/${id}`, { headers });
            setMessage(`Територію "${name}" видалено`);
            loadTerritories();
        } catch (err) {
            setError('Помилка видалення території');
        }
    };

    return (
        <div style={styles.container}>
            <div style={styles.header}>
                <h1 style={styles.title}>Дашборд</h1>
                <button onClick={handleOpenCreate} style={styles.button}>
                    + Додати територію
                </button>
            </div>

            {message && <div style={styles.success} onClick={() => setMessage('')}>{message}</div>}
            {error && <div style={styles.error} onClick={() => setError('')}>{error}</div>}

            {showForm && (
                <div style={styles.form}>
                    <h3>{editingTerritory ? `Редагувати: ${editingTerritory.name}` : 'Нова територія'}</h3>
                    <p style={styles.hint}>Введіть назву міста і перейдіть до наступного поля — координати і область підставляться автоматично</p>
                    <form onSubmit={handleSubmit}>
                        <div style={styles.grid}>
                            <div>
                                <label style={styles.label}>Назва міста *</label>
                                <input
                                    style={styles.input}
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    onBlur={(e) => fetchCoordinates(e.target.value)}
                                    required
                                    placeholder="Харків"
                                />
                            </div>
                            <div>
                                <label style={styles.label}>
                                    Область {coordsLoading && <span style={styles.loading}>завантаження...</span>}
                                </label>
                                <input
                                    style={styles.input}
                                    value={formData.region}
                                    onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                                    placeholder="заповниться автоматично"
                                />
                            </div>
                            <div>
                                <label style={styles.label}>Широта</label>
                                <input
                                    style={styles.input}
                                    value={formData.latitude}
                                    onChange={(e) => setFormData({ ...formData, latitude: e.target.value })}
                                    placeholder="заповниться автоматично"
                                />
                            </div>
                            <div>
                                <label style={styles.label}>Довгота</label>
                                <input
                                    style={styles.input}
                                    value={formData.longitude}
                                    onChange={(e) => setFormData({ ...formData, longitude: e.target.value })}
                                    placeholder="заповниться автоматично"
                                />
                            </div>
                        </div>
                        <div style={{ display: 'flex', gap: '8px' }}>
                            <button type="submit" style={styles.button}>
                                {editingTerritory ? 'Зберегти зміни' : 'Створити'}
                            </button>
                            <button
                                type="button"
                                onClick={() => setShowForm(false)}
                                style={styles.btnCancel}
                            >
                                Скасувати
                            </button>
                        </div>
                    </form>
                </div>
            )}

            <div style={styles.stats}>
                <div style={styles.statCard}>
                    <div style={styles.statNumber}>{territories.length}</div>
                    <div style={styles.statLabel}>Територій</div>
                </div>
            </div>

            <h2 style={styles.sectionTitle}>Території</h2>
            <div style={styles.grid}>
                {territories.map(t => (
                    <div key={t.id} style={styles.card}>
                        <h3 style={styles.cardTitle}>{t.name}</h3>
                        <p style={styles.cardText}>{t.region || 'Регіон не вказано'}</p>
                        {t.latitude && (
                            <p style={styles.cardText}>
                                {t.latitude}, {t.longitude}
                            </p>
                        )}
                        <p style={styles.cardId}>ID: {t.id}</p>
                        <div style={styles.cardActions}>
                            <button style={styles.btnEdit} onClick={() => handleOpenEdit(t)}>
                                Редагувати
                            </button>
                            <button style={styles.btnDelete} onClick={() => handleDelete(t.id, t.name)}>
                                Видалити
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

const styles = {
    container: { padding: '24px', maxWidth: '1200px', margin: '0 auto' },
    header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' },
    title: { color: '#2c5f2e', fontSize: '28px', margin: 0 },
    button: { background: '#2c5f2e', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '6px', cursor: 'pointer', fontSize: '14px' },
    btnCancel: { background: '#888', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '6px', cursor: 'pointer', fontSize: '14px' },
    success: { background: '#e8f5e9', color: '#2c5f2e', padding: '10px 16px', borderRadius: '6px', marginBottom: '16px', cursor: 'pointer' },
    error: { background: '#ffe0e0', color: '#cc0000', padding: '10px 16px', borderRadius: '6px', marginBottom: '16px', cursor: 'pointer' },
    form: { background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', marginBottom: '24px' },
    hint: { color: '#2c5f2e', fontSize: '13px', background: '#f0f7f0', padding: '8px 12px', borderRadius: '6px', marginBottom: '16px' },
    loading: { color: '#888', fontSize: '12px', fontWeight: 'normal' },
    grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '16px', marginBottom: '16px' },
    label: { display: 'block', marginBottom: '4px', fontSize: '13px', color: '#555', fontWeight: 'bold' },
    input: { width: '100%', padding: '8px 10px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '14px', boxSizing: 'border-box' },
    stats: { display: 'flex', gap: '16px', marginBottom: '24px' },
    statCard: { background: 'white', padding: '20px 32px', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', textAlign: 'center', borderTop: '4px solid #2c5f2e' },
    statNumber: { fontSize: '36px', fontWeight: 'bold', color: '#2c5f2e' },
    statLabel: { color: '#666', fontSize: '14px' },
    sectionTitle: { color: '#333', marginBottom: '16px' },
    card: { background: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', borderLeft: '4px solid #2c5f2e' },
    cardTitle: { color: '#2c5f2e', margin: '0 0 8px 0' },
    cardText: { color: '#666', margin: '4px 0', fontSize: '14px' },
    cardId: { color: '#999', fontSize: '12px', marginTop: '8px' },
    cardActions: { display: 'flex', gap: '8px', marginTop: '12px' },
    btnEdit: { padding: '6px 12px', background: '#0066cc', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' },
    btnDelete: { padding: '6px 12px', background: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' },
};

export default Dashboard;