-- RSS Monitor Database Schema

-- Feeds table: RSS/Atom feed definitions
CREATE TABLE IF NOT EXISTS feeds (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL UNIQUE,
    feed_type VARCHAR(50) DEFAULT 'rss',
    active BOOLEAN DEFAULT TRUE,
    check_interval_minutes INTEGER DEFAULT 60,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Entries table: Individual feed entries
CREATE TABLE IF NOT EXISTS entries (
    id SERIAL PRIMARY KEY,
    feed_id INTEGER NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
    entry_id TEXT NOT NULL, -- Original entry ID from feed
    title TEXT,
    link TEXT,
    published_at TIMESTAMP,
    author VARCHAR(255),
    summary TEXT,
    content TEXT,
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(feed_id, entry_id)
);

-- Metrics table: Time-series metrics data
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    feed_id INTEGER NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
    metric_type VARCHAR(100) NOT NULL, -- e.g., 'update_frequency', 'avg_hatena_bookmarks'
    metric_value NUMERIC,
    metadata JSONB, -- Additional metadata for the metric
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alert rules table: Configuration for alerts
CREATE TABLE IF NOT EXISTS alert_rules (
    id SERIAL PRIMARY KEY,
    feed_id INTEGER REFERENCES feeds(id) ON DELETE CASCADE,
    metric_type VARCHAR(100) NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    condition VARCHAR(50) NOT NULL, -- 'lt', 'gt', 'eq', 'lte', 'gte'
    threshold NUMERIC NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alerts table: Alert history
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    alert_rule_id INTEGER NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,
    feed_id INTEGER NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
    metric_type VARCHAR(100) NOT NULL,
    metric_value NUMERIC,
    threshold NUMERIC,
    message TEXT,
    severity VARCHAR(50) DEFAULT 'warning', -- 'info', 'warning', 'critical'
    resolved BOOLEAN DEFAULT FALSE,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Hatena bookmarks cache table
CREATE TABLE IF NOT EXISTS hatena_bookmarks (
    id SERIAL PRIMARY KEY,
    entry_id INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    bookmark_count INTEGER DEFAULT 0,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entry_id, checked_at)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_entries_feed_id ON entries(feed_id);
CREATE INDEX IF NOT EXISTS idx_entries_published_at ON entries(published_at);
CREATE INDEX IF NOT EXISTS idx_metrics_feed_id ON metrics(feed_id);
CREATE INDEX IF NOT EXISTS idx_metrics_type_measured ON metrics(metric_type, measured_at);
CREATE INDEX IF NOT EXISTS idx_alerts_feed_id ON alerts(feed_id);
CREATE INDEX IF NOT EXISTS idx_alerts_triggered_at ON alerts(triggered_at);
CREATE INDEX IF NOT EXISTS idx_hatena_entry_id ON hatena_bookmarks(entry_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_feeds_updated_at BEFORE UPDATE ON feeds
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alert_rules_updated_at BEFORE UPDATE ON alert_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
