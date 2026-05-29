import React, { useState, useEffect } from 'react';

/**
 * A component to display a student's live performance data.
 * It fetches data from the backend periodically.
 * @param {object} props - The component props.
 * @param {string} props.userId - The ID of the student to fetch performance for.
 */
function PerformancePanel({ classId, userId, compact = false }) {
    
    const [performance, setPerformance] = useState(null); // special in memory function (in this case, set performance) that allows you to store data in performance
    const [error, setError] = useState('');
    const [lesson_objectives, setObjectives] = useState([])

    const normalizeScoreToPercent = (score) => {
        // Backend has historically returned objective scores in a few shapes:
        // - 0/1
        // - boolean
        // - 0..1
        // - 0..100
        if (score === true) return 100;
        if (score === false) return 0;
        const n = Number(score);
        if (!Number.isFinite(n)) return 0;
        if (n <= 1 && n >= 0) return Math.round(n * 100);
        return Math.max(0, Math.min(100, Math.round(n)));
    };

    const assessment =
        (performance && (performance.parsed_message || performance.assessment)) ||
        null;
    const objectiveScores = (Array.isArray(lesson_objectives) ? lesson_objectives : []).map((objectiveText, index) => {
        const scoreKey = `objective_${index + 1}`;
        const score = assessment?.[scoreKey];
        return {
            objectiveText,
            pct: normalizeScoreToPercent(score),
        };
    });
    const masteredObjectiveCount = objectiveScores.filter((item) => item.pct >= 100).length;

    useEffect(() => { // useEffect tells react what to run-post render, this is literally just saying do an API call
        const fetchPerformance = async () => {
            try {
                const query = classId ? `?class_id=${encodeURIComponent(classId)}` : '';
                const response = await fetch(`/api/performance/${userId}${query}`);
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
        const intervalId = setInterval(fetchPerformance, 10000);
        return () => clearInterval(intervalId);
    }, [userId, classId]); // and this is saying do it everytime the userId changes

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
                const objectives = data?.[classId]?.objectives;
                setObjectives(Array.isArray(objectives) ? objectives : []);
                setError('');
            } catch (err) {
                console.error("Performance fetch error:", err);
                setError('Failed to load objectives. No assessments may be available yet.');
                setObjectives([]);
            }
        };
        fetchObjectives();
    }, [classId]); // and this is saying do it everytime the classId changes




return (
    <div style={{
        border: '1px solid #ddd',
        padding: '12px 16px',
        borderRadius: '10px',
        backgroundColor: '#ffffff',
        boxShadow: '0 2px 6px rgba(0, 0, 0, 0.05)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-start',
    }}>
            <h4 style={{ marginTop: 0, borderBottom: '2px solid #eee', paddingBottom: '10px' }}>{userId}</h4>
            
            {error && <p style={{ color: '#d32f2f' }}>{error}</p>}
            
            {!performance && !error && <p>Loading performance data...</p>}

            {performance && assessment && compact && (
                <div>
                    <h5>Learning Objectives:</h5>
                    <p style={{ margin: '6px 0', fontSize: '14px' }}>
                        {masteredObjectiveCount} / {objectiveScores.length} mastered
                    </p>
                </div>
            )}

            {performance && assessment && !compact && (
                <div>
                    <h5>Objective Scores:</h5>
                    <ul style={{paddingLeft: '0', listStyleType: 'none',margin: '0', paddingTop:'8px'}}>
                        {/* 4. Map over the objectives array from state. */}
                        {objectiveScores.map(({ objectiveText, pct }) => { // map just allows you to set variables that iterate over the array and do the function below
                            return(
                            <li key={objectiveText} style={{ marginBottom: '12px', fontSize:'14px'}}>
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
                                        width: `${pct}%`,
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
                    {performance.mastered === true && (
                        <p style={{ marginTop: '10px', color: '#2e7d32' }}>
                            All objectives mastered.
                        </p>
                    )}
                </div>
            )}
            {performance && performance.example_performance && (
                <div style={{ marginTop: '14px', borderTop: '2px solid #eee', paddingTop: '10px' }}>
                    <h5>Example Problems:</h5>
                    <p style={{ margin: '6px 0', fontSize: '14px' }}>
                        {performance.example_performance.correct_count} / {performance.example_performance.assigned_count} correct
                    </p>
                    <p style={{ margin: '6px 0', fontSize: '13px', color: '#586273' }}>
                        {performance.example_performance.attempted_count} attempted
                    </p>
                    {Array.isArray(performance.example_performance.examples) && performance.example_performance.examples.length > 0 && (
                        <ul style={{ paddingLeft: '0', listStyleType: 'none', margin: '8px 0 0 0' }}>
                            {performance.example_performance.examples.map((example) => (
                                <li key={example.example_id} style={{ marginBottom: '8px', fontSize: '13px' }}>
                                    <span>{example.correct ? 'Correct' : example.attempted ? 'Attempted' : 'Not attempted'}</span>
                                    <div style={{ color: '#586273', overflowWrap: 'anywhere' }}>{example.title}</div>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            )}
            {/* This handles cases where the API returns a message like "No assessments found" */}
            {performance && performance.message && <p>{performance.message}</p>}
        </div>
    );
}

export default PerformancePanel;
