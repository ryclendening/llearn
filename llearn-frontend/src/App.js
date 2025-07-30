import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './HomePage';
import ChatPage from './ChatPage';

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/chat/:classId/:userId" element={<ChatPage />} />
            </Routes>
        </Router>
    );
}

export default App;