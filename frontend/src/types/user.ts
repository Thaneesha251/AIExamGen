import { User, UserRole } from './auth';

export interface UserCreateData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  registration_number?: string;
  employee_id?: string;
  department_id?: string;
  is_active?: boolean;
}

export interface UserUpdateData {
  first_name?: string;
  last_name?: string;
  registration_number?: string;
  employee_id?: string;
  department_id?: string;
  is_active?: boolean;
}

export interface UserProfileUpdateData {
  first_name?: string;
  last_name?: string;
}

export interface UserFilterOptions {
  search?: string;
  role?: UserRole;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export interface UserListResponseData {
  total: number;
  items: User[];
  page: number;
  page_size: number;
}
