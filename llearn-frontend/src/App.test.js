import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, test, vi } from 'vitest';
import App from './App';

const mockApi = (user) => {
  vi.stubGlobal('fetch', vi.fn(async (url) => ({
    ok: user !== null || url !== '/api/auth/me',
    json: async () => {
      if (url === '/api/auth/me') return user || { detail: 'Authentication required' };
      if (url === '/api/learning-objectives') return { 'class-1': { title: 'Fractions', objectives: ['Compare fractions'] } };
      if (url === '/api/admin/teacher-access-requests') return { requests: [] };
      if (url === '/api/classes/class-1/practice-examples') {
        return {
          examples: [
            {
              id: 7,
              problem_text: 'What is 1/2 + 1/4?',
              page_start: 3,
            },
          ],
        };
      }
      if (url === '/api/classes/class-1/materials') {
        return {
          materials: [
            {
              id: 11,
              filename: 'fractions-notes.pdf',
              status: 'ready',
              chunk_count: 4,
              extraction_status: 'completed',
            },
            {
              id: 12,
              filename: 'practice-review.pdf',
              status: 'ready',
              chunk_count: 2,
              extraction_status: 'completed',
            },
          ],
        };
      }
      if (url === '/api/me/performance?class_id=class-1') {
        return {
          assessment: { objective_1: 0.5 },
          example_performance: { assigned_count: 1, correct_count: 0, attempted_count: 0 },
        };
      }
      return {};
    },
  })));
};

beforeEach(() => {
  window.history.pushState({}, '', '/');
  class MockWebSocket {
    static OPEN = 1;
    static instances = [];

    constructor() {
      this.readyState = MockWebSocket.OPEN;
      MockWebSocket.instances.push(this);
    }

    send = vi.fn();
    close = vi.fn();
  }
  vi.stubGlobal('WebSocket', MockWebSocket);
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

test('student session uses workspace tabs', async () => {
  window.history.pushState({}, '', '/chat/class-1');
  mockApi({ id: 'student-1', email: 'student@example.com', display_name: 'Student', role: 'student' });
  render(<App />);

  expect(await screen.findByRole('button', { name: /^chat$/i })).toHaveAttribute('aria-pressed', 'true');
  expect(screen.getByRole('button', { name: /practice problems/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /class material/i })).toBeInTheDocument();
  expect(await screen.findByText(/learning progress/i)).toBeInTheDocument();
  expect(screen.getByText(/compare fractions/i)).toBeInTheDocument();

  const chatInput = screen.getByPlaceholderText(/type your message/i);
  const socket = WebSocket.instances[0];
  const suggestedActions = [
    ['Give me a hint', 'Give me a hint without revealing the answer.'],
    ['Explain another way', 'Explain this another way with a different example.'],
    ['Quiz me', 'Quiz me on this objective with one question at a time.'],
    ['Review objective', 'Review the current learning objective with me.'],
  ];
  suggestedActions.forEach(([label, prompt]) => {
    fireEvent.click(screen.getByRole('button', { name: label }));
    expect(chatInput).toHaveValue(prompt);
  });
  expect(socket.send).not.toHaveBeenCalled();

  fireEvent.click(screen.getByRole('button', { name: /practice problems/i }));
  expect(await screen.findByRole('heading', { name: /practice problems/i })).toBeInTheDocument();
  expect(screen.getByText(/compare fractions/i)).toBeInTheDocument();
  fireEvent.click(await screen.findByRole('button', { name: /what is 1\/2 \+ 1\/4/i }));
  expect(screen.getByRole('button', { name: /^chat$/i })).toHaveAttribute('aria-pressed', 'true');
  expect(await screen.findByLabelText(/active example problem/i)).toBeInTheDocument();
  expect(screen.getByText(/active example selected/i)).toBeInTheDocument();

  fireEvent.click(screen.getByRole('button', { name: /class material/i }));
  expect(await screen.findByRole('heading', { name: /class material/i })).toBeInTheDocument();
  expect(await screen.findByRole('button', { name: /fractions-notes.pdf/i })).toBeInTheDocument();
  expect(screen.queryByText(/ready · 4 chunks/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/example extraction: completed/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/review class documents attached by your teacher/i)).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: /fractions-notes.pdf/i })).toHaveClass('active');
  expect(screen.getByRole('button', { name: /fractions-notes.pdf/i })).toHaveAttribute('aria-pressed', 'true');
  expect(screen.getByRole('button', { name: /practice-review.pdf/i })).not.toHaveClass('active');
  expect(screen.getByRole('button', { name: /practice-review.pdf/i })).toHaveAttribute('aria-pressed', 'false');
  expect(screen.getByTitle(/class material: fractions-notes.pdf/i)).toHaveAttribute(
    'src',
    '/api/materials/11/file'
  );
  fireEvent.click(screen.getByRole('button', { name: /practice-review.pdf/i }));
  expect(screen.getByRole('button', { name: /practice-review.pdf/i })).toHaveClass('active');
  expect(screen.getByRole('button', { name: /practice-review.pdf/i })).toHaveAttribute('aria-pressed', 'true');
  expect(screen.getByRole('button', { name: /fractions-notes.pdf/i })).toHaveAttribute('aria-pressed', 'false');
  expect(screen.getByTitle(/class material: practice-review.pdf/i)).toHaveAttribute(
    'src',
    '/api/materials/12/file'
  );
  expect(screen.getByText(/compare fractions/i)).toBeInTheDocument();
});

test('authenticated administrators visiting login are redirected to admin management', async () => {
  window.history.pushState({}, '', '/login');
  mockApi({ id: 'admin-1', email: 'admin@example.com', display_name: 'Admin', role: 'admin' });
  render(<App />);
  expect(await screen.findByRole('heading', { name: /teacher access requests/i })).toBeInTheDocument();
});
