/** Public response contracts used by the shell; no admin or CRM fields. */
export interface SiteSettings {
  company_name: string;
  tagline: string;
  about_short: string;
  logo: string | null;
  logo_dark: string | null;
  favicon: string | null;
  address_line_1: string;
  address_line_2: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  service_area: string;
  phone_us: string;
  phone_af: string;
  email: string;
  domain: string;
  founded_year: number | null;
  team_size: number | null;
  linkedin_url: string;
  x_url: string;
  github_url: string;
  instagram_url: string;
  youtube_url: string;
  facebook_url: string;
  ga4_measurement_id: string;
  default_meta_title: string;
  default_meta_description: string;
  default_og_image: string | null;
}
export interface ServiceSummary {
  key: string;
  slug: string;
  name: string;
  icon: string;
  intro: string;
  hero_image: string | null;
}
export interface ToolSummary {
  name: string;
  slug: string;
  logo: string | null;
  category: string;
  url: string;
}
export interface ProductSummary {
  name: string;
  slug: string;
  tagline: string;
  summary: string;
  category: string;
  cover_image: string | null;
  icon: string;
  delivery: string;
  is_featured: boolean;
  tech_stack: ToolSummary[];
  services: ServiceSummary[];
}
export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
