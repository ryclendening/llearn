import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './HomePage';
import ChatPage from './ChatPage';
import ClassPerformanceDashboard from './ClassPerformanceDashboard';
import LearningObjectivesForm from './LearningObjectivesForm';

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/chat/:classId/:userId" element={<ChatPage />} />
                <Route path="/dashboard/:classId" element={<ClassPerformanceDashboard />} />
                <Route path="/create-objectives" element={<LearningObjectivesForm />} />


            </Routes>
        </Router>
    );
}

export default App;