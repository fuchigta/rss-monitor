# RSS Monitor

RSSフィードの更新頻度やエントリのはてなブックマーク数を定点観測し、一定のしきい値を下回った際にアラートを発生させるモニタリングシステムです。

## 特徴

- **プラグイン型メトリクス評価システム**: 新しいメトリクスを簡単に追加可能
- **自動データ収集**: Ofeliaによる定期的なRSSフィード収集とはてなブックマーク数の取得
- **リアルタイム監視**: Grafanaダッシュボードでメトリクスを可視化
- **柔軟なアラート設定**: しきい値ベースのアラート機能
- **簡単セットアップ**: Docker Composeで全環境を一括構築

## システム構成

```
┌─────────────┐
│   Ofelia    │ ← ジョブスケジューラ（定期実行）
│  Scheduler  │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│  RSS Feed   │────▶│  PostgreSQL  │
│  Collector  │     │   Database   │
└─────────────┘     └──────┬───────┘
                           │
┌─────────────┐            │
│   Hatena    │────────────┤
│ Bookmark API│            │
└─────────────┘            │
                           ▼
                    ┌──────────────┐
                    │   Grafana    │
                    │  Dashboard   │
                    └──────────────┘
```

### コンポーネント

1. **PostgreSQL**: メトリクスデータ、フィード情報、アラート履歴を保存
2. **Python App**: RSSフィード収集、はてなブックマーク取得、メトリクス評価
3. **Ofelia**: ジョブスケジューラ（定期的にデータ収集とメトリクス評価を実行）
4. **Grafana**: ダッシュボードでメトリクスを可視化、アラート表示

## クイックスタート

### 前提条件

- Docker
- Docker Compose

### セットアップ

1. リポジトリをクローン

```bash
git clone <repository-url>
cd rss-monitor
```

2. Docker Composeで起動

```bash
docker-compose up -d
```

3. サービスが起動したことを確認

```bash
docker-compose ps
```

4. Grafanaにアクセス

ブラウザで `http://localhost:3000` を開く

- ユーザー名: `admin`
- パスワード: `admin`

5. 初回データ収集を手動実行（オプション）

```bash
docker-compose exec app python main.py run-all
```

これにより、サンプルフィードのデータ収集が即座に開始されます。

## 使い方

### フィードの追加

データベースに直接フィードを追加します：

```bash
docker-compose exec postgres psql -U rss_user -d rss_monitor
```

```sql
INSERT INTO feeds (name, url, check_interval_minutes)
VALUES ('フィード名', 'https://example.com/feed.rss', 60);
```

### アラートルールの追加

```sql
INSERT INTO alert_rules (feed_id, metric_type, rule_name, condition, threshold, enabled)
VALUES (
    1,                          -- フィードID
    'update_frequency',         -- メトリクスタイプ
    'Low update alert',         -- ルール名
    'lt',                       -- 条件（lt: より小さい）
    1.0,                        -- しきい値
    true                        -- 有効/無効
);
```

#### 条件オプション

- `lt`: Less than（より小さい）
- `lte`: Less than or equal（以下）
- `gt`: Greater than（より大きい）
- `gte`: Greater than or equal（以上）
- `eq`: Equal（等しい）

### 利用可能なメトリクス

1. **update_frequency**: フィードの更新頻度（エントリ数/時間）
2. **avg_hatena_bookmarks**: エントリの平均はてなブックマーク数

## カスタムメトリクスの追加

新しいメトリクスを追加する手順：

1. `app/metrics/` ディレクトリに新しいメトリクスファイルを作成

```python
# app/metrics/my_custom_metric.py
from typing import Any, Dict, Optional
from .base import MetricEvaluator

class MyCustomMetricEvaluator(MetricEvaluator):
    @property
    def metric_type(self) -> str:
        return 'my_custom_metric'

    @property
    def metric_name(self) -> str:
        return 'My Custom Metric'

    def evaluate(self, feed_id: int) -> Optional[Dict[str, Any]]:
        # メトリクスの計算ロジックを実装
        cursor = self.db.cursor()
        # ... データベースクエリ ...
        cursor.close()

        return {
            'value': calculated_value,
            'metadata': {'info': 'additional info'}
        }
```

2. `app/metrics/registry.py` にメトリクスを登録

```python
from .my_custom_metric import MyCustomMetricEvaluator

class MetricsRegistry:
    _evaluators: List[Type[MetricEvaluator]] = [
        UpdateFrequencyEvaluator,
        HatenaBookmarksEvaluator,
        MyCustomMetricEvaluator,  # 追加
    ]
```

3. コンテナを再起動

```bash
docker-compose restart app
```

## 手動実行

各タスクを手動で実行することも可能です：

```bash
# RSSフィード収集
docker-compose exec app python main.py collect

# はてなブックマーク数更新
docker-compose exec app python main.py update-bookmarks

# メトリクス評価
docker-compose exec app python main.py evaluate-metrics

# すべてのタスクを実行
docker-compose exec app python main.py run-all
```

## ジョブスケジュール

Ofeliaによる自動実行スケジュール（`ofelia/config.ini`）：

- **フィード収集**: 30分ごと
- **ブックマーク数更新**: 1時間ごと
- **メトリクス評価**: 15分ごと
- **フルサイクル**: 6時間ごと

スケジュールは `ofelia/config.ini` で変更可能です。

## データベーススキーマ

### 主要テーブル

- **feeds**: フィード定義
- **entries**: フィードエントリ
- **metrics**: 時系列メトリクスデータ
- **alert_rules**: アラートルール定義
- **alerts**: アラート履歴
- **hatena_bookmarks**: はてなブックマーク数キャッシュ

詳細は `db/init/01_schema.sql` を参照してください。

## トラブルシューティング

### コンテナが起動しない

```bash
# ログを確認
docker-compose logs

# 特定のサービスのログを確認
docker-compose logs app
docker-compose logs postgres
```

### データベース接続エラー

```bash
# データベースが起動しているか確認
docker-compose ps postgres

# データベースに接続できるか確認
docker-compose exec postgres pg_isready -U rss_user -d rss_monitor
```

### フィードが収集されない

```bash
# 手動でフィード収集を実行してエラーを確認
docker-compose exec app python main.py collect
```

## 開発

### ローカル開発環境

```bash
# 開発モードで起動（コード変更が即座に反映）
docker-compose up

# Pythonパッケージの追加
# app/pyproject.toml を編集後
docker-compose build app
docker-compose up -d app
```

### パッケージ管理

このプロジェクトは高速なPythonパッケージマネージャ [uv](https://github.com/astral-sh/uv) を使用しています。

```bash
# パッケージを追加する場合
# 1. app/pyproject.toml の dependencies に追加
# 2. コンテナを再ビルド
docker-compose build app
docker-compose up -d app
```

### テスト

```bash
# データベースに接続
docker-compose exec postgres psql -U rss_user -d rss_monitor

# サンプルデータを確認
SELECT * FROM feeds;
SELECT * FROM entries LIMIT 10;
SELECT * FROM metrics ORDER BY measured_at DESC LIMIT 10;
SELECT * FROM alerts WHERE resolved = FALSE;
```

## ライセンス

MIT License

## 貢献

プルリクエストを歓迎します！

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成
