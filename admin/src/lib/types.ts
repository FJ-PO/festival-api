export type Role = 'admin' | 'organizer' | 'staff' | 'customer'

export interface User {
  id: number
  email: string
  username: string | null
  full_name: string
  role: Role
  is_active: boolean
  created_at: string
}

export interface PageOf<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

export interface Venue {
  id: number
  name: string
  address: string
  municipality: string
  capacity: number
  latitude: number | null
  longitude: number | null
}

export interface Artist {
  id: number
  name: string
  genre: string | null
  country: string | null
  bio: string | null
  image_url: string | null
}

export interface Performance {
  id: number
  festival_id: number
  stage: string
  start_time: string
  end_time: string
  artist: Artist
}

export interface Festival {
  id: number
  name: string
  slug: string
  description: string | null
  genre: string | null
  start_date: string
  end_date: string
  image_url: string | null
  min_age: number
  status: 'draft' | 'published' | 'cancelled' | 'finished'
  venue: Venue
  organizer: { id: number; full_name: string }
  created_at: string
  price_from: string | null
}

export interface FestivalDetail extends Festival {
  performances: Performance[]
}

export interface TicketType {
  id: number
  festival_id: number
  name: string
  description: string | null
  price: string
  quantity_total: number
  quantity_sold: number
  quantity_available: number
  max_per_order: number
  sale_start: string | null
  sale_end: string | null
  is_active: boolean
}

export interface OrderItem {
  id: number
  ticket_type_id: number
  ticket_type_name: string
  quantity: number
  unit_price: string
}

export interface Order {
  id: number
  user_id: number
  festival_id: number
  festival_name: string
  status: 'pending' | 'paid' | 'cancelled' | 'expired' | 'refunded'
  subtotal: string
  discount_amount: string
  total: string
  payment_method: string | null
  payment_reference: string | null
  created_at: string
  expires_at: string
  paid_at: string | null
  items: OrderItem[]
}

export interface Ticket {
  id: number
  code: string
  order_id: number
  festival_id: number
  festival_name: string
  festival_start_date: string
  ticket_type_id: number
  ticket_type_name: string
  owner_id: number
  attendee_name: string
  status: 'valid' | 'used' | 'cancelled'
  issued_at: string
  checked_in_at: string | null
}

export interface SiteSettings {
  site_name: string
  tagline: string
  hero_kicker: string
  hero_title: string
  hero_subtitle: string
  hero_image_url: string | null
  hero_cta_text: string
  hero_cta_link: string
  featured_festival_id: number | null
  announcement: string | null
  about_title: string
  about_text: string
  contact_email: string | null
  contact_phone: string | null
  accent_color: string
  social: Partial<Record<'instagram' | 'facebook' | 'x' | 'youtube' | 'tiktok' | 'spotify', string | null>>
  footer_text: string
}

export interface ContentItem {
  id: number
  title: string
  slug: string
  excerpt: string | null
  content: string
  cover_image_url: string | null
  status: 'draft' | 'published'
  created_at: string
  updated_at: string
  published_at: string | null
  author: { id: number; full_name: string } | null
}

export interface CmsPage extends ContentItem {
  show_in_menu: boolean
  menu_order: number
}

export interface Post extends ContentItem {
  festival_id: number | null
}

export interface MediaItem {
  id: number
  url: string
  filename: string
  original_name: string
  content_type: string
  size: number
  alt: string | null
  created_at: string
}

export interface DiscountCode {
  id: number
  festival_id: number
  code: string
  percent_off: number
  max_uses: number | null
  times_used: number
  valid_until: string | null
  is_active: boolean
}

export interface Subscriber {
  id: number
  email: string
  name: string | null
  created_at: string
}

export interface Dashboard {
  festivals_by_status: Record<string, number>
  users_by_role: Record<string, number>
  revenue: string
  orders_paid: number
  tickets_sold: number
  tickets_checked_in: number
  artists: number
  venues: number
  pages: number
  posts: number
  sales_last_30_days: { day: string; revenue: string; orders: number }[]
  recent_orders: { id: number; festival_name: string; customer: string; total: string; status: string; created_at: string }[]
}

export interface FestivalStats {
  festival_id: number
  festival_name: string
  revenue: string
  orders_by_status: Record<string, number>
  tickets_issued: number
  tickets_checked_in: number
  attendance_rate: number
  ticket_types: { ticket_type_id: number; name: string; price: string; quantity_total: number; quantity_sold: number; quantity_available: number }[]
}

export interface CheckInResult {
  accepted: boolean
  reason: 'ok' | 'not_found' | 'already_used' | 'cancelled' | 'wrong_festival'
  message: string
  ticket: Ticket | null
}
