import React, { useState, useEffect } from 'react';

/**
 * A component to display a student's live performance data.
 * It fetches data from the backend periodically.
 * @param {object} props - The component props.
 * @param {string} props.userId - The ID of the student to fetch performance for.
 */
function PerformancePanel({ classId, userId, compact = false, variant = 'default', activeExample = null }) {
    
    const [performance, setPerformance] = useState(null); // special in memory function (in this case, set performance) that allows you to store data in performance
    const [performanceError, setPerformanceError] = useState('');
    const [objectivesError, setObjectivesError] = useState('');
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
    const isStudentSidebar = variant === 'student-sidebar';
    const objectiveMasteryPct = objectiveScores.length
        ? Math.round((masteredObjectiveCount / objectiveScores.length) * 100)
        : 0;
    const examplePerformance = performance?.example_performance;
    const examplesCorrectPct = examplePerformance?.assigned_count
        ? Math.round((examplePerformance.correct_count / examplePerformance.assigned_count) * 100)
        : 0;
    const examplesAttemptedPct = examplePerformance?.assigned_count
        ? Math.round((examplePerformance.attempted_count / examplePerformance.assigned_count) * 100)
        : 0;

    const panelClassName = `performance-panel ${isStudentSidebar ? 'student-progress-panel' : ''}`;

    const renderStatusBar = (label, pct, helperText, fill = 'var(--success)') => (
        <div className="performance-status-bar">
            <div className="performance-status-label">
                <span>{label}</span>
                <span>{pct}%</span>
            </div>
            <div className="performance-progress-track">
                <div
                    className="performance-progress-fill"
                    style={{ width: `${pct}%`, backgroundColor: fill }}
                />
            </div>
            {helperText && (
                <div className="performance-helper-text">{helperText}</div>
            )}
        </div>
    );

    useEffect(() => { // useEffect tells react what to run-post render, this is literally just saying do an API call
        const fetchPerformance = async () => {
            try {
                const query = classId ? `?class_id=${encodeURIComponent(classId)}` : '';
                const response = await fetch(
                    isStudentSidebar ? `/api/me/performance${query}` : `/api/performance/${userId}${query}`
                );
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Could not fetch performance data.');
                }
                const data = await response.json();
                setPerformance(data);
                setPerformanceError('');
            } catch (err) {
                console.error("Performance fetch error:", err);
                setPerformanceError('Failed to load performance. No assessments may be available yet.');
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
                setObjectivesError('');
            } catch (err) {
                console.error("Performance fetch error:", err);
                setObjectivesError('Failed to load objectives.');
                setObjectives([]);
            }
        };
        fetchObjectives();
    }, [classId]); // and this is saying do it everytime the classId changes
return (
    <div className={panelClassName}>
            <h4>
                {isStudentSidebar ? 'Learning Progress' : userId}
            </h4>
            
            {performanceError && !isStudentSidebar && <p style={{ color: 'var(--danger)' }}>{performanceError}</p>}
            {objectivesError && <p style={{ color: 'var(--danger)' }}>{objectivesError}</p>}
            
            {!performance && !performanceError && <p>Loading performance data...</p>}

            {performance && compact && !isStudentSidebar && (
                <div>
                    <h5>Status:</h5>
                    {renderStatusBar(
                        'Learning objectives',
                        objectiveMasteryPct,
                        `${masteredObjectiveCount} of ${objectiveScores.length} mastered`
                    )}
                    {examplePerformance && renderStatusBar(
                        'Examples correct',
                        examplesCorrectPct,
                        `${examplePerformance.correct_count} of ${examplePerformance.assigned_count} correct`
                    )}
                    {examplePerformance && renderStatusBar(
                        'Examples attempted',
                        examplesAttemptedPct,
                        `${examplePerformance.attempted_count} attempted`,
                        'var(--primary)'
                    )}
                </div>
            )}

            {isStudentSidebar && (
                <div className="student-objectives-summary">
                    <h5>Learning Objectives</h5>
                    {objectiveScores.length > 0 ? (
                        <>
                            <p className="student-objectives-count">
                                {masteredObjectiveCount} / {objectiveScores.length} mastered
                            </p>
                        <ul className="student-objective-list">
                            {objectiveScores.map(({ objectiveText, pct }) => (
                                <li key={objectiveText}>
                                    <div className="student-objective-row">
                                        <span>{objectiveText}</span>
                                        <strong>{pct}%</strong>
                                    </div>
                                    <div className="performance-progress-track">
                                        <div
                                            className="performance-progress-fill"
                                            style={{ width: `${pct}%` }}
                                        />
                                    </div>
                                </li>
                            ))}
                        </ul>
                        </>
                    ) : (
                        <p className="student-progress-muted">
                            No learning objectives found for this class.
                        </p>
                    )}
                </div>
            )}

            {performance && assessment && !compact && !isStudentSidebar && (
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
                                    backgroundColor: 'var(--secondary-soft)',
                                    borderRadius: '5px',
                                    marginTop: '4px'
                                }}>
                                    {/* The inner "fill" of the bar */}
                                    <div style={{
                                        height: '100%',
                                        width: `${pct}%`,
                                        backgroundColor: 'var(--success)',
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
                        <p style={{ marginTop: '10px', color: 'var(--success)' }}>
                            All objectives mastered.
                        </p>
                    )}
                </div>
            )}
            {performance && examplePerformance && !compact && (
                <div className="student-practice-summary">
                    <h5>{isStudentSidebar ? 'Practice Summary:' : 'Example Problems:'}</h5>
                    <p>
                        {examplePerformance.correct_count} / {examplePerformance.assigned_count} correct
                    </p>
                    <p className="student-progress-muted">
                        {examplePerformance.attempted_count} attempted
                    </p>
                    {isStudentSidebar && (
                        <p className={`student-active-example ${activeExample ? 'active' : ''}`}>
                            {activeExample ? 'Active example selected' : 'No active example selected'}
                        </p>
                    )}
                    {!isStudentSidebar && Array.isArray(examplePerformance.examples) && examplePerformance.examples.length > 0 && (
                        <ul style={{ paddingLeft: '0', listStyleType: 'none', margin: '8px 0 0 0' }}>
                            {examplePerformance.examples.map((example) => (
                                <li key={example.example_id} style={{ marginBottom: '8px', fontSize: '13px' }}>
                                    <span>{example.correct ? 'Correct' : example.attempted ? 'Attempted' : 'Not attempted'}</span>
                                    <div style={{ color: 'var(--text-muted)', overflowWrap: 'anywhere' }}>{example.title}</div>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            )}
            {/* This handles cases where the API returns a message like "No assessments found" */}
            {performance && performance.message && !compact && <p>{performance.message}</p>}
        </div>
    );
}

export default PerformancePanel;
