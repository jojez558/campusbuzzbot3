-- ═══════════════════════════════════════════════════════════
--  CampusBuzz Kenya — PostgreSQL Initialization
--  Run once after tables are created by SQLAlchemy.
--  Adds indexes for query performance.
-- ═══════════════════════════════════════════════════════════

-- Full-text search index on group name + description
CREATE INDEX IF NOT EXISTS idx_groups_search
    ON whatsapp_groups
    USING gin(to_tsvector('english', coalesce(name,'') || ' ' || coalesce(description,'')));

-- University name search
CREATE INDEX IF NOT EXISTS idx_uni_name
    ON universities USING gin(to_tsvector('english', name));

-- Frequently filtered columns
CREATE INDEX IF NOT EXISTS idx_groups_status        ON whatsapp_groups(status);
CREATE INDEX IF NOT EXISTS idx_groups_category      ON whatsapp_groups(category);
CREATE INDEX IF NOT EXISTS idx_groups_university    ON whatsapp_groups(university_id);
CREATE INDEX IF NOT EXISTS idx_groups_is_trending   ON whatsapp_groups(is_trending) WHERE is_trending = true;
CREATE INDEX IF NOT EXISTS idx_groups_is_verified   ON whatsapp_groups(is_verified) WHERE is_verified = true;
CREATE INDEX IF NOT EXISTS idx_groups_is_link_active ON whatsapp_groups(is_link_active);
CREATE INDEX IF NOT EXISTS idx_groups_view_count    ON whatsapp_groups(view_count DESC);

-- Users
CREATE INDEX IF NOT EXISTS idx_users_referral_code  ON users(referral_code);
CREATE INDEX IF NOT EXISTS idx_users_xp             ON users(xp_points DESC);
CREATE INDEX IF NOT EXISTS idx_users_joined_at      ON users(joined_at);
CREATE INDEX IF NOT EXISTS idx_users_is_banned      ON users(is_banned) WHERE is_banned = true;

-- Favorites
CREATE INDEX IF NOT EXISTS idx_fav_user   ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_fav_group  ON favorites(group_id);

-- Reports
CREATE INDEX IF NOT EXISTS idx_reports_group        ON reports(group_id);
CREATE INDEX IF NOT EXISTS idx_reports_unresolved   ON reports(is_resolved) WHERE is_resolved = false;

-- Counties → universities
CREATE INDEX IF NOT EXISTS idx_uni_county ON universities(county_id);

-- Activity log (keep last 90 days)
CREATE INDEX IF NOT EXISTS idx_activity_user   ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_time   ON activity_logs(created_at DESC);
