-- Additional SQL functions for Epistemic Citadel

-- Function to update user reputation atomically
create or replace function update_user_reputation(
  user_id uuid,
  amount numeric
)
returns void
language plpgsql
security definer
as $$
begin
  update users
  set reputation_score = reputation_score + amount
  where id = user_id;
end;
$$;

-- Function to get post quality metrics
create or replace function get_post_metrics(post_id uuid)
returns table (
  total_interactions bigint,
  saves_count bigint,
  cites_count bigint,
  reactions_count bigint,
  quality_score numeric,
  maturity_score numeric,
  age_hours numeric
)
language plpgsql
as $$
begin
  return query
  select
    count(i.id) as total_interactions,
    count(i.id) filter (where i.type = 'save') as saves_count,
    count(i.id) filter (where i.type = 'cite') as cites_count,
    count(i.id) filter (where i.type = 'reaction') as reactions_count,
    p.quality_score,
    p.maturity_score,
    extract(epoch from (now() - p.created_at)) / 3600 as age_hours
  from posts p
  left join interactions i on i.post_id = p.id
  where p.id = post_id
  group by p.id, p.quality_score, p.maturity_score, p.created_at;
end;
$$;

-- Function to get user's active stakes
create or replace function get_user_active_stakes(user_id uuid)
returns table (
  stake_id uuid,
  post_id uuid,
  amount numeric,
  created_at timestamp with time zone,
  post_quality_score numeric,
  post_maturity_score numeric,
  is_escrowed boolean,
  estimated_roi numeric
)
language plpgsql
as $$
begin
  return query
  select
    s.id as stake_id,
    s.post_id,
    s.amount,
    s.created_at,
    p.quality_score as post_quality_score,
    p.maturity_score as post_maturity_score,
    p.is_escrowed,
    case 
      when s.amount > 0 then p.quality_score / s.amount
      else 0
    end as estimated_roi
  from stakes s
  join posts p on p.id = s.post_id
  where s.user_id = user_id
    and s.status = 'active'
  order by s.created_at desc;
end;
$$;

-- Function to get the "slow feed" - posts that yielded positive ROI
create or replace function get_slow_feed(days_ago integer default 3)
returns table (
  post_id uuid,
  external_ref_id text,
  content text,
  quality_score numeric,
  total_stakes numeric,
  average_roi numeric,
  created_at timestamp with time zone
)
language plpgsql
as $$
begin
  return query
  select
    p.id as post_id,
    p.external_ref_id,
    p.content,
    p.quality_score,
    count(s.id) as total_stakes,
    avg(p.quality_score / s.amount) as average_roi,
    p.created_at
  from posts p
  join stakes s on s.post_id = p.id
  where p.created_at >= now() - (days_ago || ' days')::interval
    and s.status = 'yielded'
    and p.quality_score > 1.0
  group by p.id, p.external_ref_id, p.content, p.quality_score, p.created_at
  order by average_roi desc
  limit 100;
end;
$$;

-- Function to calculate noise-to-signal ratio for filtering
create or replace function calculate_noise_signal_ratio(post_id uuid)
returns numeric
language plpgsql
as $$
declare
  reactions_count bigint;
  saves_cites_count bigint;
begin
  select
    count(*) filter (where type = 'reaction'),
    count(*) filter (where type in ('save', 'cite'))
  into reactions_count, saves_cites_count
  from interactions
  where post_id = post_id;
  
  if saves_cites_count = 0 then
    if reactions_count > 0 then
      return 999999; -- Effectively infinity
    else
      return 0;
    end if;
  end if;
  
  return reactions_count::numeric / saves_cites_count::numeric;
end;
$$;

-- View for dashboard metrics
create or replace view user_dashboard_metrics as
select
  u.id as user_id,
  u.username,
  u.reputation_score,
  u.natural_frequency,
  count(distinct s.id) as total_stakes,
  count(distinct s.id) filter (where s.status = 'active') as active_stakes,
  count(distinct s.id) filter (where s.status = 'yielded') as yielded_stakes,
  count(distinct s.id) filter (where s.status = 'slashed') as slashed_stakes,
  coalesce(sum(s.amount) filter (where s.status = 'active'), 0) as total_staked,
  coalesce(avg(p.quality_score) filter (where s.status = 'yielded'), 0) as avg_yield_quality
from users u
left join stakes s on s.user_id = u.id
left join posts p on p.id = s.post_id
group by u.id, u.username, u.reputation_score, u.natural_frequency;
