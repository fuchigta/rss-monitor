# ADR 005: dbmateによるデータベースマイグレーション管理

## ステータス

Accepted

## 日付

2025-10-27

## コンテキスト

プロジェクトの初期実装では、Docker Composeの`docker-entrypoint-initdb.d`機能を使用して、PostgreSQLコンテナ起動時にSQLファイルを実行していた：

```
db/init/
├── 01_schema.sql
└── 02_sample_data.sql
```

この方式には以下の問題があった：

1. **マイグレーション管理の欠如**
   - スキーマ変更の履歴が追跡できない
   - ロールバックができない
   - どのマイグレーションが適用済みか不明

2. **本番環境での課題**
   - 既存のデータベースにスキーマ変更を適用する手段がない
   - 初回セットアップのみを想定した設計

3. **チーム開発の困難**
   - 複数人でのスキーマ変更の衝突リスク
   - 変更の適用順序が不明確

4. **テスト環境の再現性**
   - 特定バージョンのスキーマに戻せない
   - テストデータのセットアップが煩雑

ユーザーからの要求：
> データベーススキーマをマイグレーションに対応できるようにしたい

## 決定内容

[**dbmate**](https://github.com/amacneil/dbmate)をデータベースマイグレーションツールとして採用する。

### dbmateの特徴

1. **シンプル**
   - 単一バイナリで動作
   - 設定ファイルが最小限
   - SQLファイルベース（既存の知識を活用）

2. **言語非依存**
   - Pythonコードへの依存がない
   - どの言語のプロジェクトでも使用可能

3. **Docker対応**
   - 公式Dockerイメージが提供されている
   - Docker Composeへの統合が容易

4. **ロールバック対応**
   - `migrate:up`と`migrate:down`による双方向マイグレーション
   - 安全なスキーマ変更

### 実装方針

1. **マイグレーションファイル形式**

```sql
-- migrate:up
CREATE TABLE feeds (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS feeds;
```

2. **ディレクトリ構造**

```
db/
├── README.md                                    # マイグレーションガイド
├── migrations/
│   ├── 20250101000000_initial_schema.sql
│   └── 20250101000001_sample_data.sql
└── schema.sql                                   # 自動生成（gitignore）
```

3. **Docker Compose統合**

```yaml
dbmate:
  image: amacneil/dbmate:latest
  environment:
    DATABASE_URL: "postgres://user:pass@postgres:5432/db?sslmode=disable"
  volumes:
    - ./db:/db
  depends_on:
    postgres:
      condition: service_healthy
  command: up
  restart: on-failure
```

4. **ヘルパースクリプト**

`scripts/migrate.sh`で一般的な操作を簡素化：
- `up`: マイグレーション適用
- `down`: ロールバック
- `status`: 状態確認
- `new <name>`: 新規マイグレーション作成
- `redo`: 最後のマイグレーションをやり直し

### 移行戦略

1. `db/init/` の既存SQLファイルをマイグレーション形式に変換
2. `docker-entrypoint-initdb.d`の使用を停止
3. dbmateサービスを追加し、起動時に自動実行
4. アプリケーションはdbmate完了後に起動

## 結果

### 良い影響

1. **バージョン管理**
   - スキーマ変更がGitで追跡可能
   - 誰がいつ何を変更したか明確
   - コードレビューが可能

2. **ロールバック対応**
   - 問題発生時に安全に戻せる
   - 本番環境でのリスク低減
   - A/Bテストやカナリアリリースが容易

3. **再現性**
   - どの環境でも同じスキーマを構築可能
   - CIでのテストが確実
   - ステージング環境の一貫性

4. **チーム開発の円滑化**
   - マイグレーションの衝突を早期発見
   - レビュープロセスの確立
   - ドキュメント化された変更履歴

5. **既存資産の活用**
   - SQLファイルベースで既存の知識を活用
   - ORMへの依存がない
   - 複雑なクエリも記述可能

### 懸念事項とトレードオフ

1. **学習コスト**
   - dbmateの使い方の習得
   - マイグレーションのベストプラクティス
   - **緩和策**: ヘルパースクリプトと詳細ドキュメント提供

2. **初期セットアップの複雑化**
   - マイグレーションファイルの作成が必要
   - upとdownの両方を書く手間
   - **緩和策**: テンプレート提供、自動生成機能

3. **ツールへの依存**
   - dbmateの保守状況に依存
   - **緩和策**: アクティブなOSSプロジェクト、代替ツールへの移行も可能

## 代替案

### 案1: Alembic（SQLAlchemy）

Pythonエコシステムの標準的マイグレーションツール

**検討理由**:
- Python統合が深い
- 自動マイグレーション生成
- 成熟したツール

**却下理由**:
- SQLAlchemyへの依存が必要（ORM使わなくてもCore必要）
- 設定が複雑
- 本プロジェクトはORMを使用していない
- SQLファイルベースの方がシンプル

### 案2: golang-migrate

軽量なマイグレーションツール

**検討理由**:
- 非常にシンプル
- SQLファイルベース
- 単一バイナリ

**比較**:
dbmateとほぼ同等だが、以下の理由でdbmateを選択：
- dbmateの方が設定ファイルがシンプル
- `DATABASE_URL`環境変数だけで動作
- より直感的なコマンド体系
- Docker公式イメージの使いやすさ

### 案3: Flyway

エンタープライズグレードのマイグレーションツール

**却下理由**:
- JVMへの依存（リソース消費が大きい）
- 本プロジェクトには過剰
- 学習コストが高い
- 小規模プロジェクトには不向き

### 案4: 自前のマイグレーションシステム

PostgreSQLのスキーマバージョン管理テーブルを使った実装

**却下理由**:
- 自分でメンテナンスが必要
- 既存OSSの方が信頼性が高い
- ロールバック、履歴管理を自分で実装
- 開発リソースの無駄

### 案5: Liquibase

XMLベースのマイグレーションツール

**却下理由**:
- XML記法が冗長
- SQLの方が直感的
- JVMへの依存
- 学習コストが高い

## マイグレーション戦略

### 命名規則

```
YYYYMMDDHHMMSS_description.sql
```

例: `20250127123456_add_feed_category.sql`

タイムスタンプにより順序保証、衝突回避

### ベストプラクティス

1. **常にupとdownを定義**
   - ロールバック可能性の保証
   - downが書けないスキーマ変更は危険

2. **小さく分割**
   - 1つのマイグレーションで1つの論理的変更
   - レビューとテストが容易

3. **データ移行を含める**
   - スキーマ変更とデータ変換を同じマイグレーションに
   - 一貫性の保証

4. **本番適用前のテスト**
   - ローカルでup/downを確認
   - ステージング環境で検証
   - ロールバック手順も確認

### 初期マイグレーション

1. `20250101000000_initial_schema.sql`
   - テーブル定義
   - インデックス
   - トリガー・関数

2. `20250101000001_sample_data.sql`
   - サンプルフィード
   - サンプルアラートルール

## 運用フロー

### 開発環境

```bash
# 新しいマイグレーション作成
./scripts/migrate.sh new add_feed_priority

# マイグレーション編集
# db/migrations/YYYYMMDDHHMMSS_add_feed_priority.sql

# 適用
./scripts/migrate.sh up

# ロールバック（必要に応じて）
./scripts/migrate.sh down
```

### CI/CD

```yaml
# CI時にマイグレーション適用
- docker-compose up -d postgres
- docker-compose run --rm dbmate up
- # テスト実行
```

### 本番環境

```bash
# バックアップ
pg_dump ...

# マイグレーション適用
docker-compose run --rm dbmate up

# 検証
# （問題があればロールバック）
docker-compose run --rm dbmate down
```

## 実装の詳細

### 設定ファイル (.dbmate)

```
url: "postgres://rss_user:rss_password@localhost:5432/rss_monitor?sslmode=disable"
migrations: "./db/migrations"
schema: "./db/schema.sql"
wait: true
wait_timeout: 60s
```

### Docker Composeでの自動実行

```yaml
dbmate:
  command: up
  restart: on-failure
```

起動時に自動的にマイグレーションを適用。失敗時はリトライ。

## 移行履歴

1. 初期実装: `db/init/` + docker-entrypoint-initdb.d
2. 要求: マイグレーション対応
3. ツール選定: 5つの候補からdbmate選択
4. 実装: マイグレーション変換、Docker Compose統合
5. コミット: `010e4e0` "Add dbmate for database schema migration management"

## 参考資料

- [dbmate公式ドキュメント](https://github.com/amacneil/dbmate)
- [Database Migration Best Practices](https://www.brunton-spall.co.uk/post/2014/05/06/database-migrations-done-right/)
- [Evolutionary Database Design](https://martinfowler.com/articles/evodb.html)
- [プロジェクトdb/README.md](../../db/README.md)
