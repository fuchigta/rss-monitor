# ADR 004: uvパッケージマネージャの採用

## ステータス

Accepted

## 日付

2025-10-27

## コンテキスト

Pythonプロジェクトでは、依存パッケージの管理が重要な課題である。

プロジェクトの初期実装では`requirements.txt`を使用していたが、以下の課題があった：

1. **依存関係の管理**
   - `requirements.txt`はフラットなリストで依存関係のツリーが不明確
   - プロジェクトメタデータとパッケージ情報が分離

2. **インストール速度**
   - `pip`は逐次的にパッケージをダウンロード・インストール
   - Docker build時の待ち時間が長い

3. **標準化**
   - PEP 518/621で`pyproject.toml`が標準化
   - モダンなPythonプロジェクトのベストプラクティス

4. **ビルドツール**
   - `requirements.txt`だけではプロジェクトメタデータが不足
   - 配布パッケージの作成が困難

## 決定内容

[**uv**](https://github.com/astral-sh/uv)を採用し、`pyproject.toml`ベースのパッケージ管理に移行する。

### uvの特徴

1. **高速**
   - Rust実装による並列ダウンロード・インストール
   - pipの10-100倍の速度

2. **標準準拠**
   - `pyproject.toml` (PEP 621) をネイティブサポート
   - pip互換のインターフェース

3. **シンプル**
   - `pip`の代替として設計
   - 既存のワークフローを大きく変更しない

### 実装方針

1. **`pyproject.toml`の使用**

```toml
[project]
name = "rss-monitor"
version = "0.1.0"
description = "RSS feed monitoring system"
requires-python = ">=3.11"
dependencies = [
    "feedparser==6.0.10",
    "psycopg2-binary==2.9.9",
    "requests==2.31.0",
    "python-dateutil==2.8.2",
    "pyyaml==6.0.1",
]
```

2. **Dockerfileでの統合**

```dockerfile
# uvを公式イメージからコピー
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# pyproject.tomlから依存関係をインストール
RUN uv pip install --system -e .
```

3. **`requirements.txt`の削除**
   - 重複管理を避ける
   - `pyproject.toml`が単一の真実の源（Single Source of Truth）

## 結果

### 良い影響

1. **ビルド時間の大幅短縮**
   - Docker build時のパッケージインストールが高速化
   - CI/CDパイプラインの高速化
   - 開発サイクルの改善

2. **標準化されたプロジェクト構造**
   - PEP 621準拠
   - モダンなPythonプロジェクトのベストプラクティスに従う
   - 他のツール（ruff, pytest等）との統合が容易

3. **プロジェクトメタデータの一元管理**
   - パッケージ名、バージョン、依存関係が一箇所に
   - 配布パッケージの作成が容易（将来的にPyPIへの公開等）

4. **依存関係の明確化**
   - 直接依存と推移的依存の区別が明確
   - バージョン管理が容易

### 懸念事項とトレードオフ

1. **新しいツール**
   - uvは比較的新しい（2024年リリース）
   - チーム内での学習コスト
   - **緩和策**: pip互換インターフェースで学習コスト最小

2. **エコシステムの成熟度**
   - pipほど広く使われていない
   - エッジケースでの問題の可能性
   - **緩和策**: Astral社（Ruffの開発元）による開発で信頼性は高い

3. **移行コスト**
   - `requirements.txt` → `pyproject.toml`への移行
   - ドキュメントの更新
   - **実績**: 本プロジェクトでは問題なく移行完了

## 代替案

### 案1: pip + requirements.txt（現状維持）

**却下理由**:
- インストール速度が遅い
- プロジェクトメタデータの管理が不十分
- モダンなPythonプロジェクトの標準から外れる

### 案2: Poetry

人気のPythonパッケージマネージャ

**却下理由**:
- uvより遅い
- 独自の依存関係解決ロジック（時に問題を起こす）
- 仮想環境管理が強制的（Dockerコンテナ内では不要）
- 学習コストがuvより高い

**Poetryの利点**:
- ロックファイル（poetry.lock）による厳密な依存関係管理
- 成熟したエコシステム

**判断**:
- 本プロジェクトではロックファイルよりも速度を優先
- Dockerで環境を固定しているため、ロックファイルの必要性は低い

### 案3: pip-tools

pipの拡張ツール（requirements.txt + requirements.in）

**却下理由**:
- `pyproject.toml`への移行メリットが得られない
- 2ファイル管理の複雑さ
- uvの速度優位性がない

### 案4: PDM

PEP 582準拠のパッケージマネージャ

**却下理由**:
- PEP 582は将来性が不透明
- uvより遅い
- エコシステムがPoetryより小さい

### 案5: Hatch

プロジェクト管理ツール

**却下理由**:
- パッケージマネージャ以上の機能（ビルド、テスト実行等）
- 本プロジェクトには過剰
- uvのシンプルさの方が適している

## ベンチマーク

参考値（uvの公式サイトより）:

| ツール | インストール時間 |
|--------|----------------|
| pip | 100% |
| Poetry | 80-90% |
| uv | 1-10% |

## 実装の詳細

### pyproject.tomlの構成

```toml
[project]
name = "rss-monitor"
version = "0.1.0"
description = "RSS feed monitoring system with Hatena Bookmark integration"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    # 必要なパッケージをバージョン指定
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Dockerfileでの使用

```dockerfile
# 公式イメージからuvバイナリをコピー（最小オーバーヘッド）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# プロジェクトファイルをコピー
COPY pyproject.toml .

# システムレベルにインストール（仮想環境不要）
RUN uv pip install --system -e .
```

## 移行履歴

1. 初期実装: `requirements.txt` + `pip`
2. 問題提起: requirements.txtはuvに不適切
3. 移行: `pyproject.toml` + `uv pip`
4. コミット: `fed5216` "Replace requirements.txt with pyproject.toml for uv package manager"

## 参考資料

- [uv公式ドキュメント](https://github.com/astral-sh/uv)
- [PEP 621 – Storing project metadata in pyproject.toml](https://peps.python.org/pep-0621/)
- [PEP 518 – Specifying Minimum Build System Requirements](https://peps.python.org/pep-0518/)
- [Astral社のブログ](https://astral.sh/blog)
