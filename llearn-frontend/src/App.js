import React, { useEffect } from 'react';
import logo from './logo.svg';
import './App.css';
import Header from './header';
import Footer from './footer';
import Screen from './screen';
import Login from './login';

function App() {
  useEffect(() => {
    const button = document.querySelector('.get-started-button');
    const handleClick = () => {
      window.location.href = './login';
    };

    button.addEventListener('click', handleClick);

    // Cleanup the event listener on component unmount
    return () => {
      button.removeEventListener('click', handleClick);
    };
  }, []);

  return (
    <div style={{ position: 'relative', height: '100vh' }}>
      <Screen />
      <Header>
        <button className="get-started-button" style={{ color: '#282828', backgroundColor: '#fdffe2', position: 'absolute', right: '5%', top: '25%' }}>
          Get started
        </button>
      </Header>
      <div className="body" style={{ position: 'absolute', top: '50%', left: '3%', width: '50%', transform: 'translateY(-50%)', padding: '20px', borderRadius: '10px' }}>
        <h1>Enhance student understanding with AI-based chat sessions, tailored by you.</h1>
      </div>
      <Footer>
        <blockquote>
          "LLearn has seamlessly integrated into my lesson plans. It provides my students with the opportunity to explore our curriculum in greater depth, all the while ensuring their interactions are constructive, uplifting, and meaningful!"
        </blockquote>
      </Footer>
    </div>
  );
}

export default App;