import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import HomeButton from './HomeButton';
import PerformancePanel from './PerformancePanel';
import './ClassPerformanceDashboard.css'; // Import a dedicated CSS file for the dashboard

function ClassPerformanceDashboard() {
    const { classId } = useParams();
    const [studentIds, setStudentIds] = useState([]);
    const [error, setError] = useState('');
    const [expandedStudentId, setExpandedStudentId] = useState('');
    const [chatLogs, setChatLogs] = useState({});
    const [chatLogLoading, setChatLogLoading] = useState('');
    const [chatLogError, setChatLogError] = useState('');

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

    const toggleStudentDetails = async (userId) => {
        const nextExpandedId = expandedStudentId === userId ? '' : userId;
        setExpandedStudentId(nextExpandedId);
        setChatLogError('');
        if (!nextExpandedId || chatLogs[userId]) {
            return;
        }

        setChatLogLoading(userId);
        try {
            const response = await fetch(`/api/classes/${encodeURIComponent(classId)}/students/${encodeURIComponent(userId)}/chat-logs`);
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Could not fetch chat logs.');
            }
            setChatLogs((currentLogs) => ({ ...currentLogs, [userId]: data.sessions || [] }));
        } catch (err) {
            setChatLogError(err.message || 'Failed to load chat logs.');
        } finally {
            setChatLogLoading('');
        }
    };

    return (
        <div className="dashboard-container"> {/* Use a class for external CSS */}
            <HomeButton />
            <h2 className="dashboard-title"> {/* Use a class for external CSS */}
                🎓 Performance Panels for Class: <span style={{ color: '#00796b' }}>{classId}</span>
            </h2>

            {error && <p style={{ color: 'red', textAlign: 'center' }}>{error}</p>}

            {/* The main grid container */}
            <div className="performance-grid">
                {studentIds.map(userId => (
                    <div
                        key={userId}
                        className={`performance-panel-wrapper ${expandedStudentId === userId ? 'expanded' : ''}`} // Use a class for hover effects
                    >
                        <button
                            type="button"
                            className="student-expand-button"
                            onClick={() => toggleStudentDetails(userId)}
                        >
                            {expandedStudentId === userId ? 'Hide Details' : 'View Details'}
                        </button>
                        <PerformancePanel classId={classId} userId={userId} compact={expandedStudentId !== userId} />
                        {expandedStudentId === userId && (
                            <div className="student-detail-panel">
                                <h3>Chat Logs</h3>
                                {chatLogError && <p className="chat-log-error">{chatLogError}</p>}
                                {chatLogLoading === userId && <p>Loading chat logs...</p>}
                                {chatLogLoading !== userId && (chatLogs[userId] || []).length === 0 && !chatLogError && (
                                    <p>No chat logs yet.</p>
                                )}
                                <div className="chat-log-scroll">
                                    {(chatLogs[userId] || []).map((session) => (
                                        <div key={session.session_id} className="chat-log-session">
                                            <h4>Session {session.session_id}</h4>
                                            {session.messages.map((message) => (
                                                <div key={message.id} className={`chat-log-message ${message.role}`}>
                                                    <strong>{message.role}</strong>
                                                    <p>{message.content}</p>
                                                </div>
                                            ))}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}

export default ClassPerformanceDashboard;
