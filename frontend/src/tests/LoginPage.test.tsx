import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { LoginPage } from '../features/auth/LoginPage';

describe('LoginPage Component', () => {
  it('renders login form with email and password fields', () => {
    const handleSuccess = vi.fn();
    const handleNavigate = vi.fn();

    render(<LoginPage onSuccess={handleSuccess} onNavigateToRegister={handleNavigate} />);

    expect(screen.getByText(/Welcome Back/i)).toBeDefined();
    expect(screen.getByPlaceholderText(/student@example.com/i)).toBeDefined();
    expect(screen.getByPlaceholderText(/••••••••••••/i)).toBeDefined();
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeDefined();
  });

  it('triggers navigation callback when register link is clicked', () => {
    const handleSuccess = vi.fn();
    const handleNavigate = vi.fn();

    render(<LoginPage onSuccess={handleSuccess} onNavigateToRegister={handleNavigate} />);

    const registerBtn = screen.getByText(/Create an account/i);
    fireEvent.click(registerBtn);

    expect(handleNavigate).toHaveBeenCalledTimes(1);
  });
});
