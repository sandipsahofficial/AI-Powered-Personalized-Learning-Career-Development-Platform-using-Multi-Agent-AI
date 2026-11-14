export type UserRole = 'STUDENT' | 'MENTOR' | 'ORG_ADMIN' | 'SYS_ADMIN';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active?: boolean;
  is_verified?: boolean;
  organization_id?: string | null;
  created_at?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  full_name: string;
  email: string;
  password: string;
  confirm_password?: string;
  role: UserRole;
}
