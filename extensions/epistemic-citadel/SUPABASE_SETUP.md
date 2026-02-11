# Supabase Setup Instructions

## Operation: Epistemic Citadel - Database Configuration

### Prerequisites
- Supabase account (free tier is sufficient for Phase 1)
- Access to Supabase SQL Editor

### Setup Steps

#### 1. Create a New Supabase Project
1. Go to [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Click "New Project"
3. Choose a name: `epistemic-citadel`
4. Set a strong database password (save this securely)
5. Select a region close to your users
6. Click "Create new project"

#### 2. Initialize the Database Schema
1. Navigate to the SQL Editor in your Supabase dashboard
2. Create a new query
3. Copy the entire contents of `schema.sql`
4. Paste into the SQL Editor
5. Click "Run" to execute the schema

#### 3. Get Your API Credentials
1. Go to Project Settings → API
2. Copy the following values:
   - **Project URL**: `https://[your-project-ref].supabase.co`
   - **anon/public key**: This is your public API key
   - **service_role key**: This is your private API key (keep secure!)

#### 4. Configure Environment Variables
Create a `.env` file in the `epistemic-citadel` directory:

```env
VITE_SUPABASE_URL=https://[your-project-ref].supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

#### 5. Verify Installation
Run this SQL query in the SQL Editor to verify tables were created:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';
```

You should see: `users`, `posts`, `stakes`, `interactions`

#### 6. Seed Genesis Architects (Optional)
To create 50 initial users for testing:

```sql
INSERT INTO users (username, reputation_score, natural_frequency)
SELECT 
  'architect_' || generate_series,
  100.0 + (random() * 50),
  0.01 + (random() * 0.02)
FROM generate_series(1, 50);
```

### Next Steps
After database setup is complete, proceed to implementing the Edge Functions for quality scoring and payout calculations.
