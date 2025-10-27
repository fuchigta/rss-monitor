# ADR 003: Docker Composeによる統合デプロイメント

## ステータス

Accepted

## 日付

2025-10-27

## コンテキスト

システムの要件として「docker compose等で気軽にセットアップできる構成」が明示されていた。

複数のコンポーネント（PostgreSQL、Grafana、Python App、Ofelia）を統合的に管理する必要があり、以下の課題があった：

- 各コンポーネントの依存関係管理
- ネットワーク設定
- 環境変数の一元管理
- データ永続化
- ローカル開発環境と本番環境の一貫性
- 初回セットアップの簡素化

開発者やユーザーの体験として：
- `git clone` → `docker-compose up` で動作することが理想
- 複雑なインストール手順を避けたい
- 環境差異を最小化したい

## 決定内容

**Docker Compose**をオーケストレーションツールとして採用し、全てのコンポーネントをコンテナ化して統合管理する。

### 構成方針

1. **サービス定義**
   - `postgres`: データベース（PostgreSQL 16 Alpine）
   - `dbmate`: マイグレーション管理
   - `grafana`: 可視化ダッシュボード
   - `app`: RSSフィード収集・メトリクス評価
   - `scheduler`: Ofeliaジョブスケジューラ

2. **依存関係管理**
   - ヘルスチェックによる起動順序制御
   - `depends_on` with `condition` を使用
   - データベース起動完了後にマイグレーション実行
   - マイグレーション完了後にアプリケーション起動

```yaml
app:
  depends_on:
    postgres:
      condition: service_healthy
    dbmate:
      condition: service_completed_successfully
```

3. **ネットワーク**
   - 専用ブリッジネットワーク: `rss-monitor-network`
   - 全サービスが同一ネットワークに所属
   - サービス名でのDNS解決

4. **データ永続化**
   - Named volumes使用
   - `postgres_data`: データベースデータ
   - `grafana_data`: Grafanaダッシュボード設定

5. **設定ファイルのマウント**
   - `./db:/db`: マイグレーションファイル
   - `./app:/app`: アプリケーションコード（開発時の変更反映）
   - `./grafana/provisioning:/etc/grafana/provisioning`: Grafana設定
   - `./ofelia/config.ini:/etc/ofelia/config.ini`: スケジューラ設定

6. **環境変数**
   - データベース接続情報
   - Grafana認証情報
   - docker-compose.ymlで定義（`.env`ファイルでオーバーライド可能）

### ディレクトリ構造

```
rss-monitor/
├── docker-compose.yml      # オーケストレーション定義
├── .env.example            # 環境変数テンプレート
├── app/
│   ├── Dockerfile          # Pythonアプリイメージ
│   └── ...
├── db/
│   └── migrations/         # マイグレーションファイル
├── grafana/
│   ├── provisioning/       # 自動プロビジョニング設定
│   └── dashboards/         # ダッシュボード定義
└── ofelia/
    └── config.ini          # ジョブスケジュール定義
```

## 結果

### 良い影響

1. **簡単なセットアップ**
   ```bash
   git clone <repo>
   cd rss-monitor
   docker-compose up -d
   ```
   - 3コマンドで全環境が起動
   - 依存パッケージのインストール不要
   - OSに依存しない

2. **環境の一貫性**
   - 開発環境、ステージング、本番で同じコンテナイメージ使用
   - "Works on my machine"問題の解消
   - バージョン管理されたインフラ設定

3. **開発効率**
   - ローカル開発時のホットリロード（volumeマウント）
   - 個別サービスの再起動が容易
   - ログの集約管理（`docker-compose logs`）

4. **保守性**
   - 設定の可視化（docker-compose.yml）
   - 依存関係の明示的な定義
   - バージョン管理可能

5. **スケーラビリティへの道**
   - Kubernetes等への移行が容易
   - サービス分割の明確化

### 懸念事項とトレードオフ

1. **リソース消費**
   - 各コンテナのオーバーヘッド
   - 小規模利用でもある程度のメモリが必要
   - **緩和策**: Alpine Linuxベースイメージの使用

2. **Docker/Docker Composeへの依存**
   - これらがインストールされていない環境では動作不可
   - バージョン互換性の管理が必要
   - **緩和策**: 必要なバージョンをREADMEで明記

3. **ネットワーク設定の複雑さ**
   - 外部からのアクセス設定
   - ファイアウォール設定
   - **緩和策**: シンプルなport mapping使用

4. **デバッグの難しさ**
   - コンテナ内部へのアクセスが必要な場合がある
   - ログの追跡
   - **緩和策**: `docker-compose exec`、`logs`コマンドの活用

## 代替案

### 案1: 手動インストール（ネイティブ実行）

各コンポーネントをホストOSに直接インストール

**却下理由**:
- OSごとにインストール手順が異なる
- 依存関係の競合リスク
- セットアップの複雑さ
- 環境差異が発生しやすい
- 要件の「気軽にセットアップ」に反する

### 案2: Kubernetes (k8s)

フルオーケストレーション環境

**却下理由**:
- セットアップが複雑（minikube等でも学習コストが高い）
- 小規模システムには過剰
- ローカル開発環境には不向き
- 要件の「気軽に」に反する
- 将来的な選択肢として残す

### 案3: Vagrant

仮想マシンベースの環境管理

**却下理由**:
- リソース消費が大きい
- 起動が遅い
- Dockerに比べてポータビリティが低い
- モダンな開発フローではDockerが主流

### 案4: shell scriptによる起動スクリプト

個別にdocker runコマンドを実行

**却下理由**:
- 依存関係管理が手動
- ネットワーク設定が煩雑
- 設定の可視化が困難
- Docker Composeの方が標準的

### 案5: Ansible / Terraform

インフラ自動化ツール

**却下理由**:
- ローカル開発環境には過剰
- 学習コストが高い
- Docker Composeで十分
- クラウドデプロイ時の選択肢として検討可能

## 実装の詳細

### ヘルスチェック

PostgreSQLのヘルスチェックを定義して、依存サービスの起動タイミングを制御：

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U rss_user -d rss_monitor"]
  interval: 10s
  timeout: 5s
  retries: 5
```

### ボリューム戦略

- **Named volumes**: 永続化が必要なデータ（DB、Grafana設定）
- **Bind mounts**: 開発時に変更を即座に反映したいファイル（アプリコード、設定）

### ポート公開

- `5432`: PostgreSQL（開発時のDB接続用）
- `3000`: Grafana（ダッシュボードアクセス）

内部サービス（app、scheduler）はポート公開なし（セキュリティ）

## 参考資料

- [Docker Compose公式ドキュメント](https://docs.docker.com/compose/)
- [Compose file version 3 reference](https://docs.docker.com/compose/compose-file/compose-file-v3/)
- [Best practices for writing Dockerfiles](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
