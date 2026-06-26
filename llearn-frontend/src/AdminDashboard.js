import React, { useEffect, useState } from 'react';
import { useAuth } from './AuthContext';

function AdminDashboard() {
    const { logout } = useAuth();
    const [requests, setRequests] = useState([]);
    const [error, setError] = useState('');

    const loadRequests = async () => {
        const response = await fetch('/api/admin/teacher-access-requests');
        const data = await response.json();
        if (!response.ok) {
            setError(data.detail || 'Failed to load teacher requests.');
            return;
        }
        setRequests(data.requests || []);
    };

    useEffect(() => { loadRequests(); }, []);

    const review = async (id, decision) => {
        const response = await fetch(`/api/admin/teacher-access-requests/${id}/${decision}`, { method: 'POST' });
        if (response.ok) await loadRequests();
    };

    const revoke = async (userId) => {
        const response = await fetch(`/api/admin/teachers/${userId}/revoke`, { method: 'POST' });
        if (response.ok) await loadRequests();
    };

    return (
        <main>
            <button type="button" onClick={logout}>Log out</button>
            <h1>Teacher Access Requests</h1>
            {error && <p>{error}</p>}
            {requests.map((request) => (
                <section key={request.id}>
                    <strong>{request.user.display_name}</strong> ({request.user.email}) - {request.status}
                    {request.status === 'pending' && <>
                        <button type="button" onClick={() => review(request.id, 'approve')}>Approve</button>
                        <button type="button" onClick={() => review(request.id, 'reject')}>Reject</button>
                    </>}
                    {request.status === 'approved' && request.user.role === 'teacher' && (
                        <button type="button" onClick={() => revoke(request.user.id)}>Revoke Teacher</button>
                    )}
                </section>
            ))}
        </main>
    );
}

export default AdminDashboard;
