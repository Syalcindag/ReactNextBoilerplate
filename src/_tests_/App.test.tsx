// src/__tests__/App.test.tsx
import { render, screen } from '@testing-library/react';
import App from '../components/App';

test('renders without crashing', () => {
  render(<App />);
  const linkElement = screen.getByText("Hello, Next.js!");
  expect(linkElement).toBeInTheDocument();
});
