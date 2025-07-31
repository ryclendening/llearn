import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import PerformancePanel from './PerformancePanel';
import './ChatPage.css'; // Import the new CSS file

function ChatPage() {
    const { classId, userId } = useParams();
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const socket = useRef(null);
    const messagesEndRef = useRef(null);

    // Effect for WebSocket connection
    useEffect(() => {
        const wsUrl = `ws://localhost:8000/ws/chat/${userId}`;
        socket.current = new WebSocket(wsUrl);

        socket.current.onopen = () => {
            console.log('WebSocket connected!');
            setMessages(prev => [...prev, { sender: 'System', text: 'Connected to the chat.' }]);
        };

        socket.current.onmessage = (event) => {
            setMessages(prev => [...prev, { sender: 'Bot', text: event.data }]);
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

    // Effect for auto-scrolling the chat window
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const sendMessage = async () => {
        if (input.trim() && socket.current && socket.current.readyState === WebSocket.OPEN) {
            socket.current.send(input);
            setMessages(prev => [...prev, { sender: 'You', text: input }]);
            setInput('');
        }
        try {
            const response = await fetch(`/api/assess_performance/${userId}`, {
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

    return (
        <div className="chat-page-container">
            <h2 className="chat-page-title">Student Session: {userId}</h2>

            <div className="chat-main-content">
                {/* Left Panel: Chat Interface */}
                <div className="chat-panel">
                    <div className="chat-messages">
                        {messages.map((msg, index) => (
                            <p key={index} className={`chat-message ${msg.sender.toLowerCase()}`}>
                                <strong>{msg.sender}:</strong> {msg.text}
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
                            placeholder="Type your message..."
                        />
                        <button onClick={sendMessage}>
                            Send
                        </button>
                    </div>
                </div>

                {/* Right Panel: Performance Panel */}
                <div className="performance-panel-area">
                    <PerformancePanel classId={classId} userId={userId} />
                </div>
            </div>
        </div>
    );
}

export default ChatPage;