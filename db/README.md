# Database Migrations

このディレクトリはデータベーススキーマのマイグレーションファイルを含んでいます。

## ディレクトリ構造

```
db/
├── README.md           # このファイル
├── migrations/         # マイグレーションファイル
│   ├── 20250101000000_initial_schema.sql
│   └── 20250101000001_sample_data.sql
└── schema.sql         # dbmateが自動生成するスキーマダンプ（gitignore推奨）
```

## マイグレーションファイル形式

dbmateのマイグレーションファイルは以下の形式です：

```sql
-- migrate:up
-- ここに適用するSQL（テーブル作成、カラム追加など）
CREATE TABLE example (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255)
);

-- migrate:down
-- ここにロールバック用SQL（変更を戻す）
DROP TABLE IF EXISTS example;
```

## マイグレーション命名規則

- ファイル名: `YYYYMMDDHHMMSS_description.sql`
- 例: `20250101120000_add_feed_category.sql`
- タイムスタンプは `./scripts/migrate.sh new` コマンドで自動生成されます

## マイグレーション作成フロー

### 1. 新しいマイグレーションを作成

```bash
./scripts/migrate.sh new add_user_preferences
```

### 2. 生成されたファイルを編集

```bash
# db/migrations/20250127123456_add_user_preferences.sql
```

```sql
-- migrate:up
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    theme VARCHAR(50) DEFAULT 'light',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- migrate:down
DROP TABLE IF EXISTS user_preferences;
```

### 3. マイグレーションを適用

```bash
./scripts/migrate.sh up
```

### 4. 動作確認

```bash
# マイグレーション状態を確認
./scripts/migrate.sh status

# データベースに接続して確認
docker-compose exec postgres psql -U rss_user -d rss_monitor
```

## 既存マイグレーション

### 20250101000000_initial_schema.sql

初期スキーマの作成：
- feeds テーブル
- entries テーブル
- metrics テーブル
- alert_rules テーブル
- alerts テーブル
- hatena_bookmarks テーブル
- 各種インデックス
- updated_at自動更新用のトリガー

### 20250101000001_sample_data.sql

サンプルデータの挿入：
- はてなブックマーク、Qiita、Zennのフィード
- 各フィードのアラートルール

## ロールバック

### 最後のマイグレーションをロールバック

```bash
./scripts/migrate.sh down
```

### 特定のバージョンまでロールバック

```bash
# dbmateコンテナで直接実行
docker-compose run --rm dbmate rollback --to 20250101000000
```

## トラブルシューティング

### マイグレーションが失敗した場合

1. エラーメッセージを確認

```bash
docker-compose logs dbmate
```

2. マイグレーション状態を確認

```bash
./scripts/migrate.sh status
```

3. 必要に応じてロールバック

```bash
./scripts/migrate.sh down
```

4. マイグレーションファイルを修正して再適用

```bash
./scripts/migrate.sh up
```

### 手動でマイグレーション状態をリセット

⚠️ **注意**: これはデータを失う可能性があります

```bash
# schema_migrationsテーブルを確認
docker-compose exec postgres psql -U rss_user -d rss_monitor -c "SELECT * FROM schema_migrations;"

# 特定のマイグレーションレコードを削除（慎重に！）
docker-compose exec postgres psql -U rss_user -d rss_monitor -c "DELETE FROM schema_migrations WHERE version = '20250101000001';"
```

## ベストプラクティス

1. **小さく分割**: 1つのマイグレーションで1つの論理的な変更
2. **常にdownを定義**: ロールバック可能にする
3. **テスト**: 本番環境適用前に必ずローカルでテスト
4. **データ移行**: スキーマ変更とデータ移行は同じマイグレーションに含める
5. **順序**: 依存関係がある場合は適切な順序でマイグレーションを作成
6. **バックアップ**: 本番環境では必ず事前にバックアップを取る

## 参考リンク

- [dbmate公式ドキュメント](https://github.com/amacneil/dbmate)
- [プロジェクトREADME](../README.md#データベースマイグレーション)
