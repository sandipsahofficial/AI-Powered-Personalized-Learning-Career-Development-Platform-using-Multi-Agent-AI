import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CareerPathView } from '../features/career/CareerPathView';
import { RoadmapView } from '../features/roadmap/RoadmapView';

vi.mock('../services/careerService', () => ({
  careerService: {
    listRoles: vi.fn().mockResolvedValue([
      {
        id: '1',
        title: 'Full Stack Developer',
        slug: 'full-stack-developer',
        category_name: 'Software Engineering',
        industry_demand_level: 'VERY_HIGH',
        average_salary_range: '$90,000 - $145,000',
        description: 'Designs client and server applications.',
      },
    ]),
    getActiveGoal: vi.fn().mockResolvedValue(null),
    matchCareer: vi.fn().mockResolvedValue({
      career_role_id: '1',
      career_role_title: 'Full Stack Developer',
      match_percentage: 55.0,
      matched_skills_count: 2,
      weak_skills_count: 2,
      missing_skills_count: 3,
      total_required_skills: 7,
      matching_skills: [],
      weak_skills: [],
      missing_skills: [],
      gap_summary: {
        role_title: 'Full Stack Developer',
        readiness_verdict: 'IN_DEVELOPMENT',
        match_percentage: 55.0,
        matched_count: 2,
        weak_count: 2,
        missing_count: 3,
        mandatory_missing: [],
        key_recommendation: 'Prioritize Node.js and PostgreSQL.',
      },
      computed_at: new Date().toISOString(),
    }),
  },
}));

vi.mock('../services/roadmapService', () => ({
  roadmapService: {
    getActiveRoadmap: vi.fn().mockResolvedValue({
      id: 'roadmap-1',
      user_id: 'user-1',
      career_role_id: '1',
      career_role_title: 'Full Stack Developer',
      title: 'Personalized Pathway: Full Stack Developer',
      status: 'ACTIVE',
      version: 1,
      total_estimated_hours: 88,
      progress_percentage: 25.0,
      milestones: [
        {
          id: 'ms-1',
          phase_number: 1,
          order_index: 1,
          title: 'Phase 1: Core Foundations',
          description: 'Master HTML, CSS and JS fundamentals.',
          deliverable_title: 'Interactive Web App',
          deliverable_criteria: 'Build semantic web app.',
          estimated_hours: 16,
          status: 'COMPLETED',
          is_remedial: false,
          resources: [],
          created_at: new Date().toISOString(),
        },
      ],
      created_at: new Date().toISOString(),
    }),
  },
}));

describe('Career and Roadmap Feature Views', () => {
  it('renders CareerPathView with header and analysis elements', async () => {
    render(<CareerPathView />);
    const el = await screen.findByText(/Career Intelligence & Skill Gap Engine/i);
    expect(el).toBeDefined();
  });

  it('renders RoadmapView with active pathway details', async () => {
    render(<RoadmapView />);
    const el1 = await screen.findByText(/Personalized Pathway: Full Stack Developer/i);
    const el2 = await screen.findByText(/25% COMPLETED/i);
    expect(el1).toBeDefined();
    expect(el2).toBeDefined();
  });
});
