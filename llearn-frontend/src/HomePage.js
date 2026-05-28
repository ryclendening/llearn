import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './HomePage.css'; // Import the CSS file

function HomePage() {
    const [classCode, setClassCode] = useState('');
    const [error, setError] = useState('');
    const [activeClasses, setActiveClasses] = useState([]); // New state for active classes
    const [showDropdown, setShowDropdown] = useState(false); // State to manage dropdown visibility
    const navigate = useNavigate();

    // Fetch active classes on component mount
    useEffect(() => {
        const fetchActiveClasses = async () => {
            try {
                // Assuming an API endpoint that returns a list of active class IDs
                const response = await fetch('/api/learning-objectives'); // Changed endpoint as per user's provided code
                if (!response.ok) {
                    throw new Error('Failed to fetch active classes.');
                }
                const data = await response.json();
                // Assuming data.active_lessons is an array of class IDs
                setActiveClasses(Object.keys(data) || []); // Changed data key as per user's provided code
                // You can also console.log here for debugging in the console
                console.log('Fetched active classes:', activeClasses);
            } catch (err) {
                console.error("Error fetching active classes:", err);
                // Optionally set an error for the active classes section
            }
        };

        fetchActiveClasses();
        // You might want to refresh this periodically or on certain events
        // const intervalId = setInterval(fetchActiveClasses, 30000); // e.g., every 30 seconds
        // return () => clearInterval(intervalId);
    }, []); // Empty dependency array means this runs once on mount

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!classCode.trim()) {
            setError('Class Code cannot be empty.');
            return;
        }

        const userId = `user_${Date.now()}`;

        try {
            const response = await fetch('/api/create-student', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, lesson_id: classCode }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to join the class.');
            }

            window.open(`/chat/${classCode}/${userId}`, '_blank');

        } catch (err) {
            console.error("Error joining class:", err);
            setError(err.message);
        }
    };

    // Function to handle navigation from dropdown and close it
    const handleNavigate = (path) => {
        navigate(path);
        setShowDropdown(false); // Close dropdown after navigation
    };

    return (
        <div className="homepage-container">
            {/* Dropdown for navigation options */}
            <div className="top-navigation-container">
                <button
                    className="dropdown-toggle-button"
                    onClick={() => setShowDropdown(!showDropdown)}
                >
                    Options <span className="dropdown-arrow">{showDropdown ? '▲' : '▼'}</span>
                </button>
                {showDropdown && (
                    <div className="dropdown-menu">
                        <button
                            onClick={() => handleNavigate('/create-objectives')}
                            className="dropdown-menu-item"
                        >
                            Create New Learning Objectives
                        </button>
                        {/* Add other options here if needed */}
                    </div>
                )}
            </div>

            <h1 className="homepage-title">Join a Class</h1>
            <form onSubmit={handleSubmit} className="join-form">
                <input
                    type="text"
                    value={classCode}
                    onChange={(e) => setClassCode(e.target.value)}
                    placeholder="Enter Class Code"
                    className="class-code-input"
                />
                <button type="submit" className="join-button">
                    Join
                </button>
            </form>
            {error && <p className="error-message">{error}</p>}

            {/* Section for active dashboards */}
            <div className="active-dashboards-section">
                <h2 className="active-dashboards-title">Active Class Dashboards</h2>

                {/* --- DEBUGGING DISPLAY START --- */}
                {/* Temporarily display the raw activeClasses array for debugging */}
                {/* You can uncomment this block to see the array's content */}
                {/* <div style={{ marginTop: '10px', padding: '10px', border: '1px dashed #ccc', backgroundColor: '#f9f9f9', fontSize: '0.8em', wordBreak: 'break-all' }}>
                    <strong>DEBUG: activeClasses:</strong> {JSON.stringify(activeClasses)}
                </div> */}
                {/* --- DEBUGGING DISPLAY END --- */}

                {activeClasses.length > 0 ? (
                    <ul className="active-dashboards-list">
                        {activeClasses.map((classIdItem) => (
                            <li key={classIdItem}>
                                <button
                                    onClick={() => navigate(`/dashboard/${classIdItem}`)}
                                    className="dashboard-link-button"
                                >
                                    Dashboard for: {classIdItem}
                                </button>
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p className="no-dashboards-message">No active dashboards found.</p>
                )}
            </div>
        </div>
    );
}

export default HomePage;
