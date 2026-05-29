import React, { useEffect, useState } from 'react';
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
    const [materialClassId, setMaterialClassId] = useState('');
    const [selectedMaterialClassIds, setSelectedMaterialClassIds] = useState([]);
    const [classPickerOpen, setClassPickerOpen] = useState(false);
    const [materialFile, setMaterialFile] = useState(null);
    const [materialLoading, setMaterialLoading] = useState(false);
    const [materialError, setMaterialError] = useState('');
    const [materialSuccess, setMaterialSuccess] = useState('');
    const [materials, setMaterials] = useState([]);
    const [deleteMaterialId, setDeleteMaterialId] = useState('');
    const [classSessions, setClassSessions] = useState([]);
    const [sessionsLoading, setSessionsLoading] = useState(false);
    const [sessionsError, setSessionsError] = useState('');
    const [deleteSessionId, setDeleteSessionId] = useState('');

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

    const loadClassSessions = async () => {
        setSessionsLoading(true);
        setSessionsError('');
        try {
            const response = await fetch('/api/learning-objectives');
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Failed to load class sessions.');
            }
            const sessions = Object.entries(data).map(([id, details]) => ({
                id,
                title: details.title,
                objectives: details.objectives || [],
            }));
            setClassSessions(sessions);
            setSelectedMaterialClassIds((selectedIds) => selectedIds.filter((id) => sessions.some((session) => session.id === id)));
            setMaterialClassId((currentId) => currentId && sessions.some((session) => session.id === currentId) ? currentId : '');
        } catch (err) {
            setSessionsError(err.message || 'Failed to load class sessions.');
            setClassSessions([]);
        } finally {
            setSessionsLoading(false);
        }
    };

    useEffect(() => {
        loadClassSessions();
    }, []);

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

        try {
            const response = await fetch('/api/learning-objectives', {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
            });
            if (!response.ok) { const errorData = await response.json(); throw new Error(errorData.detail || 'Failed to submit learning objectives.'); }
            setSuccessMessage('Learning objectives submitted successfully!');
            setLessonId(''); setTitle(''); setObjectives(['']);
            await loadClassSessions();
        } catch (err) {
            setError(err.message || 'An unexpected error occurred.');
        } finally { setLoading(false); }
    };

    const handleDeleteSession = async (sessionId) => {
        const confirmed = window.confirm(`Delete class session "${sessionId}"? This will remove its objectives and related class data.`);
        if (!confirmed) {
            return;
        }

        setDeleteSessionId(sessionId);
        setSessionsError('');
        try {
            const response = await fetch(`/api/learning-objectives/${encodeURIComponent(sessionId)}`, {
                method: 'DELETE',
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Failed to delete class session.');
            }
            setClassSessions((sessions) => sessions.filter((session) => session.id !== sessionId));
            if (materialClassId === sessionId) {
                setMaterialClassId('');
                setMaterials([]);
            }
            setSelectedMaterialClassIds((selectedIds) => selectedIds.filter((id) => id !== sessionId));
        } catch (err) {
            setSessionsError(err.message || 'Failed to delete class session.');
        } finally {
            setDeleteSessionId('');
        }
    };

    const loadMaterials = async (classIdOverride) => {
        const classId = (classIdOverride || materialClassId).trim();
        if (!classId) {
            setMaterialError('Enter a class ID first.');
            return;
        }

        setMaterialLoading(true);
        setMaterialError('');
        try {
            const response = await fetch(`/api/classes/${encodeURIComponent(classId)}/materials`);
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Failed to load class materials.');
            }
            setMaterials(data.materials || []);
        } catch (err) {
            setMaterialError(err.message || 'Failed to load class materials.');
            setMaterials([]);
        } finally {
            setMaterialLoading(false);
        }
    };

    const toggleSelectedMaterialClass = (classId) => {
        setSelectedMaterialClassIds((selectedIds) => (
            selectedIds.includes(classId)
                ? selectedIds.filter((id) => id !== classId)
                : [...selectedIds, classId]
        ));
        setMaterialError('');
        setMaterialSuccess('');
    };

    const handleMaterialUpload = async (event) => {
        event.preventDefault();
        if (selectedMaterialClassIds.length === 0) {
            setMaterialError('Select at least one class for this document.');
            return;
        }
        if (!materialFile) {
            setMaterialError('Choose a PDF file to upload.');
            return;
        }

        const formData = new FormData();
        formData.append('file', materialFile);
        selectedMaterialClassIds.forEach((classId) => {
            formData.append('class_ids', classId);
        });
        setMaterialLoading(true);
        setMaterialError('');
        setMaterialSuccess('');
        try {
            const response = await fetch('/api/materials', {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            if (!response.ok) {
                const detail = typeof data.detail === 'string' ? data.detail : data.detail?.message;
                throw new Error(detail || 'Failed to upload material.');
            }
            setMaterialSuccess(`Uploaded ${data.filename} to ${data.class_ids.length} class${data.class_ids.length === 1 ? '' : 'es'} and indexed ${data.chunk_count} chunks.`);
            setMaterialFile(null);
            event.target.reset();
            const classIdToView = materialClassId && selectedMaterialClassIds.includes(materialClassId)
                ? materialClassId
                : selectedMaterialClassIds[0];
            if (classIdToView) {
                setMaterialClassId(classIdToView);
                await loadMaterials(classIdToView);
            }
        } catch (err) {
            setMaterialError(err.message || 'Failed to upload material.');
        } finally {
            setMaterialLoading(false);
        }
    };

    const handleDeleteMaterial = async (material) => {
        const confirmed = window.confirm(`Delete "${material.filename}" from ${material.class_id}? This will remove its RAG chunks for that class.`);
        if (!confirmed) {
            return;
        }

        setDeleteMaterialId(material.id);
        setMaterialError('');
        setMaterialSuccess('');
        try {
            const response = await fetch(`/api/materials/${material.id}`, {
                method: 'DELETE',
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Failed to delete material.');
            }
            setMaterials((currentMaterials) => currentMaterials.filter((item) => item.id !== material.id));
            setMaterialSuccess(`Deleted ${material.filename} from ${material.class_id}.`);
        } catch (err) {
            setMaterialError(err.message || 'Failed to delete material.');
        } finally {
            setDeleteMaterialId('');
        }
    };

    const selectedClassLabel = selectedMaterialClassIds.length === 0
        ? 'Select classes'
        : `${selectedMaterialClassIds.length} class${selectedMaterialClassIds.length === 1 ? '' : 'es'} selected`;

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

            <section className="objectives-form-card sessions-card">
                <div className="sessions-header">
                    <h2>Existing Class Sessions</h2>
                    <button
                        type="button"
                        onClick={loadClassSessions}
                        className="add-objective-button refresh-sessions-button"
                        disabled={sessionsLoading}
                    >
                        {sessionsLoading ? 'Refreshing...' : 'Refresh'}
                    </button>
                </div>

                {sessionsError && <p className="error-message">{sessionsError}</p>}
                {!sessionsLoading && classSessions.length === 0 && !sessionsError && (
                    <p className="empty-sessions-message">No class sessions found.</p>
                )}
                {classSessions.length > 0 && (
                    <ul className="sessions-list">
                        {classSessions.map((session) => (
                            <li key={session.id} className="session-list-item">
                                <div className="session-details">
                                    <strong>{session.title}</strong>
                                    <span>{session.id}</span>
                                    <small>{session.objectives.length} objectives</small>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => handleDeleteSession(session.id)}
                                    className="delete-session-button"
                                    disabled={deleteSessionId === session.id}
                                >
                                    {deleteSessionId === session.id ? 'Deleting...' : 'Delete'}
                                </button>
                            </li>
                        ))}
                    </ul>
                )}
            </section>

            <form onSubmit={handleMaterialUpload} className="objectives-form-card material-upload-card">
                <h2>Import Class Material</h2>
                <div className="form-group">
                    <label>Associated Classes:</label>
                    <div className="class-picker">
                        <button
                            type="button"
                            className="class-picker-toggle"
                            onClick={() => setClassPickerOpen((isOpen) => !isOpen)}
                            disabled={classSessions.length === 0}
                        >
                            {selectedClassLabel}
                        </button>
                        {classPickerOpen && (
                            <div className="class-picker-menu">
                                {classSessions.length === 0 && (
                                    <p className="empty-sessions-message">Create a class session first.</p>
                                )}
                                {classSessions.map((session) => (
                                    <label key={session.id} className="class-picker-option">
                                        <input
                                            type="checkbox"
                                            checked={selectedMaterialClassIds.includes(session.id)}
                                            onChange={() => toggleSelectedMaterialClass(session.id)}
                                        />
                                        <span>
                                            <strong>{session.title}</strong>
                                            <small>{session.id}</small>
                                        </span>
                                    </label>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
                <div className="form-group">
                    <label htmlFor="materialFile">Course Material PDF:</label>
                    <input
                        type="file"
                        id="materialFile"
                        accept="application/pdf"
                        onChange={(e) => setMaterialFile(e.target.files?.[0] || null)}
                        className="form-input"
                        required
                    />
                </div>
                {materialError && <p className="error-message">{materialError}</p>}
                {materialSuccess && <p className="success-message">{materialSuccess}</p>}
                <div className="preview-actions">
                    <button type="submit" className="submit-button" disabled={materialLoading}>
                        {materialLoading ? 'Importing...' : 'Import Material'}
                    </button>
                    <button
                        type="button"
                        onClick={() => loadMaterials()}
                        className="add-objective-button"
                        disabled={materialLoading || !materialClassId.trim()}
                    >
                        Refresh Materials
                    </button>
                </div>
                <div className="form-group">
                    <label htmlFor="materialClassId">View Materials For:</label>
                    <select
                        id="materialClassId"
                        value={materialClassId}
                        onChange={(e) => {
                            const classId = e.target.value;
                            setMaterialClassId(classId);
                            setMaterialError('');
                            setMaterialSuccess('');
                            setMaterials([]);
                            if (classId) {
                                loadMaterials(classId);
                            }
                        }}
                        className="form-input"
                    >
                        <option value="">Select a class</option>
                        {classSessions.map((session) => (
                            <option key={session.id} value={session.id}>
                                {session.title} ({session.id})
                            </option>
                        ))}
                    </select>
                </div>

                {materials.length > 0 && (
                    <div className="materials-list">
                        <h3>Imported Materials</h3>
                        <ul>
                            {materials.map((material) => (
                                <li key={material.id}>
                                    <div className="material-details">
                                        <span>{material.filename}</span>
                                        <small>{material.status} · {material.chunk_count} chunks</small>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => handleDeleteMaterial(material)}
                                        className="delete-session-button"
                                        disabled={deleteMaterialId === material.id}
                                    >
                                        {deleteMaterialId === material.id ? 'Deleting...' : 'Delete'}
                                    </button>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </form>
        </div>
    );
}

export default LearningObjectivesForm;
