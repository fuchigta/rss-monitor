-- migrate:up

-- Sample feeds
INSERT INTO feeds (name, url, check_interval_minutes) VALUES
    ('はてなブックマーク - テクノロジー', 'https://b.hatena.ne.jp/hotentry/it.rss', 30),
    ('Qiita', 'https://qiita.com/popular-items/feed', 60),
    ('Zenn Topics', 'https://zenn.dev/feed', 60)
ON CONFLICT (url) DO NOTHING;

-- Sample alert rules
INSERT INTO alert_rules (feed_id, metric_type, rule_name, condition, threshold, enabled) VALUES
    (1, 'update_frequency', 'Low update frequency alert', 'lt', 1.0, true),
    (1, 'avg_hatena_bookmarks', 'Low average bookmarks alert', 'lt', 10.0, true),
    (2, 'update_frequency', 'Qiita low update alert', 'lt', 0.5, true),
    (3, 'avg_hatena_bookmarks', 'Zenn low bookmark alert', 'lt', 5.0, true);

-- migrate:down

-- Delete sample alert rules
DELETE FROM alert_rules WHERE feed_id IN (1, 2, 3);

-- Delete sample feeds
DELETE FROM feeds WHERE url IN (
    'https://b.hatena.ne.jp/hotentry/it.rss',
    'https://qiita.com/popular-items/feed',
    'https://zenn.dev/feed'
);
