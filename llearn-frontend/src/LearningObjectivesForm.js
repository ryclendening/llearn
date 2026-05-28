import React, { useState } from 'react';
import './LearningObjectivesForm.css';

function LearningObjectivesForm() {
    const [lessonId, setLessonId] = useState('');
    const [title, setTitle] = useState('');
    const [objectives, setObjectives] = useState(['']);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');

    // ── Generator state ──────────────────────────────────────────────────────
    const [genAge, setGenAge] = useState('');
    const [genGenre, setGenGenre] = useState('');
    const [genLoading, setGenLoading] = useState(false);
    const [genError, setGenError] = useState('');
    const [generatedPlan, setGeneratedPlan] = useState(null);

    const handleLessonIdChange = (e) => { setLessonId(e.target.value); setError(''); setSuccessMessage(''); };
    const handleTitleChange = (e) => { setTitle(e.target.value); setError(''); setSuccessMessage(''); };
    const handleObjectiveChange = (index, e) => {
        const newObjectives = [...objectives];
        newObjectives[index] = e.target.value;
        setObjectives(newObjectives);
        setError(''); setSuccessMessage('');
    };
    const addObjectiveField = () => setObjectives([...objectives, '']);
    const removeObjectiveField = (index) => setObjectives(objectives.filter((_, i) => i !== index));

    // ── Generate objectives from AI ──────────────────────────────────────────
    const handleGenerate = async () => {
        if (!genAge || !genGenre.trim()) {
            setGenError('Please enter both age and genre.');
            return;
        }
        setGenLoading(true);
        setGenError('');
        setGeneratedPlan(null);
        try {
            const response = await fetch(`/api/generate-objectives?age=${genAge}&genre=${encodeURIComponent(genGenre)}`);
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to generate objectives.');
            }
            const data = await response.json();
            console.log("API response:", data);
            console.log("objectives:", data.objectives);
            console.log("type:", typeof data);
            setGeneratedPlan(data);
        } catch (err) {
            setGenError(err.message || 'An unexpected error occurred.');
        } finally {
            setGenLoading(false);
        }
    };

    // ── Apply generated plan to the form ─────────────────────────────────────
    const applyGeneratedPlan = () => {
        setLessonId(generatedPlan.lesson_id);
        setTitle(generatedPlan.title);
        setObjectives(generatedPlan.objectives);
        setGeneratedPlan(null);
        setGenAge('');
        setGenGenre('');
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!lessonId.trim() || !title.trim()) { setError('Lesson ID and Title cannot be empty.'); return; }
        const filteredObjectives = objectives.filter(obj => obj.trim() !== '');
        if (filteredObjectives.length === 0) { setError('Please add at least one learning objective.'); return; }

        setLoading(true); setError(''); setSuccessMessage('');
        const payload = { lesson_id: lessonId.trim(), title: title.trim(), objectives: filteredObjectives };
        const assessor_payload = { class_id: lessonId.trim() };

        try {
            const response = await fetch('/api/learning-objectives', {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
            });
            if (!response.ok) { const errorData = await response.json(); throw new Error(errorData.detail || 'Failed to submit learning objectives.'); }
            setSuccessMessage('Learning objectives submitted successfully!');
            setLessonId(''); setTitle(''); setObjectives(['']);
        } catch (err) {
            setError(err.message || 'An unexpected error occurred.');
        } finally { setLoading(false); }

        try {
            const response = await fetch('/api/create-assessor', {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(assessor_payload),
            });
            if (!response.ok) { const errorData = await response.json(); throw new Error(errorData.detail || 'Failed to create assessor.'); }
            setSuccessMessage('Assessor created successfully!');
        } catch (err) {
            setError(err.message || 'An unexpected error occurred.');
        } finally { setLoading(false); }
    };

    return (
        <div className="objectives-page-container">
            <h1 className="objectives-page-title">Create Learning Objectives</h1>

            {/* ── AI Generator Section ── */}
            <div className="objectives-form-card" style={{ marginBottom: '1.5rem' }}>
                <h2 style={{ marginBottom: '1rem' }}>Generate with AI</h2>
                <div className="form-group">
                    <label>Student Age:</label>
                    <input
                        type="number" value={genAge} onChange={e => setGenAge(e.target.value)}
                        placeholder="e.g., 10" className="form-input"
                    />
                </div>
                <div className="form-group">
                    <label>Topic / Genre:</label>
                    <input
                        type="text" value={genGenre} onChange={e => setGenGenre(e.target.value)}
                        placeholder="e.g., planets" className="form-input"
                    />
                </div>
                {genError && <p className="error-message">{genError}</p>}
                <button onClick={handleGenerate} className="submit-button" disabled={genLoading}>
                    {genLoading ? 'Generating...' : 'Generate Objectives'}
                </button>

                {/* ── Preview generated plan ── */}
                {generatedPlan && (
                    <div className="generated-preview">
                        <h3>{generatedPlan.title}</h3>
                        <p className="lesson-id-label">Lesson ID: {generatedPlan.lesson_id}</p>
                        <ul>
                            {generatedPlan.objectives.map((obj, i) => (
                                <li key={i}>{obj}</li>
                            ))}
                        </ul>
                        <div className="preview-actions">
                            <button onClick={applyGeneratedPlan} className="submit-button">Use These Objectives</button>
                            <button onClick={handleGenerate} className="add-objective-button" disabled={genLoading}>
                                {genLoading ? 'Regenerating...' : 'Regenerate'}
                            </button>
                            <button onClick={() => setGeneratedPlan(null)} className="discard-button">Discard</button>
                        </div>
                    </div>
                )}
            </div>

            {/* ── Manual Form ── */}
            <form onSubmit={handleSubmit} className="objectives-form-card">
                <div className="form-group">
                    <label htmlFor="lessonId">Lesson ID:</label>
                    <input type="text" id="lessonId" value={lessonId} onChange={handleLessonIdChange}
                        placeholder="e.g., science101" className="form-input" required />
                </div>
                <div className="form-group">
                    <label htmlFor="title">Title:</label>
                    <input type="text" id="title" value={title} onChange={handleTitleChange}
                        placeholder="e.g., Introduction to Plants" className="form-input" required />
                </div>
                <div className="form-group objectives-group">
                    <label>Learning Objectives:</label>
                    {objectives.map((objective, index) => (
                        <div key={index} className="objective-input-row">
                            <input type="text" value={objective} onChange={(e) => handleObjectiveChange(index, e)}
                                placeholder={`Objective ${index + 1}`} className="form-input objective-input" required />
                            {objectives.length > 1 && (
                                <button type="button" onClick={() => removeObjectiveField(index)} className="remove-objective-button">&times;</button>
                            )}
                        </div>
                    ))}
                    <button type="button" onClick={addObjectiveField} className="add-objective-button">+ Add Objective</button>
                </div>

                {error && <p className="error-message">{error}</p>}
                {successMessage && <p className="success-message">{successMessage}</p>}

                <button type="submit" className="submit-button" disabled={loading}>
                    {loading ? 'Submitting...' : 'Submit Objectives'}
                </button>
            </form>
        </div>
    );
}

export default LearningObjectivesForm;