import { render, screen } from '@testing-library/react';
import { beforeEach, test, vi } from 'vitest';
import App from './App';

const mockApi = (user) => {
  vi.stubGlobal('fetch', vi.fn(async (url) => ({
    ok: user !== null || url !== '/api/auth/me',
    json: async () => {
      if (url === '/api/auth/me') return user || { detail: 'Authentication required' };
      if (url === '/api/learning-objectives') return {};
      if (url === '/api/admin/teacher-access-requests') return { requests: [] };
      return {};
    },
  })));
};

beforeEach(() => {
  window.history.pushState({}, '', '/');
});

test('unauthenticated users see sign in', async () => {
  mockApi(null);
  render(<App />);
  expect(await screen.findByRole('heading', { name: /sign in to llearn/i })).toBeInTheDocument();
});

test('student users see class joining', async () => {
  mockApi({ id: 'student-1', email: 'student@example.com', display_name: 'Student', role: 'student' });
  render(<App />);
  expect(await screen.findByRole('button', { name: /join class/i })).toBeInTheDocument();
});

test('administrators see identity administration entry point', async () => {
  mockApi({ id: 'admin-1', email: 'admin@example.com', display_name: 'Admin', role: 'admin' });
  render(<App />);
  expect(await screen.findByRole('button', { name: /manage teacher requests/i })).toBeInTheDocument();
});

test('authenticated administrators visiting login are redirected to admin management', async () => {
  window.history.pushState({}, '', '/login');
  mockApi({ id: 'admin-1', email: 'admin@example.com', display_name: 'Admin', role: 'admin' });
  render(<App />);
  expect(await screen.findByRole('heading', { name: /teacher access requests/i })).toBeInTheDocument();
});
