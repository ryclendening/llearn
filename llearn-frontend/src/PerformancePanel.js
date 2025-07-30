import React, { useState, useEffect } from 'react';

/**
 * A component to display a student's live performance data.
 * It fetches data from the backend periodically.
 * @param {object} props - The component props.
 * @param {string} props.userId - The ID of the student to fetch performance for.
 */
function PerformancePanel({ classId,userId }) {
    
    const [performance, setPerformance] = useState(null); // special in memory function (in this case, set performance) that allows you to store data in performance
    const [error, setError] = useState('');
    const [lesson_objectives, setObjectives] = useState([])
    useEffect(() => { // useEffect tells react what to run-post render, this is literally just saying do an API call
        const fetchPerformance = async () => {
            try {
                const response = await fetch(`/api/performance/${userId}`);
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Could not fetch performance data.');
                }
                const data = await response.json();
                console.log(data)
                setPerformance(data);
                setError('');
            } catch (err) {
                console.error("Performance fetch error:", err);
                setError('Failed to load performance. No assessments may be available yet.');
                setPerformance(null);
            }
        };
        fetchPerformance();
        const intervalId = setInterval(fetchPerformance, 5000);
        return () => clearInterval(intervalId);
    }, [userId]); // and this is saying do it everytime the userId changes

    useEffect(() => { // useEffect tells react what to run-post render, this is literally just saying do an API call
        const fetchObjectives = async () => {

            if (!classId) return;

            try {
                const response = await fetch(`/api/learning-objectives`);
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Could not fetch objectives data.');
                }
                const data = await response.json();
                setObjectives(data[classId].objectives);
                setError('');
            } catch (err) {
                console.error("Performance fetch error:", err);
                setError('Failed to load objectives. No assessments may be available yet.');
                setObjectives(null);
            }
        };
        fetchObjectives();
    }, [classId]); // and this is saying do it everytime the userId changes




    return (
        <div style={{
            border: '1px solid #e0e0e0',
            padding: '20px',
            marginLeft: '20px',
            width: '350px',
            borderRadius: '8px',
            backgroundColor: '#f9f9f9'
        }}>
            <h4 style={{ marginTop: 0, borderBottom: '2px solid #eee', paddingBottom: '10px' }}>Live Performance</h4>
            
            {error && <p style={{ color: '#d32f2f' }}>{error}</p>}
            
            {!performance && !error && <p>Loading performance data...</p>}

            {performance && performance.parsed_message && (
                <div>
                    <h5>Objective Scores:</h5>
                    <ul style={{paddingLeft: '0', listStyleType: 'none'}}>
                        {/* 4. Map over the objectives array from state. */}
                        {lesson_objectives.map((objectiveText, index) => { // map just allows you to set variables that iterate over the array and do the function below
                            const scoreKey = `objective_${index + 1}`;
                            const score = performance.parsed_message[scoreKey];
                            return(
                            <li key={objectiveText} style={{ marginBottom: '12px' }}>
                                <span style={{ textTransform: 'capitalize' }}>{objectiveText}</span>
                                {/* The outer container for the bar */}
                                <div style={{
                                    height: '20px',
                                    width: '100%',
                                    backgroundColor: '#e9ecef',
                                    borderRadius: '5px',
                                    marginTop: '4px'
                                }}>
                                    {/* The inner "fill" of the bar */}
                                    <div style={{
                                        height: '100%',
                                        // This is the key: width is 100% if score is 1, otherwise 0%
                                        width: score === 1 ? '100%' : '0%',
                                        backgroundColor: '#28a745', // Green for "complete"
                                        borderRadius: '5px',
                                        // A smooth transition effect for the fill
                                        transition: 'width 0.5s ease-in-out'
                                    }}>
                                    </div>
                                </div>
                            </li>
                        )})}
                    </ul>
                </div>
            )}
            {/* This handles cases where the API returns a message like "No assessments found" */}
            {performance && performance.message && <p>{performance.message}</p>}
        </div>
    );
}

export default PerformancePanel;
