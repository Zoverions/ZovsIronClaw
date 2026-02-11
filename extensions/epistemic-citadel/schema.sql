-- OPERATION: EPISTEMIC CITADEL
-- Database Schema for Shadow Graph
-- This schema supports the Proof-of-Integration reputation staking system

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- 1. USERS (The Architects)
-- Stores user reputation and natural frequency metrics
create table users (
  id uuid primary key default uuid_generate_v4(),
  username text unique not null,
  reputation_score numeric default 100.0, -- The "Energy" of the system
  natural_frequency numeric default 0.01, -- Inferred integration latency (Hz)
  created_at timestamp with time zone default now()
);

-- 2. POSTS (The Signal)
-- Note: In Phase 1, 'content' might just be a reference to an external Tweet ID
create table posts (
  id uuid primary key default uuid_generate_v4(),
  author_id uuid references users(id),
  external_ref_id text, -- ID of the Tweet being "Staked" on
  content text, 
  created_at timestamp with time zone default now(),
  maturity_score numeric default 0.0, -- Function of Age
  quality_score numeric default 0.0,  -- Function of Interactions
  is_escrowed boolean default true    -- True until age > 72h
);

-- 3. STAKES (The Bet)
-- Tracks reputation stakes on posts
create table stakes (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references users(id),
  post_id uuid references posts(id),
  amount numeric not null check (amount > 0),
  status text default 'active', -- 'active', 'slashed', 'yielded'
  created_at timestamp with time zone default now()
);

-- 4. INTERACTIONS (The Feedback)
-- Tracks user interactions with posts (saves, cites, reactions)
create table interactions (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references users(id),
  post_id uuid references posts(id),
  type text not null, -- 'save', 'cite', 'reaction'
  weight numeric default 1.0,
  created_at timestamp with time zone default now()
);

-- Indexes for performance
create index idx_posts_external_ref on posts(external_ref_id);
create index idx_posts_created_at on posts(created_at);
create index idx_stakes_user_id on stakes(user_id);
create index idx_stakes_post_id on stakes(post_id);
create index idx_interactions_post_id on interactions(post_id);
create index idx_interactions_user_id on interactions(user_id);

-- Row Level Security (RLS) policies
alter table users enable row level security;
alter table posts enable row level security;
alter table stakes enable row level security;
alter table interactions enable row level security;

-- Allow users to read all data
create policy "Users can view all users" on users for select using (true);
create policy "Users can view all posts" on posts for select using (true);
create policy "Users can view all stakes" on stakes for select using (true);
create policy "Users can view all interactions" on interactions for select using (true);

-- Allow users to insert their own data
create policy "Users can insert their own stakes" on stakes for insert with check (true);
create policy "Users can insert their own interactions" on interactions for insert with check (true);
create policy "Users can insert posts" on posts for insert with check (true);

-- Allow users to update their own data
create policy "Users can update their own reputation" on users for update using (true);
create policy "Users can update posts" on posts for update using (true);
create policy "Users can update stakes" on stakes for update using (true);
