import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getPublicStats } from '../services/api';

const PublicDashboard = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getPublicStats()
            .then(r => setStats(r.data))
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    return (
        <div style={styles.container}>
            <div style={styles.hero}>
                <h1 style={styles.heroTitle}>Веб-система кореляційного аналізу</h1>
                <p style={styles.heroSubtitle}>
                    Аналіз взаємозв'язків між екологічними та економічними показниками територій України
                </p>
                <div style={styles.heroButtons}>
                    <Link to="/login" style={styles.btnPrimary}>Увійти в систему</Link>
                    <Link to="/register" style={styles.btnSecondary}>Зареєструватись</Link>
                </div>
            </div>

            {!loading && stats && (
                <div style={styles.stats}>
                    <div style={styles.statCard}>
                        <div style={styles.statNumber}>{stats.territories_count}</div>
                        <div style={styles.statLabel}>Територій</div>
                    </div>
                    <div style={styles.statCard}>
                        <div style={styles.statNumber}>{stats.ecological_measurements_count}</div>
                        <div style={styles.statLabel}>Екологічних вимірювань</div>
                    </div>
                    <div style={styles.statCard}>
                        <div style={styles.statNumber}>{stats.economic_measurements_count}</div>
                        <div style={styles.statLabel}>Економічних показників</div>
                    </div>
                </div>
            )}

            <div style={styles.section}>
                <h2 style={styles.sectionTitle}>Можливості системи</h2>
                <div style={styles.features}>
                    {[
                        { title: 'Кореляційний аналіз', desc: 'Пірсон, Спірмен, Кендалл з перевіркою значущості' },
                        { title: 'Часткова кореляція', desc: 'Аналіз з контролем третіх змінних' },
                        { title: 'Часові ряди', desc: 'Крос-кореляція та ковзна кореляція' },
                        { title: 'Регресійний аналіз', desc: 'Лінійна та множинна регресія' },
                        { title: 'Геовізуалізація', desc: 'Карти кореляцій по районах' },
                        { title: 'PDF звіти', desc: 'Автоматична генерація звітів' },
                    ].map((f, i) => (
                        <div key={i} style={styles.featureCard}>
                            <div style={styles.featureIcon}>{f.icon}</div>
                            <h3 style={styles.featureTitle}>{f.title}</h3>
                            <p style={styles.featureDesc}>{f.desc}</p>
                        </div>
                    ))}
                </div>
            </div>

            {!loading && stats && stats.territories.length > 0 && (
                <div style={styles.section}>
                    <h2 style={styles.sectionTitle}>Доступні території</h2>
                    <div style={styles.territoriesGrid}>
                        {stats.territories.map(t => (
                            <div key={t.id} style={styles.territoryCard}>
                                <h3 style={styles.territoryName}>{t.name}</h3>
                                <p style={styles.territoryRegion}>{t.region || 'Регіон не вказано'}</p>
                                {t.latitude && (
                                    <p style={styles.territoryCoords}>
                                        {t.latitude?.toFixed(4)}, {t.longitude?.toFixed(4)}
                                    </p>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div style={styles.footer}>
                <p>Веб-система кореляційного аналізу екологічних та економічних показників території</p>
            </div>
        </div>
    );
};

const styles = {
    container: { minHeight: '100vh', background: '#f5f5f5' },
    hero: {
        background: 'linear-gradient(135deg, #1a3a1a 0%, #2c5f2e 100%)',
        padding: '80px 24px',
        textAlign: 'center',
        color: 'white',
    },
    heroTitle: { fontSize: '36px', marginBottom: '16px', fontWeight: 'bold' },
    heroSubtitle: { fontSize: '18px', opacity: 0.9, marginBottom: '32px', maxWidth: '600px', margin: '0 auto 32px' },
    heroButtons: { display: 'flex', gap: '16px', justifyContent: 'center' },
    btnPrimary: {
        background: 'white', color: '#2c5f2e', padding: '12px 32px',
        borderRadius: '6px', textDecoration: 'none', fontWeight: 'bold', fontSize: '16px'
    },
    btnSecondary: {
        background: 'transparent', color: 'white', padding: '12px 32px',
        borderRadius: '6px', textDecoration: 'none', border: '2px solid white', fontSize: '16px'
    },
    stats: {
        display: 'flex', justifyContent: 'center', gap: '24px',
        padding: '32px 24px', flexWrap: 'wrap',
    },
    statCard: {
        background: 'white', padding: '24px 48px', borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)', textAlign: 'center',
        borderTop: '4px solid #2c5f2e',
    },
    statNumber: { fontSize: '48px', fontWeight: 'bold', color: '#2c5f2e' },
    statLabel: { color: '#666', fontSize: '14px', marginTop: '4px' },
    section: { padding: '48px 24px', maxWidth: '1200px', margin: '0 auto' },
    sectionTitle: { color: '#2c5f2e', fontSize: '28px', marginBottom: '24px', textAlign: 'center' },
    features: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '20px' },
    featureCard: {
        background: 'white', padding: '24px', borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)', textAlign: 'center',
    },
    featureIcon: { fontSize: '36px', marginBottom: '12px' },
    featureTitle: { color: '#2c5f2e', marginBottom: '8px', fontSize: '16px' },
    featureDesc: { color: '#666', fontSize: '13px', lineHeight: '1.5' },
    territoriesGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px' },
    territoryCard: {
        background: 'white', padding: '20px', borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)', borderLeft: '4px solid #2c5f2e',
    },
    territoryName: { color: '#2c5f2e', margin: '0 0 8px 0' },
    territoryRegion: { color: '#666', fontSize: '13px', margin: '0 0 4px 0' },
    territoryCoords: { color: '#999', fontSize: '12px', margin: 0 },
    footer: {
        background: '#2c5f2e', color: 'white', textAlign: 'center',
        padding: '24px', fontSize: '14px',
    },
};

export default PublicDashboard;