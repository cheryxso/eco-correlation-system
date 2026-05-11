import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const getRoleFromToken = (token) => {
    if (!token) return 'guest';

    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload?.role || 'guest';
    } catch (error) {
        return 'guest';
    }
};

const Navbar = () => {
    const { token, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    if (!token) return null;

    const role = getRoleFromToken(token);
    const isAdmin = role === 'admin';
    const isAnalyst = role === 'analyst';
    const isLpr = role === 'lpr';

    return (
        <nav style={styles.nav}>
            <div style={styles.brand}>Кореляційний аналіз</div>
            <div style={styles.links}>
                {(isAdmin || isAnalyst || isLpr) && (
                    <Link to="/dashboard" style={styles.link}>Дашборд</Link>
                )}

                {(isAdmin || isAnalyst) && (
                    <Link to="/upload" style={styles.link}>Дані</Link>
                )}

                {(isAdmin || isAnalyst) && (
                    <Link to="/analysis" style={styles.link}>Аналіз</Link>
                )}

                {(isAdmin || isAnalyst || isLpr) && (
                    <Link to="/reports" style={styles.link}>Звіти</Link>
                )}

                {isAdmin && (
                    <Link to="/admin" style={styles.adminLink}>Адмін</Link>
                )}

                <button onClick={handleLogout} style={styles.logout}>Вийти</button>
            </div>
        </nav>
    );
};

const styles = {
    nav: {
        background: '#2c5f2e', padding: '0 24px', display: 'flex',
        alignItems: 'center', justifyContent: 'space-between',
        height: '60px', boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
    },
    brand: { color: 'white', fontSize: '20px', fontWeight: 'bold' },
    links: { display: 'flex', alignItems: 'center', gap: '24px' },
    link: { color: 'white', textDecoration: 'none', fontSize: '15px', opacity: 0.9 },
    adminLink: {
        color: '#ffcc00', textDecoration: 'none', fontSize: '15px',
        fontWeight: 'bold', border: '1px solid #ffcc00',
        padding: '4px 12px', borderRadius: '4px'
    },
    logout: {
        background: 'rgba(255,255,255,0.2)', color: 'white',
        border: '1px solid rgba(255,255,255,0.4)', padding: '6px 16px',
        borderRadius: '6px', cursor: 'pointer', fontSize: '14px',
    }
};

export default Navbar;