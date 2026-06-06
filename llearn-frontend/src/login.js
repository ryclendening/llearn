import React, { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';

function Login() {
    const { user, refresh } = useAuth();
    const [email, setEmail] = useState('');
    const [role, setRole] = useState('student');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    if (user) {
        return <Navigate to={user.role === 'admin' ? '/admin' : '/'} replace />;
    }

    const devLogin = async (event) => {
        event.preventDefault();
        const response = await fetch('/api/auth/dev-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, role }),
        });
        if (!response.ok) {
            const data = await response.json();
            setError(data.detail || 'Development login failed.');
            return;
        }
        const nextUser = await refresh();
        navigate(nextUser?.role === 'admin' ? '/admin' : '/', { replace: true });
    };

    return (
        <div className="login-container">
            <h1>Sign in to lLearn</h1>
            <a href="/api/auth/login"><button type="button">Continue with Google</button></a>
            {import.meta.env.DEV && (
                <form onSubmit={devLogin}>
                    <h2>Development Login</h2>
                    <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email" required />
                    <label htmlFor="devRole">Act as:</label>
                    <select id="devRole" value={role} onChange={(event) => setRole(event.target.value)}>
                        <option value="student">Student</option>
                        <option value="teacher">Teacher</option>
                        <option value="admin">Admin</option>
                    </select>
                    <button type="submit">Sign in locally as {role}</button>
                    {error && <p className="error-message">{error}</p>}
                </form>
            )}
        </div>
    );
}

export default Login;
