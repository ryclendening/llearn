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

    const roleLabel = user.role.charAt(0).toUpperCase() + user.role.slice(1);
    const classActionLabel = user.role === 'teacher' ? 'Open Dashboard' : 'Start Session';

    return (
        <main className="homepage-container">
            <section className="homepage-shell">
                <header className="homepage-header">
                    <div>
                        <span className="role-badge">{roleLabel}</span>
                        <h1 className="homepage-title">Welcome, {user.display_name}</h1>
                    </div>
                    <button type="button" className="secondary-action-button" onClick={logout}>Log out</button>
                </header>

            {import.meta.env.DEV && (
                <section className="dev-role-card" aria-label="Development role switcher">
                    <strong>Development role</strong>
                    <div className="dev-role-actions">
                        <button type="button" onClick={() => switchDevelopmentRole('student')}>Student</button>
                        <button type="button" onClick={() => switchDevelopmentRole('teacher')}>Teacher</button>
                        <button type="button" onClick={() => switchDevelopmentRole('admin')}>Admin</button>
                    </div>
                </section>
            )}

                {user.role === 'admin' && (
                    <section className="homepage-card">
                        <div>
                            <h2>Administration</h2>
                            <p>Review teacher access requests and manage approved teacher accounts.</p>
                        </div>
                        <button type="button" className="primary-action-button" onClick={() => navigate('/admin')}>Manage Teacher Requests</button>
                    </section>
                )}

                {user.role === 'teacher' && (
                    <section className="homepage-card">
                        <div>
                            <h2>Teacher Workspace</h2>
                            <p>Create goals, review classes, and prepare materials for student practice.</p>
                        </div>
                        <button type="button" className="primary-action-button" onClick={() => navigate('/create-objectives')}>Manage Class Setup</button>
                    </section>
                )}

                {user.role === 'student' && (
                    <section className="homepage-card">
                        <div>
                            <h2>Join A Class</h2>
                            <p>Enter a class code from your teacher to start learning.</p>
                        </div>
                        <form onSubmit={joinClass} className="join-form">
                            <input
                                value={classCode}
                                onChange={(event) => setClassCode(event.target.value)}
                                placeholder="Enter Class Code"
                                className="class-code-input"
                                required
                            />
                            <button type="submit" className="primary-action-button">Join Class</button>
                        </form>
                        {error && <p className="error-message">{error}</p>}
                        <button type="button" className="secondary-action-button" onClick={requestTeacherAccess} disabled={user.teacher_request_status === 'pending'}>
                            {user.teacher_request_status === 'pending' ? 'Teacher Access Pending' : 'Request Teacher Access'}
                        </button>
                    </section>
                )}

                {user.role !== 'admin' && (
                    <section className="homepage-card classes-card">
                        <div className="classes-header">
                            <div>
                                <h2>Your Classes</h2>
                                <p>{classes.length === 0 ? 'No classes yet.' : `${classes.length} active class${classes.length === 1 ? '' : 'es'}.`}</p>
                            </div>
                        </div>

                        {classes.length === 0 ? (
                            <p className="empty-classes-message">
                                {user.role === 'teacher'
                                    ? 'Create a class in the teacher workspace to see it here.'
                                    : 'Join a class to see it here.'}
                            </p>
                        ) : (
                            <div className="class-card-list">
                                {classes.map(([id, details]) => (
                                    <button
                                        key={id}
                                        type="button"
                                        className="class-card-button"
                                        onClick={() => navigate(user.role === 'teacher' ? `/dashboard/${id}` : `/chat/${id}`)}
                                    >
                                        <span>
                                            <strong>{details.title}</strong>
                                            <small>{id}</small>
                                        </span>
                                        <em>{classActionLabel}</em>
                                    </button>
                                ))}
                            </div>
                        )}
                    </section>
                )}
            </section>
        </main>
    );
}

export default HomePage;
