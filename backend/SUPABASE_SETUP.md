# Supabase Setup Guide

## 🚀 Quick Setup

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Sign up / Log in
3. Click "New Project"
4. Choose organization and name your project
5. Set a strong database password
6. Select region (choose closest to you)
7. Click "Create new project" (takes ~2 minutes)

### 2. Get Your Credentials

Once your project is ready:

1. Go to **Settings** → **API**
2. Copy your credentials:
   - **Project URL** (looks like: `https://xxxxx.supabase.co`)
   - **anon/public key** (starts with `eyJ...`)
   - **service_role key** (also starts with `eyJ...`)

### 3. Run Database Migration

1. In your Supabase dashboard, go to **SQL Editor**
2. Click "New Query"
3. Copy the entire contents of `supabase_schema.sql`
4. Paste into the editor
5. Click "Run" or press Cmd/Ctrl + Enter

You should see a success message and 4 tables created:
- `profiles`
- `job_history`
- `scrape_history`
- `job_changes`

### 4. Configure Your .env File

Add these to your `.env` file:

```env
# Supabase Database
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-public-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here
```

**Important:** Use the **service_role** key for the scraper (bypasses Row Level Security)

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Test Connection

```bash
python -c "from database import Database; db = Database(); print('✅ Connected!')"
```

## 🔐 Security Recommendations

### Option 1: Use Service Role Key (Recommended for Scripts)
- Use `SUPABASE_SERVICE_KEY` in your `.env`
- Bypasses Row Level Security (RLS)
- Full database access
- Keep this key SECRET

### Option 2: Use Anon Key with RLS Disabled
- Use `SUPABASE_KEY` (anon key)
- Don't enable RLS policies in the SQL
- Good for simple projects

### Option 3: Use Anon Key with RLS Policies
- Enable RLS in `supabase_schema.sql` (uncomment lines)
- Create policies for authenticated access
- Most secure for multi-user apps

## 📊 View Your Data

### In Supabase Dashboard:
1. Go to **Table Editor**
2. Select a table (profiles, job_changes, etc.)
3. View, edit, filter data in GUI

### Via SQL:
1. Go to **SQL Editor**
2. Run queries:

```sql
-- View all profiles
SELECT * FROM profiles ORDER BY last_updated DESC;

-- View job changes
SELECT 
    name,
    old_position || ' at ' || old_company as previous,
    new_position || ' at ' || new_company as current,
    detected_at
FROM job_changes
ORDER BY detected_at DESC;

-- View scrape history
SELECT 
    profile_url,
    success,
    scraped_at,
    error_message
FROM scrape_history
ORDER BY scraped_at DESC
LIMIT 50;
```

## 🔄 Migrating from SQLite

If you were using SQLite before and want to migrate your data:

```bash
# Export from SQLite (if you have existing data)
sqlite3 linkedin_monitor.db .dump > backup.sql

# Then manually insert into Supabase via SQL Editor
# or create a Python migration script
```

## 🆘 Troubleshooting

### "Could not connect to Supabase"
- Check your `SUPABASE_URL` is correct
- Verify `SUPABASE_KEY` or `SUPABASE_SERVICE_KEY` is set
- Make sure your `.env` file is in the project root

### "relation does not exist"
- Run the `supabase_schema.sql` migration
- Check you're using the correct project in Supabase

### "permission denied"
- Use `SUPABASE_SERVICE_KEY` instead of `SUPABASE_KEY`
- Or disable RLS on your tables

### "Import supabase could not be resolved"
- Run: `pip install supabase>=2.0.0`
- Make sure you're in your virtual environment

## 📈 Benefits of Supabase

✅ **Remote Access** - Query from anywhere  
✅ **Real-time** - Set up subscriptions for live updates  
✅ **GUI Dashboard** - Easy data viewing and management  
✅ **Automatic Backups** - Built-in with paid plans  
✅ **Scalable** - PostgreSQL can handle much more data  
✅ **Multi-user** - Share access with team members  
✅ **API** - REST and GraphQL APIs auto-generated  

## 🎯 Next Steps

Once configured, your scraper will automatically:
1. Connect to Supabase on startup
2. Store all profiles in the cloud
3. Track job changes in real-time
4. Keep audit logs of all scrapes

Run your scraper as usual:
```bash
python main.py once
```

Check your Supabase dashboard to see data flowing in! 🎉
