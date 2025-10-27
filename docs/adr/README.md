# Architecture Decision Records (ADR)

このディレクトリには、RSS Monitorプロジェクトのアーキテクチャに関する重要な決定事項を記録しています。

## ADRとは

Architecture Decision Record (ADR) は、プロジェクトで行われた重要なアーキテクチャ上の決定を文書化したものです。各ADRには以下が含まれます：

- **背景（Context）**: なぜこの決定が必要だったか
- **決定内容（Decision）**: 何を決定したか
- **結果（Consequences）**: この決定がもたらす影響（良い面・悪い面）
- **代替案（Alternatives）**: 検討した他の選択肢

## ADR一覧

| ADR | タイトル | ステータス | 日付 |
|-----|---------|-----------|------|
| [001](001-system-architecture-components.md) | システムアーキテクチャとコンポーネント選定 | Accepted | 2025-10-27 |
| [002](002-plugin-based-metrics-system.md) | プラグイン型メトリクス評価システム | Accepted | 2025-10-27 |
| [003](003-docker-compose-deployment.md) | Docker Composeによる統合デプロイメント | Accepted | 2025-10-27 |
| [004](004-uv-package-manager.md) | uvパッケージマネージャの採用 | Accepted | 2025-10-27 |
| [005](005-dbmate-migration-tool.md) | dbmateによるデータベースマイグレーション管理 | Accepted | 2025-10-27 |

## ADRの命名規則

```
NNN-kebab-case-title.md
```

- `NNN`: 3桁の連番（001, 002, ...）
- タイトルはケバブケース（小文字、ハイフン区切り）

## ADRのステータス

- **Proposed**: 提案中
- **Accepted**: 承認済み
- **Deprecated**: 非推奨
- **Superseded**: 別のADRに置き換えられた

## 参考リンク

- [ADRの書き方（GitHub）](https://github.com/joelparkerhenderson/architecture-decision-record)
- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
