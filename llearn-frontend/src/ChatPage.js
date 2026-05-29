import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import HomeButton from './HomeButton';
import MathText from './MathText';
import PerformancePanel from './PerformancePanel';
import './ChatPage.css'; // Import the new CSS file

function ChatPage() {
    const { classId, userId } = useParams();
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [practiceExamples, setPracticeExamples] = useState([]);
    const [selectedExampleId, setSelectedExampleId] = useState('');
    const [solvedExampleIds, setSolvedExampleIds] = useState([]);
    const [practiceResult, setPracticeResult] = useState(null);
    const [practiceSolution, setPracticeSolution] = useState('');
    const [practiceLoading, setPracticeLoading] = useState(false);
    const [practiceError, setPracticeError] = useState('');
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

    const activateExample = (example) => {
        setSelectedExampleId(String(example.id));
        setPracticeResult(null);
        setPracticeSolution('');
        setPracticeError('');
        setMessages(prev => [...prev, {
            sender: 'System',
            text: `Example problem selected. Use the main chat box to submit your answer.\n\n${example.problem_text}`,
        }]);
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

    // Effect for WebSocket connection
    useEffect(() => {
        const wsUrl = `ws://localhost:8000/ws/chat/${userId}`;
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
    }, [userId]);

    useEffect(() => {
        loadPracticeExamples();
    }, [classId]);

    // Effect for auto-scrolling the chat window
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
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
            const response = await fetch(`/api/performance/${userId}`, {
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
                body: JSON.stringify({ user_id: userId, answer: submittedAnswer }),
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
            const response = await fetch(`/api/classes/${encodeURIComponent(classId)}/practice-examples/${selectedExampleId}/solution?user_id=${encodeURIComponent(userId)}`);
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
            <h2 className="chat-page-title">Student Session: {userId}</h2>

            <div className="chat-main-content">
                {/* Left Panel: Chat Interface */}
                <div className="chat-panel">
                    <div className="chat-messages">
                        {messages.map((msg, index) => (
                            <p key={index} className={`chat-message ${msg.sender.toLowerCase()}`}>
                                <strong>{msg.sender}:</strong>{' '}
                                <MathText text={msg.text} citations={msg.citations} onCitationClick={openCitation} />
                            </p>
                        ))}
                        <div ref={messagesEndRef} />
                    </div>
                    <div className="chat-input-area">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                            placeholder={selectedExampleId ? "Enter your final answer for the selected example..." : "Type your message..."}
                        />
                        {!selectedExampleId && (
                            <button onClick={sendMessage}>
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
                                    onClick={() => {
                                        setSelectedExampleId('');
                                        setPracticeResult(null);
                                        setPracticeSolution('');
                                        setPracticeError('');
                                    }}
                                >
                                    Exit Example
                                </button>
                            </>
                        )}
                    </div>
                </div>

                {/* Right Panel: Performance Panel */}
                <div className="performance-panel-area">
                    <div className="practice-panel">
                        <div className="practice-header">
                            <h3>Example Problems</h3>
                            <button type="button" onClick={loadPracticeExamples}>Refresh</button>
                        </div>
                        {practiceError && <p className="practice-error">{practiceError}</p>}
                        {practiceExamples.length === 0 && !practiceError && (
                            <p className="practice-empty">No example problems are available for this class yet.</p>
                        )}
                        {practiceExamples.length > 0 && (
                            <div className="practice-card-list">
                                {practiceExamples.map((example, index) => (
                                    <button
                                        key={example.id}
                                        type="button"
                                        className={`practice-card ${String(example.id) === String(selectedExampleId) ? 'active' : ''} ${solvedExampleIds.includes(example.id) ? 'solved' : ''}`}
                                        onDoubleClick={() => activateExample(example)}
                                        title="Double-click to work this problem in chat"
                                    >
                                        <span className="practice-card-meta">
                                            Example {index + 1}
                                            {example.page_start ? ` · p. ${example.page_start}` : ''}
                                        </span>
                                        <span className="practice-card-text">
                                            <MathText text={example.problem_text} />
                                        </span>
                                    </button>
                                ))}
                            </div>
                        )}
                        {selectedExample && (
                            <div className="practice-workspace">
                                <p className="practice-empty">Active example. Enter a final answer, or exit to return to chat.</p>
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
                            </div>
                        )}
                    </div>
                    <PerformancePanel classId={classId} userId={userId} />
                </div>
            </div>
        </div>
    );
}

export default ChatPage;
