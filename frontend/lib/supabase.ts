import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Database types for TypeScript
export interface MonitoredProfile {
  id: number
  url: string
  name: string | null
  active: boolean
  added_at: string
  last_checked: string | null
}

export interface Profile {
  url: string
  name: string | null
  headline: string | null
  current_position: string | null
  current_company: string | null
  last_updated: string | null
}

export interface JobChange {
  id: number
  profile_url: string
  name: string | null
  old_position: string | null
  old_company: string | null
  new_position: string | null
  new_company: string | null
  detected_at: string
  notified: boolean
}