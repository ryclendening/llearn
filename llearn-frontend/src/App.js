import React from 'react';
import { BrowserRouter as Router, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import AdminDashboard from './AdminDashboard';
import ChatPage from './ChatPage';
import ClassPerformanceDashboard from './ClassPerformanceDashboard';
import HomePage from './HomePage';
import LearningObjectivesForm from './LearningObjectivesForm';
import Login from './login';
import ThemeToggle from './ThemeToggle';

function ProtectedRoute({ roles, children }) {
    const { user, loading } = useAuth();
    if (loading) return <p>Loading...</p>;
    if (!user) return <Navigate to="/login" replace />;
    if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;
    return children;
}

function AppRoutes() {
    return (
        <Router>
            <ThemeToggle />
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/" element={<ProtectedRoute roles={['student', 'teacher', 'admin']}><HomePage /></ProtectedRoute>} />
                <Route path="/chat/:classId" element={<ProtectedRoute roles={['student']}><ChatPage /></ProtectedRoute>} />
                <Route path="/dashboard/:classId" element={<ProtectedRoute roles={['teacher']}><ClassPerformanceDashboard /></ProtectedRoute>} />
                <Route path="/create-objectives" element={<ProtectedRoute roles={['teacher']}><LearningObjectivesForm /></ProtectedRoute>} />
                <Route path="/admin" element={<ProtectedRoute roles={['admin']}><AdminDashboard /></ProtectedRoute>} />
            </Routes>
        </Router>
    );
}

function App() {
    return <AuthProvider><AppRoutes /></AuthProvider>;
}

export default App;
