import { render, screen } from '@testing-library/react';
import App from './App';

test('renders the class join page', () => {
  render(<App />);
  expect(screen.getByRole('heading', { name: /join a class/i })).toBeInTheDocument();
});
