/** Public response contracts used by the shell; no admin or CRM fields. */
export interface SiteSettings {
  company_name: string;
  tagline: string;
  about_short: string;
  response_time: string;
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
  team_size: string;
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

export interface SEO {
  meta_title: string;
  meta_description: string;
  og_image: string | null;
  noindex: boolean;
  updated_at: string;
}
export interface Industry {
  name: string;
  slug: string;
  icon: string;
  description: string;
}
export interface Feature {
  title: string;
  description: string;
  icon: string;
  order: number;
}
export interface FAQ {
  question: string;
  answer: string;
}
export interface Metric {
  label: string;
  value: string;
  unit: string;
}
export interface GalleryImage {
  image: string;
  caption: string;
  order: number;
}
export interface Testimonial {
  client_name: string;
  client_role: string;
  client_company: string;
  company_logo: string | null;
  quote: string;
  rating: number;
  is_featured: boolean;
}
export interface TeamMember {
  name: string;
  role: string;
  bio: string;
  photo: string | null;
  linkedin: string;
  github: string;
}
export interface Video {
  slug: string;
  title: string;
  description: string;
  orientation: "landscape" | "portrait";
  source: "youtube" | "vimeo" | "file";
  external_url: string;
  video_file: string | null;
  poster_image: string | null;
  duration_seconds: number | null;
  captions_url: string;
  published_at: string | null;
}
export interface SpecificItem {
  slug?: string;
  title?: string;
  name?: string;
  description?: string;
  summary?: string;
  objective?: string;
  results?: string;
  example_prompt?: string;
  features?: string;
  logo?: string | null;
  thumbnail?: string | null;
  cover_image?: string | null;
  icon_image?: string | null;
  client_name?: string;
  issuer?: string;
  handle?: string;
  platform?: string;
  platforms?: string[] | string;
  url?: string;
  external_url?: string;
  credential_url?: string;
  app_store_url?: string;
  play_store_url?: string;
  file?: string | null;
  screenshots?: GalleryImage[];
  industry?: Industry | null;
  reach?: number | null;
  conversions?: number | null;
  engagement_rate?: string | null;
  downloads?: number | null;
  rating?: string | null;
  follower_count?: number | null;
}
export interface ServiceDetail extends ServiceSummary, SEO {
  hero_headline: string;
  hero_subline: string;
  body: string;
  offerings: Feature[];
  process_steps: Feature[];
  faqs: FAQ[];
  tools: ToolSummary[];
  industries: Industry[];
  stats: Metric[];
  testimonials: Testimonial[];
  case_studies: CaseSummary[];
  products: ProductSummary[];
  videos: Video[];
  specific_content: Record<string, SpecificItem[]>;
}
export interface ProductDetail extends ProductSummary, SEO {
  body: string;
  demo_url: string;
  docs_url: string;
  features: Feature[];
  gallery: GalleryImage[];
  videos: Video[];
  industries: Industry[];
}
export interface CaseSummary {
  title: string;
  slug: string;
  client_name: string;
  client_logo: string | null;
  industry: Industry | null;
  country: string;
  cover_image: string | null;
  service: ServiceSummary | null;
  is_featured: boolean;
}
export interface CaseDetail extends CaseSummary, SEO {
  challenge: string;
  solution: string;
  outcome: string;
  project_url: string;
  duration_months: number | null;
  metrics: Metric[];
  gallery: GalleryImage[];
  tech_stack: ToolSummary[];
  videos: Video[];
}
export interface Category {
  name: string;
  slug: string;
  description?: string;
}
export interface PostSummary {
  title: string;
  slug: string;
  excerpt: string;
  cover_image: string | null;
  author: TeamMember | null;
  service: ServiceSummary | null;
  category: Category | null;
  tags: Category[];
  reading_minutes: number;
  is_featured: boolean;
  published_at: string | null;
}
export interface PostDetail extends PostSummary, SEO {
  body: string;
}
export interface HomeContent {
  case_studies: CaseSummary[];
  products: ProductSummary[];
  posts: PostSummary[];
  industries: Industry[];
  tools: ToolSummary[];
  certifications: SpecificItem[];
  compliance_standards: SpecificItem[];
}
export interface SitemapEntry {
  url: string;
  locale: string;
  lastmod: string | null;
  alternates: Record<string, string>;
}
