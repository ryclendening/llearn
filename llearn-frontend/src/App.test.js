import { fireEvent, render, screen } from '@testing-library/react';
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

test('teacher class setup uses workflow tabs', async () => {
  window.history.pushState({}, '', '/create-objectives');
  mockApi({ id: 'teacher-1', email: 'teacher@example.com', display_name: 'Teacher', role: 'teacher' });
  render(<App />);

  expect(await screen.findByRole('heading', { name: /goal workflow/i })).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: /generate with ai/i })).not.toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: /existing classes/i })).not.toBeInTheDocument();
  expect(screen.queryByLabelText(/course material pdf/i)).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole('button', { name: /generate with ai/i }));
  expect(await screen.findByRole('heading', { name: /generate with ai/i })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: /ai objective generator/i })).toBeInTheDocument();

  fireEvent.click(screen.getByRole('button', { name: /existing classes/i }));
  expect(await screen.findByRole('heading', { name: /existing classes/i })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: /existing class sessions/i })).toBeInTheDocument();

  fireEvent.click(screen.getByRole('button', { name: /class materials/i }));

  expect(await screen.findByRole('heading', { name: /class material workflow/i })).toBeInTheDocument();
  expect(screen.getByLabelText(/course material pdf/i)).toBeInTheDocument();
});

test('authenticated administrators visiting login are redirected to admin management', async () => {
  window.history.pushState({}, '', '/login');
  mockApi({ id: 'admin-1', email: 'admin@example.com', display_name: 'Admin', role: 'admin' });
  render(<App />);
  expect(await screen.findByRole('heading', { name: /teacher access requests/i })).toBeInTheDocument();
});
