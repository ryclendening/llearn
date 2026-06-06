import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import './HomePage.css';

function HomePage() {
    const { user, refresh, logout } = useAuth();
    const [classCode, setClassCode] = useState('');
    const [classes, setClasses] = useState([]);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const loadClasses = async () => {
        if (user.role === 'admin') return;
        const response = await fetch('/api/learning-objectives');
        if (response.ok) setClasses(Object.entries(await response.json()));
    };

    useEffect(() => { loadClasses(); }, [user.role]);

    const joinClass = async (event) => {
        event.preventDefault();
        const response = await fetch('/api/classes/join', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ class_id: classCode }),
        });
        const data = await response.json();
        if (!response.ok) {
            setError(data.detail || 'Failed to join class.');
            return;
        }
        await loadClasses();
        navigate(`/chat/${encodeURIComponent(classCode)}`);
    };

    const requestTeacherAccess = async () => {
        const response = await fetch('/api/teacher-access-requests', { method: 'POST' });
        if (response.ok) await refresh();
    };

    const switchDevelopmentRole = async (role) => {
        const response = await fetch('/api/auth/dev-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: user.email, display_name: user.display_name, role }),
        });
        const data = await response.json();
        if (!response.ok) {
            setError(data.detail || 'Could not switch development role.');
            return;
        }
        await refresh();
    };

    return (
        <main className="homepage-container">
            <button type="button" onClick={logout}>Log out</button>
            <h1 className="homepage-title">Welcome, {user.display_name}</h1>
            <p>{user.role}</p>
            {import.meta.env.DEV && (
                <section>
                    <strong>Development role:</strong>
                    <button type="button" onClick={() => switchDevelopmentRole('student')}>Act as student</button>
                    <button type="button" onClick={() => switchDevelopmentRole('teacher')}>Act as teacher</button>
                    <button type="button" onClick={() => switchDevelopmentRole('admin')}>Act as admin</button>
                </section>
            )}

            {user.role === 'admin' && <button type="button" onClick={() => navigate('/admin')}>Manage Teacher Requests</button>}

            {user.role === 'teacher' && <>
                <button type="button" onClick={() => navigate('/create-objectives')}>Manage Classes And Materials</button>
                <h2>Your Classes</h2>
            </>}

            {user.role === 'student' && <>
                <form onSubmit={joinClass} className="join-form">
                    <input value={classCode} onChange={(event) => setClassCode(event.target.value)} placeholder="Enter Class Code" required />
                    <button type="submit">Join Class</button>
                </form>
                {error && <p className="error-message">{error}</p>}
                <button type="button" onClick={requestTeacherAccess} disabled={user.teacher_request_status === 'pending'}>
                    {user.teacher_request_status === 'pending' ? 'Teacher Access Pending' : 'Request Teacher Access'}
                </button>
                <h2>Your Classes</h2>
            </>}

            {classes.map(([id, details]) => (
                <button
                    key={id}
                    type="button"
                    onClick={() => navigate(user.role === 'teacher' ? `/dashboard/${id}` : `/chat/${id}`)}
                >
                    {details.title} ({id})
                </button>
            ))}
        </main>
    );
}

export default HomePage;
