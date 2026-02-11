# Deployment Guide - Epistemic Citadel

This guide walks you through deploying the complete Epistemic Citadel system, from database setup to Chrome extension installation.

---

## Phase 1: Database Setup (Backend)

### 1.1 Create Supabase Project

1. Go to [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Click "New Project"
3. Fill in the details:
   - **Name:** `epistemic-citadel`
   - **Database Password:** Choose a strong password (save it!)
   - **Region:** Select closest to your users
4. Click "Create new project"
5. Wait for the project to be provisioned (~2 minutes)

### 1.2 Initialize Database Schema

1. In your Supabase dashboard, navigate to **SQL Editor**
2. Click "New Query"
3. Copy the entire contents of `schema.sql`
4. Paste into the editor
5. Click "Run" (or press Cmd/Ctrl + Enter)
6. Verify success: You should see "Success. No rows returned"

### 1.3 Add SQL Functions

1. In the SQL Editor, create another new query
2. Copy the entire contents of `functions.sql`
3. Paste into the editor
4. Click "Run"
5. Verify: Navigate to **Database → Functions** to see the new functions

### 1.4 Seed Genesis Architects (Optional)

To create 50 test users:

```sql
INSERT INTO users (username, reputation_score, natural_frequency)
SELECT 
  'architect_' || generate_series,
  100.0 + (random() * 50),
  0.01 + (random() * 0.02)
FROM generate_series(1, 50);
```

### 1.5 Get API Credentials

1. Navigate to **Project Settings → API**
2. Copy these values (you'll need them later):
   - **Project URL:** `https://[your-project-ref].supabase.co`
   - **anon public key:** Your public API key
   - **service_role key:** Your private API key (keep secret!)

---

## Phase 2: Edge Functions Deployment

### 2.1 Install Supabase CLI

```bash
npm install -g supabase
```

Or with Homebrew (macOS):
```bash
brew install supabase/tap/supabase
```

### 2.2 Login to Supabase

```bash
supabase login
```

This will open a browser window for authentication.

### 2.3 Link to Your Project

```bash
cd /path/to/epistemic-citadel
supabase link --project-ref your-project-ref
```

Replace `your-project-ref` with the reference from your project URL.

### 2.4 Deploy Edge Functions

```bash
# Deploy quality scoring function
supabase functions deploy update-quality-scores

# Deploy payout processing function
supabase functions deploy process-payouts
```

### 2.5 Set Environment Variables

```bash
# Set Supabase URL
supabase secrets set SUPABASE_URL=https://your-project-ref.supabase.co

# Set service role key
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### 2.6 Test Edge Functions

```bash
# Test quality scoring
curl -X POST \
  'https://your-project-ref.supabase.co/functions/v1/update-quality-scores' \
  -H 'Authorization: Bearer YOUR_SERVICE_ROLE_KEY'

# Test payout processing
curl -X POST \
  'https://your-project-ref.supabase.co/functions/v1/process-payouts' \
  -H 'Authorization: Bearer YOUR_SERVICE_ROLE_KEY'
```

---

## Phase 3: Cron Jobs Setup

### 3.1 Enable pg_cron Extension

In Supabase SQL Editor:

```sql
create extension if not exists pg_cron;
```

### 3.2 Schedule Quality Score Updates (Every Hour)

```sql
select cron.schedule(
  'update-quality-scores-hourly',
  '0 * * * *',
  $$
  select net.http_post(
    url := 'https://your-project-ref.supabase.co/functions/v1/update-quality-scores',
    headers := jsonb_build_object(
      'Authorization', 'Bearer YOUR_SERVICE_ROLE_KEY'
    )
  );
  $$
);
```

### 3.3 Schedule Payout Processing (Every 6 Hours)

```sql
select cron.schedule(
  'process-payouts-6h',
  '0 */6 * * *',
  $$
  select net.http_post(
    url := 'https://your-project-ref.supabase.co/functions/v1/process-payouts',
    headers := jsonb_build_object(
      'Authorization', 'Bearer YOUR_SERVICE_ROLE_KEY'
    )
  );
  $$
);
```

### 3.4 Verify Cron Jobs

```sql
select * from cron.job;
```

You should see both jobs listed.

---

## Phase 4: Chrome Extension Configuration

### 4.1 Update Configuration Files

Replace the placeholder values in these files:

**In `content.js`:**
```javascript
const SUPABASE_URL = 'https://your-project-ref.supabase.co';
const SUPABASE_ANON_KEY = 'your-anon-public-key';
```

**In `background.js`:**
```javascript
const SUPABASE_URL = 'https://your-project-ref.supabase.co';
const SUPABASE_ANON_KEY = 'your-anon-public-key';
```

**In `popup.js`:**
```javascript
const SUPABASE_URL = 'https://your-project-ref.supabase.co';
const SUPABASE_ANON_KEY = 'your-anon-public-key';
```

### 4.2 Install Dependencies (Optional)

If you want to use TypeScript compilation:

```bash
cd /path/to/epistemic-citadel
npm install
npm run build
```

---

## Phase 5: Load Extension in Chrome

### 5.1 Enable Developer Mode

1. Open Chrome
2. Navigate to `chrome://extensions/`
3. Toggle "Developer mode" (top right corner)

### 5.2 Load Unpacked Extension

1. Click "Load unpacked"
2. Navigate to the `epistemic-citadel` directory
3. Click "Select Folder"
4. The extension should now appear in your extensions list

### 5.3 Verify Installation

1. Click the extension icon (should appear in your toolbar)
2. You should see the onboarding screen
3. Create an account with a username
4. Navigate to Twitter/X
5. You should see Shield icons next to tweet actions

---

## Phase 6: Testing

### 6.1 Test Staking

1. Go to Twitter/X
2. Find any tweet
3. Click the Shield icon
4. Enter an amount (e.g., 10)
5. Click "Stake"
6. Verify in Supabase dashboard:
   - Navigate to **Table Editor → stakes**
   - You should see your new stake

### 6.2 Test Dashboard

1. Click the extension icon
2. Verify your reputation decreased by the staked amount
3. Check "Active Stakes" section
4. You should see your stake listed

### 6.3 Test Quality Scoring

Manually trigger the quality scoring function:

```bash
curl -X POST \
  'https://your-project-ref.supabase.co/functions/v1/update-quality-scores' \
  -H 'Authorization: Bearer YOUR_SERVICE_ROLE_KEY'
```

Check the response for updated post counts.

### 6.4 Test Filtering

1. Create a test post in Supabase with:
   - `external_ref_id`: A real tweet ID
   - `quality_score`: 0.3 (low quality)
2. Navigate to that tweet on Twitter/X
3. If it has high velocity (>100 likes in <10 min), it should be blurred

---

## Phase 7: Production Checklist

Before launching to users:

- [ ] Database schema is deployed
- [ ] All SQL functions are created
- [ ] Edge functions are deployed and tested
- [ ] Cron jobs are scheduled and running
- [ ] Extension configuration is updated with production values
- [ ] Icons are replaced with final designs
- [ ] Extension is tested on multiple tweets
- [ ] Dashboard displays correct data
- [ ] Reputation calculations are accurate
- [ ] Filtering logic works as expected
- [ ] Error handling is in place
- [ ] Privacy policy is created (if collecting user data)
- [ ] Terms of service are created

---

## Troubleshooting

### Extension Not Loading

- Check Chrome console for errors: `chrome://extensions/` → Click "Errors"
- Verify manifest.json is valid
- Ensure all file paths are correct

### Database Connection Errors

- Verify Supabase URL and API keys are correct
- Check Supabase dashboard for service status
- Ensure Row Level Security policies allow access

### Edge Functions Not Running

- Check function logs in Supabase dashboard
- Verify environment variables are set
- Test functions manually with curl

### Cron Jobs Not Executing

- Check `cron.job_run_details` table for execution history
- Verify pg_cron extension is enabled
- Ensure service role key is correct in cron job

---

## Monitoring

### Database Metrics

Monitor in Supabase Dashboard → Database → Reports:
- Query performance
- Table sizes
- Index usage

### Edge Function Logs

View in Supabase Dashboard → Edge Functions → Logs:
- Execution count
- Error rate
- Response times

### Extension Usage

Track in your analytics:
- Active users
- Stakes created
- Reputation changes
- Filter applications

---

## Next Steps

After successful deployment:

1. **Gather Feedback:** Share with the 50 Genesis Architects
2. **Tune Parameters:** Adjust decay rates, thresholds based on real data
3. **Optimize Performance:** Add caching, optimize queries
4. **Enhance Features:** Add more filtering options, analytics
5. **Scale:** Prepare for larger user base

---

**You are cleared to engage.**
