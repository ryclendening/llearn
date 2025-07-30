import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import PerformancePanel from './PerformancePanel'; // 1. Import the new component

function ChatPage() {
    const {classId, userId } = useParams(); // Get user_id from the URL
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const socket = useRef(null);
    const messagesEndRef = useRef(null); // Ref to auto-scroll chat

    // Effect for WebSocket connection
    useEffect(() => {
        // The WebSocket URL must match your backend server address
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

        // Cleanup function to close the socket when the component unmounts
        return () => {
            if (socket.current) {
                socket.current.close();
            }
        };
    }, [userId]); // Re-run effect if userId changes

    // Effect for auto-scrolling the chat window
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);


    const sendMessage = () => {
        if (input.trim() && socket.current && socket.current.readyState === WebSocket.OPEN) {
            socket.current.send(input);
            setMessages(prev => [...prev, { sender: 'You', text: input }]);
            setInput('');
        }
    };

    return (
        <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
            <h2 style={{ textAlign: 'center', marginBottom: '20px' }}>Student Session: {userId}</h2>
            
            {/* 2. Main container for the two-panel layout */}
            <div style={{ display: 'flex', flexDirection: 'row', height: '80vh', maxWidth: '1200px', margin: 'auto' }}>

                {/* Left Panel: Chat Interface */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', border: '1px solid #ccc', borderRadius: '8px', overflow: 'hidden' }}>
                    <div style={{ flex: 1, padding: '10px', overflowY: 'auto' }}>
                        {messages.map((msg, index) => (
                            <p key={index} style={{ margin: '8px 0' }}>
                                <strong style={{color: msg.sender === 'You' ? '#007bff' : '#28a745'}}>{msg.sender}:</strong> {msg.text}
                            </p>
                        ))}
                        <div ref={messagesEndRef} /> {/* Invisible element to scroll to */}
                    </div>
                    <div style={{ display: 'flex', borderTop: '1px solid #ccc', padding: '10px' }}>
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                            placeholder="Type your message..."
                            style={{ flex: 1, padding: '10px', fontSize: '16px', border: '1px solid #ddd', borderRadius: '5px' }}
                        />
                        <button onClick={sendMessage} style={{ padding: '10px 20px', fontSize: '16px', marginLeft: '10px', cursor: 'pointer', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '5px' }}>
                            Send
                        </button>
                    </div>
                </div>

                {/* 3. Right Panel: Performance Display */}
                <PerformancePanel classId={classId} userId={userId} />

            </div>
        </div>
    );
}

export default ChatPage;
