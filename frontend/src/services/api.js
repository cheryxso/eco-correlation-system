import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Авторизація
export const register = (data) => api.post('/auth/register', data);
export const login = (data) => api.post('/auth/login', data);
export const getMe = (token) => api.get('/auth/me', { params: { token } });

// Території
export const getTerritories = () => api.get('/territories/');
export const createTerritory = (data) => api.post('/territories/', data);

// Екологічні дані
export const uploadEcoCSV = (territoryId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/ecological/upload/${territoryId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
};
export const fetchOpenAQ = (territoryId, city) =>
    api.post(`/ecological/fetch-openaq/${territoryId}`, null, { params: { city } });
export const fetchSaveEcoBot = (territoryId, city) =>
    api.post(`/ecological/fetch-saveecobot/${territoryId}`, null, { params: { city } });

// Економічні дані
export const uploadEconCSV = (territoryId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/economic/upload/${territoryId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
};

// Аналіз
export const runCorrelation = (data) => api.post('/analysis/correlation', data);
export const runPartialCorrelation = (data) => api.post('/analysis/partial-correlation', data);
export const runTimeSeries = (data) => api.post('/analysis/timeseries', data);
export const runRegression = (data) => api.post('/analysis/regression', data);
export const runComparison = (data) => api.post('/analysis/comparison', data);

// Звіти
export const generateReport = (data) => api.post('/reports/generate', data, {
    responseType: 'blob'
});

// Публічні endpoint-и (без авторизації)
export const getPublicStats = () => api.get('/territories/public/stats');