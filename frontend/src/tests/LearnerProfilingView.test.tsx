import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { LearnerProfilingView } from '../features/profiling/LearnerProfilingView';

// Mock profiling service
vi.mock('../services/profilingService', () => ({
  profilingService: {
    getStatus: vi.fn().mockResolvedValue({
      has_uploaded_resume: true,
      last_uploaded_filename: 'resume.txt',
      total_skills_in_preview: 5,
      confirmed_skills_count: 2,
      pending_review_count: 3,
      total_persisted_skills: 4,
    }),
    getPreview: vi.fn().mockResolvedValue({
      user_id: 'test-user-id',
      extracted_skills: [
        {
          id: 'skill-1',
          canonical_name: 'Python',
          category: 'Programming Languages',
          original_phrase: 'Python 3.10',
          proficiency_level: 4,
          proficiency_status: 'ESTIMATED',
          confidence_score: 0.88,
          evidence: [
            {
              evidence_type: 'PROJECT_DEMONSTRATED',
              source_section: 'Projects',
              original_phrase: 'Python',
              description: 'Built high-throughput backend services.',
              confidence_score: 0.88,
            },
          ],
          normalization_method: 'EXACT_MATCH',
          is_confirmed: false,
          is_rejected: false,
        },
      ],
      total_skills_count: 1,
      categories_breakdown: { 'Programming Languages': 1 },
      ai_model_used: 'llama3.2:3b',
      is_fallback: false,
      extraction_timestamp: new Date().toISOString(),
      document_summary: {
        headline: 'Senior Backend Developer',
        summary: 'Demonstrated experience in Python backend development.',
      },
    }),
    uploadResume: vi.fn().mockResolvedValue({}),
    extractSkills: vi.fn().mockResolvedValue({}),
    updateSkill: vi.fn().mockResolvedValue({}),
    confirmProfile: vi.fn().mockResolvedValue({ message: 'Saved successfully' }),
  },
}));

describe('LearnerProfilingView Component', () => {
  it('renders header, tabs, and analyze button', () => {
    render(<LearnerProfilingView />);

    expect(screen.getByText(/AI Profiling & Skill Extraction Engine/i)).toBeDefined();
    expect(screen.getByText(/Upload Resume Document/i)).toBeDefined();
    expect(screen.getByText(/Paste Raw Text/i)).toBeDefined();
    expect(screen.getByText(/Analyze & Extract Skills/i)).toBeDefined();
  });

  it('switches to raw text paste mode when tab is clicked', () => {
    render(<LearnerProfilingView />);

    const textTab = screen.getByText(/Paste Raw Text/i);
    fireEvent.click(textTab);

    expect(screen.getByPlaceholderText(/Paste your technical skills/i)).toBeDefined();
  });
});
