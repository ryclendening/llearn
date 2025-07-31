import React, { useState } from 'react';
import './LearningObjectivesForm.css'; // Import the CSS file for styling

function LearningObjectivesForm() {
    // State for form fields
    const [lessonId, setLessonId] = useState('');
    const [title, setTitle] = useState('');
    const [objectives, setObjectives] = useState(['']); // Start with one empty objective input

    // State for UI feedback
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');

    /**
     * Handles changes to the lesson ID input field.
     * @param {object} e - The event object.
     */
    const handleLessonIdChange = (e) => {
        setLessonId(e.target.value);
        setError(''); // Clear error on input change
        setSuccessMessage(''); // Clear success message on input change
    };

    /**
     * Handles changes to the title input field.
     * @param {object} e - The event object.
     */
    const handleTitleChange = (e) => {
        setTitle(e.target.value);
        setError(''); // Clear error on input change
        setSuccessMessage(''); // Clear success message on input change
    };

    /**
     * Handles changes to a specific objective input field.
     * @param {number} index - The index of the objective being changed.
     * @param {object} e - The event object.
     */
    const handleObjectiveChange = (index, e) => {
        const newObjectives = [...objectives];
        newObjectives[index] = e.target.value;
        setObjectives(newObjectives);
        setError(''); // Clear error on input change
        setSuccessMessage(''); // Clear success message on input change
    };

    /**
     * Adds a new empty objective input field.
     */
    const addObjectiveField = () => {
        setObjectives([...objectives, '']);
    };

    /**
     * Removes an objective input field at a specific index.
     * @param {number} index - The index of the objective to remove.
     */
    const removeObjectiveField = (index) => {
        const newObjectives = objectives.filter((_, i) => i !== index);
        setObjectives(newObjectives);
    };

    /**
     * Handles the form submission.
     * Constructs the payload and sends it to the backend.
     * @param {object} event - The form submission event.
     */
    const handleSubmit = async (event) => {
        event.preventDefault(); // Prevent default form submission behavior

        // Basic validation
        if (!lessonId.trim() || !title.trim()) {
            setError('Lesson ID and Title cannot be empty.');
            return;
        }
        const filteredObjectives = objectives.filter(obj => obj.trim() !== '');
        if (filteredObjectives.length === 0) {
            setError('Please add at least one learning objective.');
            return;
        }

        setLoading(true);
        setError('');
        setSuccessMessage('');

        // Construct the payload as per the requirement
        const payload = {
            lesson_id: lessonId.trim(),
            title: title.trim(),
            objectives: filteredObjectives,
        };
        const assessor_payload = {
            class_id: lessonId.trim(),
        };

        try {
            const response = await fetch('/api/learning-objectives', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to submit learning objectives.');
            }

            // Success!
            setSuccessMessage('Learning objectives submitted successfully!');
            // Optionally clear the form after successful submission
            setLessonId('');
            setTitle('');
            setObjectives(['']); // Reset to one empty objective

        } catch (err) {
            console.error("Submission error:", err);
            setError(err.message || 'An unexpected error occurred.');
        } finally {
            setLoading(false);
        }
        try {
            const response = await fetch('/api/create-assessor', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(assessor_payload),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create assessor.');
            }

            // Success!
            setSuccessMessage('Asessor created successfully!');
            // Optionally clear the form after successful submission
            setLessonId('');
            setTitle('');
            setObjectives(['']); // Reset to one empty objective

        } catch (err) {
            console.error("Submission error:", err);
            setError(err.message || 'An unexpected error occurred.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="objectives-page-container">
            <h1 className="objectives-page-title">Create Learning Objectives</h1>

            <form onSubmit={handleSubmit} className="objectives-form-card">
                {/* Lesson ID Input */}
                <div className="form-group">
                    <label htmlFor="lessonId">Lesson ID:</label>
                    <input
                        type="text"
                        id="lessonId"
                        value={lessonId}
                        onChange={handleLessonIdChange}
                        placeholder="e.g., science101"
                        className="form-input"
                        required
                    />
                </div>

                {/* Title Input */}
                <div className="form-group">
                    <label htmlFor="title">Title:</label>
                    <input
                        type="text"
                        id="title"
                        value={title}
                        onChange={handleTitleChange}
                        placeholder="e.g., Introduction to Plants"
                        className="form-input"
                        required
                    />
                </div>

                {/* Objectives Section */}
                <div className="form-group objectives-group">
                    <label>Learning Objectives:</label>
                    {objectives.map((objective, index) => (
                        <div key={index} className="objective-input-row">
                            <input
                                type="text"
                                value={objective}
                                onChange={(e) => handleObjectiveChange(index, e)}
                                placeholder={`Objective ${index + 1}`}
                                className="form-input objective-input"
                                required // Each objective should be required
                            />
                            {objectives.length > 1 && ( // Only show remove button if more than one objective
                                <button
                                    type="button"
                                    onClick={() => removeObjectiveField(index)}
                                    className="remove-objective-button"
                                >
                                    &times; {/* HTML entity for multiplication sign, often used for close/remove */}
                                </button>
                            )}
                        </div>
                    ))}
                    <button
                        type="button"
                        onClick={addObjectiveField}
                        className="add-objective-button"
                    >
                        + Add Objective
                    </button>
                </div>

                {/* Submission Feedback */}
                {error && <p className="error-message">{error}</p>}
                {successMessage && <p className="success-message">{successMessage}</p>}

                {/* Submit Button */}
                <button
                    type="submit"
                    className="submit-button"
                    disabled={loading} // Disable button while loading
                >
                    {loading ? 'Submitting...' : 'Submit Objectives'}
                </button>
            </form>
        </div>
    );
}

export default LearningObjectivesForm;
