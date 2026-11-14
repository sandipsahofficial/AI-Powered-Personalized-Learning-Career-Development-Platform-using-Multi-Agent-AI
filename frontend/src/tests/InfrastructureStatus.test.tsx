import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { InfrastructureStatus } from '../components/InfrastructureStatus';

describe('InfrastructureStatus Component', () => {
  it('renders the infrastructure header correctly', () => {
    render(<InfrastructureStatus />);
    expect(screen.getByText(/Environment & Infrastructure Status/i)).toBeDefined();
    expect(screen.getByText(/Frontend Client/i)).toBeDefined();
    expect(screen.getByText(/FastAPI Backend/i)).toBeDefined();
    expect(screen.getAllByText(/PostgreSQL \+ pgvector/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Redis 7 In-Memory/i)).toBeDefined();
    expect(screen.getByText(/Ollama Local LLM Connectivity/i)).toBeDefined();
  });
});
