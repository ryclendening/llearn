import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function HomePage() {
    const [classCode, setClassCode] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!classCode.trim()) {
            setError('Class Code cannot be empty.');
            return;
        }

        // Generate a simple unique ID for the user for this session
        const userId = `user_${Date.now()}`;

        try {
            // Step 1: Call your backend to create the student instance
            const response = await fetch('/api/create-student', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, lesson_id: classCode }),
            });

            if (!response.ok) {
                // Handle cases where the class code might be invalid on the backend
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to join the class.');
            }

            // Step 2: Navigate to the chat page on success
            navigate(`/chat/${classCode}/${userId}`);

        } catch (err) {
            console.error("Error joining class:", err);
            setError(err.message);
        }
    };

    return (
        <div style={{ padding: '50px', textAlign: 'center' }}>
            <h1>Join a Class</h1>
            <form onSubmit={handleSubmit}>
                <input
                    type="text"
                    value={classCode}
                    onChange={(e) => setClassCode(e.target.value)}
                    placeholder="Enter Class Code"
                    style={{ padding: '10px', width: '300px', fontSize: '16px' }}
                />
                <button type="submit" style={{ padding: '10px 20px', fontSize: '16px', marginLeft: '10px' }}>
                    Join
                </button>
            </form>
            {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
        </div>
    );
}

export default HomePage;