import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = 'http://localhost:8000';

const AdminPanel = () => {
    const [users, setUsers] = useState([]);
    const [invites, setInvites] = useState([]);
    const [activeTab, setActiveTab] = useState('users');
    const [inviteRole, setInviteRole] = useState('lpr');
    const [inviteDays, setInviteDays] = useState(7);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    const token = localStorage.getItem('token');
    const headers = { Authorization: `Bearer ${token}` };

    useEffect(() => {
        loadUsers();
        loadInvites();
    }, []);

    const loadUsers = async () => {
        try {
            const res = await axios.get(`${API}/users/`, { headers });
            setUsers(res.data);
        } catch (err) {
            setError('Помилка завантаження користувачів');
        }
    };

    const loadInvites = async () => {
        try {
            const res = await axios.get(`${API}/invites/`, { headers });
            setInvites(res.data);
        } catch (err) {
            console.error(err);
        }
    };

    const handleRoleChange = async (userId, newRole) => {
        try {
            await axios.patch(
                `${API}/users/${userId}/role?role=${newRole}`,
                {},
                { headers }
            );
            setMessage(`Роль змінено на ${newRole}`);
            loadUsers();
        } catch (err) {
            setError('Помилка зміни ролі');
        }
    };

    const handleDeactivate = async (userId) => {
        if (!window.confirm('Деактивувати користувача?')) return;
        try {
            await axios.patch(`${API}/users/${userId}/deactivate`, {}, { headers });
            setMessage('Користувача заблоковано');
            loadUsers();
        } catch (err) {
            setError('Помилка деактивації');
        }
    };

    const handleActivate = async (userId) => {
        if (!window.confirm('Розблокувати користувача?')) return;
        try {
            await axios.patch(`${API}/users/${userId}/activate`, {}, { headers });
            setMessage('Користувача розблоковано');
            loadUsers();
        } catch (err) {
            setError('Помилка активації');
        }
    };

    const handleGenerateInvite = async () => {
        try {
            const res = await axios.post(
                `${API}/invites/generate`,
                { role: inviteRole, expires_in_days: parseInt(inviteDays) },
                { headers }
            );
            setMessage(`Код згенеровано: ${res.data.code}`);
            loadInvites();
        } catch (err) {
            setError('Помилка генерації коду');
        }
    };

    const handleDeleteInvite = async (inviteId) => {
        try {
            await axios.delete(`${API}/invites/${inviteId}`, { headers });
            setMessage('Код видалено');
            loadInvites();
        } catch (err) {
            setError('Помилка видалення');
        }
    };

    const getRoleBadge = (role) => {
        const colors = {
            admin: '#dc3545',
            analyst: '#2c5f2e',
            lpr: '#0066cc',
            guest: '#888'
        };
        const labels = {
            admin: 'Адмін',
            analyst: 'Аналітик',
            lpr: 'ЛПР',
            guest: 'Гість'
        };
        return (
            <span style={{
                background: colors[role] || '#888',
                color: 'white',
                padding: '2px 10px',
                borderRadius: '12px',
                fontSize: '12px',
                fontWeight: 'bold'
            }}>
                {labels[role] || role}
            </span>
        );
    };

    return (
        <div style={styles.container}>
            <h1 style={styles.title}>Адміністративна панель</h1>

            {message && (
                <div style={styles.success} onClick={() => setMessage('')}>
                    {message}
                </div>
            )}
            {error && (
                <div style={styles.error} onClick={() => setError('')}>
                    {error}
                </div>
            )}

            <div style={styles.tabs}>
                <button
                    style={activeTab === 'users' ? styles.tabActive : styles.tab}
                    onClick={() => setActiveTab('users')}
                >
                    👥 Користувачі ({users.length})
                </button>
                <button
                    style={activeTab === 'invites' ? styles.tabActive : styles.tab}
                    onClick={() => setActiveTab('invites')}
                >
                    Інвайт-коди ({invites.length})
                </button>
            </div>

            {activeTab === 'users' && (
                <div style={styles.card}>
                    <h2 style={styles.cardTitle}>Управління користувачами</h2>
                    <table style={styles.table}>
                        <thead>
                            <tr style={styles.thead}>
                                <th style={styles.th}>ID</th>
                                <th style={styles.th}>Email</th>
                                <th style={styles.th}>Ім'я</th>
                                <th style={styles.th}>Роль</th>
                                <th style={styles.th}>Статус</th>
                                <th style={styles.th}>Дії</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map(user => (
                                <tr key={user.id} style={styles.tr}>
                                    <td style={styles.td}>{user.id}</td>
                                    <td style={styles.td}>{user.email}</td>
                                    <td style={styles.td}>{user.full_name || '—'}</td>
                                    <td style={styles.td}>{getRoleBadge(user.role)}</td>
                                    <td style={styles.td}>
                                        <span style={{
                                            color: user.is_active ? 'green' : 'red',
                                            fontSize: '13px'
                                        }}>
                                            {user.is_active ? '● Активний' : '● Неактивний'}
                                        </span>
                                    </td>
                                    <td style={styles.td}>
                                        <select
                                            style={styles.roleSelect}
                                            value={user.role}
                                            onChange={(e) => handleRoleChange(user.id, e.target.value)}
                                        >
                                            <option value="analyst">Аналітик</option>
                                            <option value="lpr">ЛПР</option>
                                            <option value="admin">Адмін</option>
                                        </select>
                                        {user.is_active ? (
                                            <button
                                                style={styles.btnDanger}
                                                onClick={() => handleDeactivate(user.id)}
                                            >
                                                Блок
                                            </button>
                                        ) : (
                                            <button
                                                style={styles.btnSuccess}
                                                onClick={() => handleActivate(user.id)}
                                            >
                                                Розблок
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {activeTab === 'invites' && (
                <div style={styles.card}>
                    <h2 style={styles.cardTitle}>Генерація інвайт-кодів</h2>

                    <div style={styles.generateForm}>
                        <div style={styles.field}>
                            <label style={styles.label}>Роль для коду</label>
                            <select
                                value={inviteRole}
                                onChange={e => setInviteRole(e.target.value)}
                                style={styles.select}
                            >
                                <option value="lpr">ЛПР</option>
                                <option value="admin">Адмін</option>
                                <option value="analyst">Аналітик</option>
                            </select>
                        </div>
                        <div style={styles.field}>
                            <label style={styles.label}>Термін дії (днів)</label>
                            <input
                                type="number"
                                value={inviteDays}
                                onChange={e => setInviteDays(e.target.value)}
                                style={styles.select}
                                min="1"
                                max="30"
                            />
                        </div>
                        <button onClick={handleGenerateInvite} style={styles.btnGenerate}>
                            Згенерувати код
                        </button>
                    </div>

                    <h3 style={{ color: '#333', marginTop: '24px' }}>Всі коди</h3>
                    <table style={styles.table}>
                        <thead>
                            <tr style={styles.thead}>
                                <th style={styles.th}>Код</th>
                                <th style={styles.th}>Роль</th>
                                <th style={styles.th}>Статус</th>
                                <th style={styles.th}>Використав</th>
                                <th style={styles.th}>Дія</th>
                            </tr>
                        </thead>
                        <tbody>
                            {invites.map(inv => (
                                <tr key={inv.id} style={styles.tr}>
                                    <td style={styles.td}>
                                        <code style={styles.code}>{inv.code}</code>
                                    </td>
                                    <td style={styles.td}>{getRoleBadge(inv.role)}</td>
                                    <td style={styles.td}>
                                        <span style={{ color: inv.is_used ? 'red' : 'green', fontSize: '13px' }}>
                                            {inv.is_used ? '● Використано' : '● Активний'}
                                        </span>
                                    </td>
                                    <td style={styles.td}>{inv.used_by_email || '—'}</td>
                                    <td style={styles.td}>
                                        {!inv.is_used && (
                                            <button
                                                style={styles.btnDanger}
                                                onClick={() => handleDeleteInvite(inv.id)}
                                            >
                                                Видалити
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

const styles = {
    container: { padding: '24px', maxWidth: '1200px', margin: '0 auto' },
    title: { color: '#2c5f2e', fontSize: '28px', marginBottom: '24px' },
    success: { background: '#e8f5e9', color: '#2c5f2e', padding: '12px', borderRadius: '6px', marginBottom: '16px', cursor: 'pointer' },
    error: { background: '#ffe0e0', color: '#cc0000', padding: '12px', borderRadius: '6px', marginBottom: '16px', cursor: 'pointer' },
    tabs: { display: 'flex', gap: '8px', marginBottom: '24px' },
    tab: { padding: '10px 20px', background: '#f0f0f0', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '14px' },
    tabActive: { padding: '10px 20px', background: '#2c5f2e', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '14px' },
    card: { background: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' },
    cardTitle: { color: '#333', marginBottom: '20px' },
    table: { width: '100%', borderCollapse: 'collapse' },
    thead: { background: '#2c5f2e' },
    th: { padding: '10px 12px', color: 'white', textAlign: 'left', fontSize: '13px' },
    tr: { borderBottom: '1px solid #eee' },
    td: { padding: '10px 12px', fontSize: '13px' },
    roleSelect: { padding: '4px 8px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '13px', marginRight: '8px' },
    btnDanger: { padding: '4px 10px', background: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' },
    btnSuccess: { padding: '4px 10px', background: '#2c5f2e', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' },
    generateForm: { display: 'flex', gap: '16px', alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: '16px' },
    field: {},
    label: { display: 'block', marginBottom: '6px', fontSize: '13px', color: '#555', fontWeight: 'bold' },
    select: { padding: '8px 10px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '14px' },
    btnGenerate: { padding: '10px 20px', background: '#2c5f2e', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '14px' },
    code: { background: '#f0f0f0', padding: '2px 8px', borderRadius: '4px', fontSize: '13px', fontFamily: 'monospace' },
};

export default AdminPanel;