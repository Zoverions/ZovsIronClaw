# Epistemic Citadel - Chrome Extension

**Mission:** Deploy a "Class III" communications protocol designed to filter high-frequency noise and amplify low-frequency wisdom.

**Core Mechanism:** Proof-of-Integration (Reputation Staking + Temporal Escrow).

**Current Phase:** Phase 1 – The "Parasitic" Browser Extension (Overlay on Twitter/X).

---

## Overview

Epistemic Citadel is a Chrome extension that implements a reputation-staking system for Twitter/X. It allows users to stake their reputation on tweets they believe will age well, creating a "Shadow Graph" that filters noise and amplifies signal over time.

### The Problem
Current platforms suffer from "Aliasing"—they sample reality too fast, mistaking noise for signal.

### The Solution
An **Inverse Filter**. We do not block content; we delay it. We monetize patience.

### The Metric
Value is not `Engagement` (Amplitude). Value is `Relevance` integrated over time.

---

## Architecture

```
┌─────────────────────────────────────────┐
│     Chrome Extension (Frontend)         │
│  ┌─────────────────────────────────┐   │
│  │ Content Script: Twitter Overlay │   │
│  │ - Shield Button Injection       │   │
│  │ - Acoustic Filtering            │   │
│  │ - Staking Modal                 │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ Popup: Dashboard                │   │
│  │ - Reputation Wallet             │   │
│  │ - Active Stakes                 │   │
│  │ - The Slow Feed                 │   │
│  └─────────────────────────────────┘   │
└──────────────────┬──────────────────────┘
                   │ REST API
                   ▼
┌─────────────────────────────────────────┐
│      Supabase (Backend)                 │
│  ┌─────────────────────────────────┐   │
│  │ PostgreSQL Database             │   │
│  │ - Users (Reputation)            │   │
│  │ - Posts (Quality Scores)        │   │
│  │ - Stakes (Bets)                 │   │
│  │ - Interactions (Feedback)       │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ Edge Functions                  │   │
│  │ - Update Quality Scores (Hourly)│   │
│  │ - Process Payouts (6h)          │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## Features

### 1. Reputation Staking
- Stake reputation on tweets you believe will age well
- 72-hour escrow period for content to mature
- Earn reputation if the tweet gains quality interactions (saves, cites)
- Lose reputation if it was just noise

### 2. Acoustic Filtering
- Automatically blur high-velocity, low-quality tweets
- High Velocity = >100 likes in <10 minutes
- Low Quality = Shadow Quality Score < 0.5
- Tooltip explains why content is filtered

### 3. The Slow Feed
- Curated feed of tweets that yielded positive ROI
- Only shows content staked 3+ days ago
- Sorted by average ROI across all stakes

### 4. Quality Integral Algorithm
The "Physics" of the system:

**Quality Score (Q):**
```
Q = maturity_score × interaction_value

where:
  maturity_score = log(1 + age_hours / 24)
  interaction_value = Σ (saves + cites) × √t - reactions × e^(-t)
```

**Payout Function (at t = 72h):**
```
ROI = Q / stake_amount

if Q > threshold:
  return stake + yield (Yield)
else if Q < 0:
  burn stake (Slash)
else:
  return stake (Neutral)
```

---

## Installation

### Prerequisites
1. **Supabase Account** - Sign up at [supabase.com](https://supabase.com)
2. **Chrome Browser** - Version 88 or higher

### Step 1: Set Up Supabase

1. Follow the instructions in `SUPABASE_SETUP.md`
2. Create a new Supabase project
3. Run the SQL schema from `schema.sql`
4. Run the SQL functions from `functions.sql`
5. Deploy the Edge Functions from `supabase/functions/`

### Step 2: Configure the Extension

1. Open `content.js` and replace:
   ```javascript
   const SUPABASE_URL = 'YOUR_SUPABASE_URL';
   const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY';
   ```

2. Open `background.js` and replace the same values

3. Open `popup.js` and replace the same values

### Step 3: Load the Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `epistemic-citadel` directory
5. The extension should now appear in your extensions list

### Step 4: Set Up Your Account

1. Click the extension icon in your Chrome toolbar
2. Enter a username
3. Click "Create Account"
4. Your reputation wallet will be initialized with 100 points

---

## Usage

### Staking on a Tweet

1. Navigate to Twitter/X
2. Find a tweet you believe will age well
3. Click the **Shield** icon next to the Like/Retweet buttons
4. Enter the amount of reputation you want to stake (1-100)
5. Optionally, add a thesis explaining why you believe in this content
6. Click "Stake"

Your reputation will be locked for 72 hours. After that, the system will calculate the quality score and determine your payout.

### Viewing Your Stakes

1. Click the extension icon
2. View your active stakes in the dashboard
3. See estimated ROI and quality scores
4. Monitor maturity progress

### The Slow Feed

1. Click the extension icon
2. Scroll to "The Slow Feed" section
3. View tweets that have matured and yielded positive ROI
4. Click any item to open the tweet on Twitter

---

## Development

### Project Structure

```
epistemic-citadel/
├── manifest.json              # Extension manifest (V3)
├── content.js                 # Content script (Twitter overlay)
├── content.css                # Content script styles
├── background.js              # Background service worker
├── popup.html                 # Popup dashboard HTML
├── popup.css                  # Popup dashboard styles
├── popup.js                   # Popup dashboard logic
├── quality-scoring.ts         # Algorithmic logic (TypeScript)
├── schema.sql                 # Database schema
├── functions.sql              # SQL functions
├── icons/                     # Extension icons
│   ├── icon16.png
│   ├── icon32.png
│   ├── icon48.png
│   └── icon128.png
└── supabase/
    └── functions/
        ├── update-quality-scores/
        │   └── index.ts
        └── process-payouts/
            └── index.ts
```

### Testing

1. **Manual Testing:**
   - Load the extension in Chrome
   - Navigate to Twitter/X
   - Test staking on tweets
   - Verify filtering behavior
   - Check dashboard updates

2. **Database Testing:**
   - Use Supabase SQL Editor to query data
   - Verify quality scores are updating
   - Check payout calculations

3. **Edge Function Testing:**
   - Use Supabase Functions dashboard
   - Manually trigger functions
   - Check logs for errors

### Deployment

#### Deploy Edge Functions

```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref your-project-ref

# Deploy functions
supabase functions deploy update-quality-scores
supabase functions deploy process-payouts
```

#### Set Up Cron Jobs

In Supabase Dashboard → Database → Cron Jobs:

```sql
-- Update quality scores every hour
select cron.schedule(
  'update-quality-scores',
  '0 * * * *',
  $$
  select net.http_post(
    url := 'https://your-project-ref.supabase.co/functions/v1/update-quality-scores',
    headers := '{"Authorization": "Bearer YOUR_SERVICE_ROLE_KEY"}'::jsonb
  );
  $$
);

-- Process payouts every 6 hours
select cron.schedule(
  'process-payouts',
  '0 */6 * * *',
  $$
  select net.http_post(
    url := 'https://your-project-ref.supabase.co/functions/v1/process-payouts',
    headers := '{"Authorization": "Bearer YOUR_SERVICE_ROLE_KEY"}'::jsonb
  );
  $$
);
```

---

## Roadmap

### Phase 1: The Parasitic Extension (Current)
- ✅ Chrome extension overlay on Twitter/X
- ✅ Reputation staking mechanism
- ✅ Acoustic filtering
- ✅ Dashboard with Slow Feed

### Phase 2: The Native Platform (Days 11-20)
- Standalone web app (not parasitic)
- Native posting and interaction
- Enhanced analytics and visualizations
- Community features

### Phase 3: The Mesh Network (Days 21-30)
- Decentralized reputation graph
- Cross-platform staking
- API for third-party integrations
- Mobile app

---

## Contributing

This is part of the ZovsIronClaw project. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

MIT License - See LICENSE file in the root of the ZovsIronClaw repository.

---

## Support

For questions or issues:
- Open an issue in the ZovsIronClaw repository
- Join the community discussion

---

**You are cleared to engage.**
