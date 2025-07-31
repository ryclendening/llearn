import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import PerformancePanel from './PerformancePanel';
import './ClassPerformanceDashboard.css'; // Import a dedicated CSS file for the dashboard

function ClassPerformanceDashboard() {
    const { classId } = useParams();
    const [studentIds, setStudentIds] = useState([]);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchClassRoster = async () => {
            if (!classId) return;

            try {
                const response = await fetch(`/api/get-roster/${classId}`);
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Could not fetch class roster.');
                }
                const data = await response.json();
                setStudentIds(data.roster);
                setError('');
            } catch (err) {
                console.error("Roster fetch error:", err);
                setError('Failed to load class roster.');
                setStudentIds([]);
            }
        };

        fetchClassRoster();
    }, [classId]);

    return (
        <div className="dashboard-container"> {/* Use a class for external CSS */}
            <h2 className="dashboard-title"> {/* Use a class for external CSS */}
                🎓 Performance Panels for Class: <span style={{ color: '#00796b' }}>{classId}</span>
            </h2>

            {error && <p style={{ color: 'red', textAlign: 'center' }}>{error}</p>}

            {/* The main grid container */}
            <div className="performance-grid">
                {studentIds.map(userId => (
                    <div
                        key={userId}
                        className="performance-panel-wrapper" // Use a class for hover effects
                    >
                        <PerformancePanel classId={classId} userId={userId} />
                    </div>
                ))}
            </div>
        </div>
    );
}

export default ClassPerformanceDashboard;