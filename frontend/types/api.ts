// Typed mirrors of the backend Pydantic schemas (see backend/app/schemas/).

// --- Auth ---
export interface UserOut {
  id: string;
  email: string;
  is_active: boolean;
}
export interface Token {
  access_token: string;
  token_type: string;
}

// --- Profile ---
export interface Education {
  id?: string;
  institution: string | null;
  degree: string | null;
  field: string | null;
  start_date: string | null;
  expected_graduation: string | null;
  gpa: number | null;
}
export interface Certification {
  id?: string;
  name: string | null;
  issuer: string | null;
  date: string | null;
  credential_url: string | null;
}
export interface Skill {
  id?: string;
  category: string;
  name: string;
}
export interface Experience {
  id?: string;
  organization: string | null;
  position: string | null;
  start_date: string | null;
  end_date: string | null;
  description: string | null;
  skills_used: string[];
  achievements: string[];
}
export interface Project {
  id?: string;
  name: string | null;
  description: string | null;
  technologies: string[];
  url: string | null;
  github_url: string | null;
  responsibilities: string[];
  achievements: string[];
}
export interface Preferences {
  target_roles: string[];
  job_types: string[];
  internship_types: string[];
  preferred_locations: string[];
  work_modes: string[];
  min_salary: number | null;
  min_stipend: number | null;
  preferred_industries: string[];
  keywords: string[];
  excluded_companies: string[];
  excluded_roles: string[];
  min_match_score: number | null;
}
export interface ProfileOut {
  id: string;
  full_name: string | null;
  phone: string | null;
  country: string | null;
  city: string | null;
  portfolio_url: string | null;
  github_url: string | null;
  linkedin_url: string | null;
  other_links: string[] | null;
  educations: Education[];
  certifications: Certification[];
  skills: Skill[];
  experiences: Experience[];
  projects: Project[];
  preferences: Preferences | null;
}

// --- Resumes ---
export interface Resume {
  id: string;
  label: string;
  original_filename: string;
  file_type: string;
  is_default: boolean;
  created_at: string;
}
export interface ResumeDetail extends Resume {
  parsed_text: string | null;
  structured_data: string | null;
}

// --- Jobs ---
export interface Job {
  id: string;
  source: string;
  source_job_id: string | null;
  url: string;
  company: string | null;
  title: string | null;
  description: string | null;
  location: string | null;
  work_mode: string;
  employment_type: string;
  salary_min: number | null;
  salary_max: number | null;
  currency: string | null;
  required_skills: string[] | null;
  preferred_skills: string[] | null;
  deadline: string | null;
  application_url: string | null;
  status: string;
  posted_at: string | null;
  discovered_at: string | null;
  created_at: string;
}
export interface JobList {
  count: number;
  jobs: Job[];
}
export interface DiscoverResult {
  discovered: number;
  jobs: Job[];
}

// --- Applications ---
export interface Application {
  id: string;
  job_id: string;
  user_id: string;
  status: string;
  resume_id: string | null;
  cover_letter: string | null;
  match_score: number | null;
  match_category: string | null;
  match_reasons: string[];
  created_at: string;
}
export interface StatusEvent {
  id: string;
  application_id: string;
  status: string;
  note: string | null;
  created_at: string;
}

// --- Settings / health ---
export interface RuntimeSettings {
  env: string;
  ai_provider: string;
  ai_model: string;
  ai_embed_model: string;
  job_source_config: string;
  max_upload_mb: number;
  browser_headless: boolean;
  api_prefix: string;
}
export interface Health {
  status: string;
  env: string;
}