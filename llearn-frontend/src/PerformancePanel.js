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

    const renderStatusBar = (label, pct, helperText, fill = 'var(--success)') => (
        <div style={{ marginBottom: '12px' }}>
            <div style={{ alignItems: 'center', display: 'flex', justifyContent: 'space-between', gap: '10px' }}>
                <span style={{ fontSize: '13px', fontWeight: 700 }}>{label}</span>
                <span style={{ color: 'var(--text-muted)', fontSize: '12px', whiteSpace: 'nowrap' }}>{pct}%</span>
            </div>
            <div style={{
                height: '10px',
                width: '100%',
                backgroundColor: 'var(--secondary-soft)',
                borderRadius: '999px',
                marginTop: '5px',
                overflow: 'hidden',
            }}>
                <div style={{
                    height: '100%',
                    width: `${pct}%`,
                    backgroundColor: fill,
                    borderRadius: '999px',
                    transition: 'width 0.5s ease-in-out',
                }} />
            </div>
            {helperText && (
                <div style={{ color: 'var(--text-muted)', fontSize: '12px', marginTop: '4px' }}>
                    {helperText}
                </div>
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
                console.log(data)
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
    <div style={{
        border: '1px solid var(--border)',
        padding: '12px 16px',
        borderRadius: 'var(--radius)',
        backgroundColor: 'var(--surface)',
        boxShadow: 'var(--shadow-subtle)',
        color: 'var(--text)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-start',
    }}>
            <h4 style={{ marginTop: 0, borderBottom: '2px solid var(--border)', paddingBottom: '10px', color: 'var(--secondary)' }}>
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
                <div>
                    <h5>Learning Objectives:</h5>
                    {objectiveScores.length > 0 ? (
                        <>
                            <p style={{ margin: '6px 0', fontSize: '14px' }}>
                                {masteredObjectiveCount} / {objectiveScores.length} mastered
                            </p>
                        <ul style={{paddingLeft: '0', listStyleType: 'none', margin: '8px 0 0 0'}}>
                            {objectiveScores.map(({ objectiveText, pct }) => (
                                <li key={objectiveText} style={{ marginBottom: '10px', fontSize: '13px' }}>
                                    <span style={{ display: 'block', overflowWrap: 'anywhere' }}>{objectiveText}</span>
                                    <div style={{
                                        height: '10px',
                                        width: '100%',
                                        backgroundColor: 'var(--secondary-soft)',
                                        borderRadius: '999px',
                                        marginTop: '4px'
                                    }}>
                                        <div style={{
                                            height: '100%',
                                            width: `${pct}%`,
                                            backgroundColor: 'var(--success)',
                                            borderRadius: '999px',
                                            transition: 'width 0.5s ease-in-out'
                                        }} />
                                    </div>
                                </li>
                            ))}
                        </ul>
                        </>
                    ) : (
                        <p style={{ margin: '6px 0', fontSize: '13px', color: 'var(--text-muted)' }}>
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
                <div style={{ marginTop: '14px', borderTop: '2px solid var(--border)', paddingTop: '10px' }}>
                    <h5>{isStudentSidebar ? 'Practice Summary:' : 'Example Problems:'}</h5>
                    <p style={{ margin: '6px 0', fontSize: '14px' }}>
                        {examplePerformance.correct_count} / {examplePerformance.assigned_count} correct
                    </p>
                    <p style={{ margin: '6px 0', fontSize: '13px', color: 'var(--text-muted)' }}>
                        {examplePerformance.attempted_count} attempted
                    </p>
                    {isStudentSidebar && (
                        <p style={{ margin: '8px 0 0 0', fontSize: '13px', color: activeExample ? 'var(--primary)' : 'var(--text-muted)' }}>
                            {activeExample ? 'Active example selected' : 'No active example'}
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
