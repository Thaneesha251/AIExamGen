export type UserRole = 'ADMIN' | 'FACULTY' | 'STUDENT';

export interface UserRoleSchema {
  id: string;
  name: UserRole;
  description?: string;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  registration_number?: string | null;
  employee_id?: string | null;
  department_id?: string | null;
  role_id: string;
  role?: UserRoleSchema | null;
  role_name?: UserRole;
  is_active: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  registration_number?: string;
  department_id?: string;
}

export interface ChangePasswordCredentials {
  current_password: string;
  new_password: string;
}

export interface TokenData {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    role: UserRole;
    registration_number?: string | null;
    employee_id?: string | null;
  };
}

export interface AuthApiResponse {
  success: boolean;
  data: TokenData;
}
