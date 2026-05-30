import React, { useEffect, useState } from 'react';
import './ThemeToggle.css';

const getInitialTheme = () => {
    const savedTheme = window.localStorage.getItem('llearn-theme');
    if (savedTheme === 'dark' || savedTheme === 'light') {
        return savedTheme;
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

function ThemeToggle() {
    const [theme, setTheme] = useState(getInitialTheme);
    const isDark = theme === 'dark';

    useEffect(() => {
        document.documentElement.dataset.theme = theme;
        window.localStorage.setItem('llearn-theme', theme);
    }, [theme]);

    return (
        <button
            type="button"
            className="theme-toggle"
            aria-pressed={isDark}
            aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            onClick={() => setTheme(isDark ? 'light' : 'dark')}
        >
            <span className="theme-toggle-track" aria-hidden="true">
                <span className="theme-toggle-thumb" />
            </span>
            <span>{isDark ? 'Dark' : 'Light'}</span>
        </button>
    );
}

export default ThemeToggle;
