import React, { createContext, useState, useContext, useEffect } from 'react';
import { login as loginApi, register as registerApi } from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('token'));
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (token) {
            localStorage.setItem('token', token);
        }
    }, [token]);

    const login = async (email, password) => {
        setLoading(true);
        setError(null);
        try {
            const response = await loginApi({ email, password });
            const { access_token } = response.data;
            setToken(access_token);
            localStorage.setItem('token', access_token);
            return true;
        } catch (err) {
            setError(err.response?.data?.detail || 'Помилка входу');
            return false;
        } finally {
            setLoading(false);
        }
    };

            const register = async (email, password, fullName, inviteCode) => {
            setLoading(true);
            setError(null);
         try {
            await registerApi({
            email,
            password,
            full_name: fullName,
            invite_code: inviteCode || null
        });
        return true;
    } catch (err) {
        setError(err.response?.data?.detail || 'Помилка реєстрації');
        return false;
    } finally {
        setLoading(false);
    }
};

    const logout = () => {
        setToken(null);
        setUser(null);
        localStorage.removeItem('token');
    };

    return (
        <AuthContext.Provider value={{ user, token, loading, error, login, register, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);