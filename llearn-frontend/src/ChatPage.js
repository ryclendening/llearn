import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import HomeButton from './HomeButton';
import MathText from './MathText';
import PerformancePanel from './PerformancePanel';
import './ChatPage.css'; // Import the new CSS file

const SUGGESTED_CHAT_ACTIONS = [
    { label: 'Give me a hint', prompt: 'Give me a hint without revealing the answer.' },
    { label: 'Explain another way', prompt: 'Explain this another way with a different example.' },
    { label: 'Quiz me', prompt: 'Quiz me on this objective with one question at a time.' },
    { label: 'Review objective', prompt: 'Review the current learning objective with me.' },
];

function ChatPage() {
    const { classId } = useParams();
    const [activeWorkspaceTab, setActiveWorkspaceTab] = useState('chat');
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [practiceExamples, setPracticeExamples] = useState([]);
    const [selectedExampleId, setSelectedExampleId] = useState('');
    const [solvedExampleIds, setSolvedExampleIds] = useState([]);
    const [practiceResult, setPracticeResult] = useState(null);
    const [practiceSolution, setPracticeSolution] = useState('');
    const [practiceLoading, setPracticeLoading] = useState(false);
    const [practiceError, setPracticeError] = useState('');
    const [classMaterials, setClassMaterials] = useState([]);
    const [selectedMaterialId, setSelectedMaterialId] = useState('');
    const [materialsLoading, setMaterialsLoading] = useState(false);
    const [materialsError, setMaterialsError] = useState('');
    const socket = useRef(null);
    const messagesEndRef = useRef(null);

    const parseSocketMessage = (data) => {
        try {
            const payload = JSON.parse(data);
            return {
                sender: payload.type === 'system' ? 'System' : 'Bot',
                text: payload.text || '',
                citations: Array.isArray(payload.citations) ? payload.citations : [],
            };
        } catch {
            return { sender: 'Bot', text: data, citations: [] };
        }
    };

    const openCitation = (citation) => {
        if (!citation.material_id) {
            return;
        }

        const page = citation.page || 1;
        window.open(`/api/materials/${citation.material_id}/file#page=${page}`, '_blank', 'noopener,noreferrer');
    };

    const selectedExample = practiceExamples.find((example) => String(example.id) === String(selectedExampleId));
    const selectedMaterial = classMaterials.find((material) => String(material.id) === String(selectedMaterialId));
    const selectedMaterialUrl = selectedMaterial ? `/api/materials/${selectedMaterial.id}/file` : '';

    const activateExample = (example) => {
        setSelectedExampleId(String(example.id));
        setPracticeResult(null);
        setPracticeSolution('');
        setPracticeError('');
        setActiveWorkspaceTab('chat');
    };

    const clearSelectedExample = () => {
        setSelectedExampleId('');
        setPracticeResult(null);
        setPracticeSolution('');
        setPracticeError('');
    };

    const loadPracticeExamples = async () => {
        if (!classId) {
            return;
        }

        try {
            const response = await fetch(`/api/classes/${encodeURIComponent(classId)}/practice-examples`);
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Could not load example problems.');
            }
            setPracticeExamples(data.examples || []);
            setPracticeError('');
        } catch (err) {
            setPracticeError(err.message || 'Could not load example problems.');
            setPracticeExamples([]);
        }
    };

    const loadClassMaterials = async () => {
        if (!classId) {
            return;
        }

        setMaterialsLoading(true);
        try {
            const response = await fetch(`/api/classes/${encodeURIComponent(classId)}/materials`);
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Could not load class materials.');
            }
            const materials = Array.isArray(data.materials) ? data.materials : [];
            setClassMaterials(materials);
            setSelectedMaterialId((currentId) => {
                if (materials.some((material) => String(material.id) === String(currentId))) {
                    return currentId;
                }
                return materials[0]?.id ? String(materials[0].id) : '';
            });
            setMaterialsError('');
        } catch (err) {
            setMaterialsError(err.message || 'Could not load class materials.');
            setClassMaterials([]);
            setSelectedMaterialId('');
        } finally {
            setMaterialsLoading(false);
        }
    };

    // Effect for WebSocket connection
    useEffect(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat/${encodeURIComponent(classId)}`;
        socket.current = new WebSocket(wsUrl);

        socket.current.onopen = () => {
            console.log('WebSocket connected!');
            setMessages(prev => [...prev, { sender: 'System', text: 'Connected to the chat.' }]);
        };

        socket.current.onmessage = (event) => {
            setMessages(prev => [...prev, parseSocketMessage(event.data)]);
        };

        socket.current.onerror = (error) => {
            console.error('WebSocket error:', error);
            setMessages(prev => [...prev, { sender: 'System', text: 'A connection error occurred.' }]);
        };

        socket.current.onclose = () => {
            console.log('WebSocket disconnected.');
            setMessages(prev => [...prev, { sender: 'System', text: 'You have been disconnected.' }]);
        };

        return () => {
            if (socket.current) {
                socket.current.close();
            }
        };
    }, [classId]);

    useEffect(() => {
        loadPracticeExamples();
        loadClassMaterials();
    }, [classId]);

    // Effect for auto-scrolling the chat window
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView?.({ behavior: "smooth" });
    }, [messages]);

    const sendMessage = async () => {
        if (selectedExampleId) {
            await submitPracticeAnswer();
            return;
        }

        if (input.trim() && socket.current && socket.current.readyState === WebSocket.OPEN) {
            socket.current.send(input);
            setMessages(prev => [...prev, { sender: 'You', text: input }]);
            setInput('');
        }
        try {
            const response = await fetch(`/api/me/performance?class_id=${encodeURIComponent(classId)}`, {
                method: 'GET'
            });

            if (!response.ok) {
                console.error('Performance assessment failed.');
            } else {
                console.log('Performance assessed successfully.');
            }
        } catch (err) {
            console.error('Error while assessing performance:', err);
        }
    }

    const submitPracticeAnswer = async () => {
        if (!selectedExampleId || !input.trim()) {
            setPracticeError('Choose a problem and enter an answer.');
            return;
        }

        const submittedAnswer = input.trim();
        setPracticeLoading(true);
        setPracticeError('');
        setPracticeResult(null);
        setPracticeSolution('');
        setMessages(prev => [...prev, { sender: 'You', text: submittedAnswer }]);
        setInput('');
        try {
            const response = await fetch(`/api/classes/${encodeURIComponent(classId)}/practice-examples/${selectedExampleId}/attempts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answer: submittedAnswer }),
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Could not grade answer.');
            }
            setPracticeResult(data.attempt);
            if (data.attempt?.is_correct) {
                setSolvedExampleIds((currentIds) => (
                    currentIds.includes(Number(selectedExampleId))
                        ? currentIds
                        : [...currentIds, Number(selectedExampleId)]
                ));
            }
            setMessages(prev => [...prev, {
                sender: 'Judge',
                text: `${data.attempt?.is_correct ? 'Correct.' : 'Not quite yet.'} ${data.attempt?.feedback || ''}`,
            }]);
        } catch (err) {
            setPracticeError(err.message || 'Could not grade answer.');
            setMessages(prev => [...prev, { sender: 'System', text: err.message || 'Could not grade answer.' }]);
        } finally {
            setPracticeLoading(false);
        }
    };

    const revealPracticeSolution = async () => {
        if (!selectedExampleId) {
            return;
        }

        setPracticeLoading(true);
        setPracticeError('');
        try {
            const response = await fetch(`/api/classes/${encodeURIComponent(classId)}/practice-examples/${selectedExampleId}/solution`);
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Could not load solution.');
            }
            setPracticeSolution(data.solution_text || '');
        } catch (err) {
            setPracticeError(err.message || 'Could not load solution.');
        } finally {
            setPracticeLoading(false);
        }
    };

    return (
        <div className="chat-page-container">
            <HomeButton />
            <div className="student-session-header">
                <span className="student-session-eyebrow">Student Workspace</span>
                <h2 className="chat-page-title">{classId}</h2>
            </div>

            <div className="chat-main-content">
                <aside className="student-workspace-sidebar" aria-label="Student workspace">
                    <button
                        type="button"
                        className={`student-workspace-tab ${activeWorkspaceTab === 'chat' ? 'active' : ''}`}
                        aria-pressed={activeWorkspaceTab === 'chat'}
                        onClick={() => setActiveWorkspaceTab('chat')}
                    >
                        Chat
                    </button>

                    <button
                        type="button"
                        className={`student-workspace-tab ${activeWorkspaceTab === 'practice' ? 'active' : ''}`}
                        aria-pressed={activeWorkspaceTab === 'practice'}
                        onClick={() => setActiveWorkspaceTab('practice')}
                    >
                        Practice Problems
                    </button>

                    <button
                        type="button"
                        className={`student-workspace-tab ${activeWorkspaceTab === 'materials' ? 'active' : ''}`}
                        aria-pressed={activeWorkspaceTab === 'materials'}
                        onClick={() => setActiveWorkspaceTab('materials')}
                    >
                        Class Material
                    </button>

                    <div className="student-sidebar-goals" aria-label="Student goals and progress">
                        <div className="student-sidebar-goals-header">
                            <span className="student-sidebar-goals-eyebrow">Goals</span>
                            <strong>Your Progress</strong>
                        </div>

                        <PerformancePanel
                            classId={classId}
                            variant="student-sidebar"
                            activeExample={selectedExample}
                        />
                    </div>
                </aside>                

                <section className="student-workspace-content">
                    {activeWorkspaceTab === 'chat' && (
                        <div className="chat-panel">
                            {selectedExample && (
                                <section className="active-example-box" aria-label="Active example problem">
                                    <div className="active-example-header">
                                        <div>
                                            <span className="active-example-eyebrow">Example Practice</span>
                                            <h3>
                                                {selectedExample.title || 'Selected Problem'}
                                                {selectedExample.page_start ? ` · p. ${selectedExample.page_start}` : ''}
                                            </h3>
                                        </div>
                                        <button
                                            type="button"
                                            className="active-example-exit"
                                            onClick={clearSelectedExample}
                                        >
                                            Exit
                                        </button>
                                    </div>
                                    <div className="active-example-problem">
                                        <MathText text={selectedExample.problem_text} />
                                    </div>
                                    <p className="active-example-instructions">
                                        Submit one final answer below. The next message will be checked against the worked solution.
                                    </p>
                                    {practiceError && <p className="practice-error">{practiceError}</p>}
                                    {practiceResult && (
                                        <div className={`practice-result ${practiceResult.is_correct ? 'correct' : 'incorrect'}`}>
                                            <strong>{practiceResult.is_correct ? 'Correct' : 'Not quite yet'}</strong>
                                            <p><MathText text={practiceResult.feedback} /></p>
                                            {!practiceResult.is_correct && (
                                                <button type="button" onClick={revealPracticeSolution} disabled={practiceLoading}>
                                                    Show Solution
                                                </button>
                                            )}
                                        </div>
                                    )}
                                    {practiceSolution && (
                                        <div className="practice-solution">
                                            <strong>Solution</strong>
                                            <p><MathText text={practiceSolution} /></p>
                                        </div>
                                    )}
                                </section>
                            )}
                            <div className="chat-messages">
                                {messages.map((msg, index) => (
                                    <p key={index} className={`chat-message ${msg.sender.toLowerCase()}`}>
                                        <strong>{msg.sender}:</strong>{' '}
                                        <MathText text={msg.text} citations={msg.citations} onCitationClick={openCitation} />
                                    </p>
                                ))}
                                <div ref={messagesEndRef} />
                            </div>
                            {!selectedExampleId && (
                                <div className="suggested-chat-actions" aria-label="Suggested chat actions">
                                    {SUGGESTED_CHAT_ACTIONS.map((action) => (
                                        <button
                                            key={action.label}
                                            type="button"
                                            onClick={() => setInput(action.prompt)}
                                        >
                                            {action.label}
                                        </button>
                                    ))}
                                </div>
                            )}
                            <div className="chat-input-area">
                                <input
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                                    placeholder={selectedExampleId ? "Enter your final answer for the selected example..." : "Type your message..."}
                                />
                                {!selectedExampleId && (
                                    <button type="button" onClick={sendMessage}>
                                        Send
                                    </button>
                                )}
                                {selectedExampleId && (
                                    <>
                                        <button
                                            type="button"
                                            className="check-answer-button"
                                            onClick={submitPracticeAnswer}
                                            disabled={practiceLoading}
                                        >
                                            {practiceLoading ? 'Checking...' : 'Check Answer'}
                                        </button>
                                        <button
                                            type="button"
                                            className="clear-example-button"
                                            onClick={clearSelectedExample}
                                        >
                                            Exit Example
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>
                    )}

                    {activeWorkspaceTab === 'practice' && (
                        <div className="student-workspace-panel">
                            <div className="workspace-panel-header">
                                <div>
                                    <h3>Practice Problems</h3>
                                    <p>Choose a worked example to answer in chat.</p>
                                </div>
                                <button
                                    type="button"
                                    className="workspace-secondary-button"
                                    onClick={loadPracticeExamples}
                                >
                                    Refresh
                                </button>
                            </div>
                            {!selectedExample && practiceError && <p className="practice-error">{practiceError}</p>}
                            {practiceExamples.length === 0 && !practiceError && (
                                <p className="practice-empty">No example problems are available for this class yet.</p>
                            )}
                            {practiceExamples.length > 0 && (
                                <div className="practice-card-list practice-card-grid">
                                    {practiceExamples.map((example, index) => (
                                        <button
                                            key={example.id}
                                            type="button"
                                            className={`practice-card ${String(example.id) === String(selectedExampleId) ? 'active' : ''} ${solvedExampleIds.includes(example.id) ? 'solved' : ''}`}
                                            onClick={() => activateExample(example)}
                                        >
                                            <span className="practice-card-meta">
                                                Example {index + 1}
                                                {example.page_start ? ` · p. ${example.page_start}` : ''}
                                            </span>
                                            <span className="practice-card-text">
                                                <MathText text={example.problem_text} />
                                            </span>
                                            <em>Work in chat</em>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {activeWorkspaceTab === 'materials' && (
                        <div className="student-workspace-panel material-workspace-panel">
                            <div className="workspace-panel-header compact">
                                <h3>Class Material</h3>
                                <button
                                    type="button"
                                    className="workspace-secondary-button"
                                    onClick={loadClassMaterials}
                                    disabled={materialsLoading}
                                >
                                    {materialsLoading ? 'Refreshing...' : 'Refresh'}
                                </button>
                            </div>
                            {materialsError && <p className="practice-error">{materialsError}</p>}
                            {materialsLoading && classMaterials.length === 0 && (
                                <p className="practice-empty">Loading class materials...</p>
                            )}
                            {!materialsLoading && classMaterials.length === 0 && !materialsError && (
                                <p className="practice-empty">No class materials are available yet.</p>
                            )}
                            {classMaterials.length > 0 && (
                                <div className="class-material-browser">
                                    <div className="class-material-list" aria-label="Class materials">
                                        {classMaterials.map((material) => (
                                            <button
                                                key={material.id}
                                                type="button"
                                                className={`class-material-card ${String(material.id) === String(selectedMaterialId) ? 'active' : ''}`}
                                                aria-pressed={String(material.id) === String(selectedMaterialId)}
                                                onClick={() => setSelectedMaterialId(String(material.id))}
                                            >
                                                <span>
                                                    <span className="class-material-title">{material.filename}</span>
                                                </span>
                                            </button>
                                        ))}
                                    </div>
                                    {selectedMaterial && (
                                        <section className="class-material-viewer" aria-label={`Preview of ${selectedMaterial.filename}`}>
                                            <div className="class-material-viewer-header">
                                                <a href={selectedMaterialUrl} target="_blank" rel="noreferrer">
                                                    Open in new tab
                                                </a>
                                            </div>
                                            <iframe
                                                title={`Class material: ${selectedMaterial.filename}`}
                                                src={selectedMaterialUrl}
                                            />
                                        </section>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </section>
            </div>
        </div>
    );
}

export default ChatPage;
