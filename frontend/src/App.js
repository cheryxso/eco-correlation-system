import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import DataUpload from './pages/DataUpload';
import Analysis from './pages/Analysis';
import Reports from './pages/Reports';
import PublicDashboard from './pages/PublicDashboard';
import AdminPanel from './pages/AdminPanel';

const getRoleFromToken = (token) => {
    if (!token) return 'guest';

    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload?.role || 'guest';
    } catch (error) {
        return 'guest';
    }
};

const hasAccess = (role, allowedRoles) => {
    if (role === 'admin') return true;
    return allowedRoles.includes(role);
};

const PrivateRoute = ({ children, allowedRoles }) => {
    const { token } = useAuth();

    if (!token) {
        return <Navigate to="/login" replace />;
    }

    const role = getRoleFromToken(token);

    if (allowedRoles && !hasAccess(role, allowedRoles)) {
        return <Navigate to="/dashboard" replace />;
    }

    return children;
};

const AppRoutes = () => {
    return (
        <>
            <Navbar />
            <Routes>
                <Route path="/" element={<PublicDashboard />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />

                <Route path="/dashboard" element={
                    <PrivateRoute allowedRoles={['analyst', 'lpr', 'admin']}>
                        <Dashboard />
                    </PrivateRoute>
                } />

                <Route path="/upload" element={
                    <PrivateRoute allowedRoles={['analyst', 'admin']}>
                        <DataUpload />
                    </PrivateRoute>
                } />

                <Route path="/analysis" element={
                    <PrivateRoute allowedRoles={['analyst', 'admin']}>
                        <Analysis />
                    </PrivateRoute>
                } />

                <Route path="/reports" element={
                    <PrivateRoute allowedRoles={['analyst', 'lpr', 'admin']}>
                        <Reports />
                    </PrivateRoute>
                } />

                <Route path="/admin" element={
                    <PrivateRoute allowedRoles={['admin']}>
                        <AdminPanel />
                    </PrivateRoute>
                } />

                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </>
    );
};

function App() {
    return (
        <AuthProvider>
            <Router>
                <AppRoutes />
            </Router>
        </AuthProvider>
    );
}

export default App;