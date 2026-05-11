import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Register = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [inviteCode, setInviteCode] = useState('');
    const { register, loading, error } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        const success = await register(email, password, fullName, inviteCode);
        if (success) navigate('/login');
    };

    return (
        <div style={styles.container}>
            <div style={styles.card}>
                <h1 style={styles.title}>🌿 Кореляційний аналіз</h1>
                <h2 style={styles.subtitle}>Реєстрація</h2>
                {error && <div style={styles.error}>{error}</div>}
                <form onSubmit={handleSubmit}>
                    <div style={styles.field}>
                        <label style={styles.label}>Повне ім'я</label>
                        <input
                            type="text"
                            value={fullName}
                            onChange={(e) => setFullName(e.target.value)}
                            style={styles.input}
                            placeholder="Іван Іванов"
                        />
                    </div>
                    <div style={styles.field}>
                        <label style={styles.label}>Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            style={styles.input}
                            placeholder="email@example.com"
                            required
                        />
                    </div>
                    <div style={styles.field}>
                        <label style={styles.label}>Пароль</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            style={styles.input}
                            placeholder="••••••••"
                            required
                        />
                    </div>
                    <div style={styles.field}>
                        <label style={styles.label}>
                            Інвайт-код <span style={styles.optional}>(необов'язково)</span>
                        </label>
                        <input
                            type="text"
                            value={inviteCode}
                            onChange={(e) => setInviteCode(e.target.value)}
                            style={styles.input}
                            placeholder="ADMIN-xxxxxxxx або LPR-xxxxxxxx"
                        />
                        <p style={styles.hint}>
                            Без коду - роль Аналітика. З кодом від адміністратора - роль Адміна або ЛПР.
                        </p>
                    </div>
                    <button type="submit" style={styles.button} disabled={loading}>
                        {loading ? 'Завантаження...' : 'Зареєструватись'}
                    </button>
                </form>
                <p style={styles.link}>
                    Вже є акаунт? <Link to="/login">Увійти</Link>
                </p>
            </div>
        </div>
    );
};

const styles = {
    container: {
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #1a3a1a 0%, #2c5f2e 100%)',
    },
    card: {
        background: 'white',
        padding: '40px',
        borderRadius: '12px',
        boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
        width: '400px',
    },
    title: {
        textAlign: 'center',
        color: '#2c5f2e',
        marginBottom: '8px',
        fontSize: '24px',
    },
    subtitle: {
        textAlign: 'center',
        color: '#666',
        marginBottom: '24px',
        fontSize: '18px',
        fontWeight: 'normal',
    },
    error: {
        background: '#ffe0e0',
        color: '#cc0000',
        padding: '10px',
        borderRadius: '6px',
        marginBottom: '16px',
        fontSize: '14px',
    },
    field: { marginBottom: '16px' },
    label: {
        display: 'block',
        marginBottom: '6px',
        color: '#333',
        fontWeight: 'bold',
        fontSize: '14px',
    },
    optional: {
        color: '#999',
        fontWeight: 'normal',
        fontSize: '12px',
    },
    input: {
        width: '100%',
        padding: '10px 12px',
        border: '1px solid #ddd',
        borderRadius: '6px',
        fontSize: '14px',
        boxSizing: 'border-box',
    },
    hint: {
        color: '#888',
        fontSize: '12px',
        marginTop: '4px',
    },
    button: {
        width: '100%',
        padding: '12px',
        background: '#2c5f2e',
        color: 'white',
        border: 'none',
        borderRadius: '6px',
        fontSize: '16px',
        cursor: 'pointer',
        marginTop: '8px',
    },
    link: {
        textAlign: 'center',
        marginTop: '16px',
        color: '#666',
        fontSize: '14px',
    }
};

export default Register;