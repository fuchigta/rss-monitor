# ADR 002: プラグイン型メトリクス評価システム

## ステータス

Accepted

## 日付

2025-10-27

## コンテキスト

システムの主要要件の一つとして「評価項目（メトリクス）をアドオン的にあとから追加が簡単にしたい」という要求があった。

初期要件のメトリクス：
- RSSフィードの更新頻度
- エントリの平均はてなブックマーク数

将来的に追加される可能性のあるメトリクス：
- エントリのコメント数
- 特定キーワードの出現頻度
- エントリの文字数統計
- 外部リンクの数
- その他のソーシャルメディアシェア数

メトリクス追加時の理想的な要件：
- 既存コードへの影響を最小限に
- メトリクスロジックの独立性
- 統一されたインターフェース
- テストの容易さ

## 決定内容

**プラグイン型アーキテクチャ**を採用し、以下の設計原則に基づいてメトリクス評価システムを実装する：

### 1. 基底クラスパターン

`MetricEvaluator` 抽象基底クラス（ABC）を定義：

```python
class MetricEvaluator(ABC):
    @property
    @abstractmethod
    def metric_type(self) -> str:
        """メトリクスタイプの一意識別子"""
        pass

    @property
    @abstractmethod
    def metric_name(self) -> str:
        """人間が読めるメトリクス名"""
        pass

    @abstractmethod
    def evaluate(self, feed_id: int) -> Optional[Dict[str, Any]]:
        """メトリクス評価ロジック"""
        pass
```

### 2. レジストリパターン

`MetricsRegistry` クラスで全てのメトリクスを一元管理：

```python
class MetricsRegistry:
    _evaluators: List[Type[MetricEvaluator]] = [
        UpdateFrequencyEvaluator,
        HatenaBookmarksEvaluator,
        # 新しいメトリクスをここに追加するだけ
    ]
```

### 3. 共通機能の提供

基底クラスで以下の共通機能を実装：
- `save_metric()`: メトリクス値のデータベース保存
- `check_alerts()`: アラートルールの評価
- `_evaluate_condition()`: しきい値判定ロジック

### 4. ディレクトリ構造

```
app/metrics/
├── __init__.py
├── base.py                  # MetricEvaluator基底クラス
├── registry.py              # MetricsRegistry
├── update_frequency.py      # 更新頻度メトリクス
├── hatena_bookmarks.py      # はてなブックマークメトリクス
└── [future_metric].py       # 将来追加されるメトリクス
```

### 5. 新メトリクス追加フロー

1. 新しいファイルを作成（例: `entry_length.py`）
2. `MetricEvaluator` を継承
3. 必須メソッドを実装
4. `registry.py` のリストに追加

```python
# app/metrics/entry_length.py
class EntryLengthEvaluator(MetricEvaluator):
    @property
    def metric_type(self) -> str:
        return 'avg_entry_length'

    @property
    def metric_name(self) -> str:
        return 'Average Entry Length'

    def evaluate(self, feed_id: int) -> Optional[Dict[str, Any]]:
        # 実装
        return {'value': avg_length, 'metadata': {...}}
```

## 結果

### 良い影響

1. **拡張性**
   - 新しいメトリクスの追加が非常に簡単（2ファイルの変更のみ）
   - 既存メトリクスに影響を与えない
   - テンプレートとして基底クラスが機能

2. **保守性**
   - 各メトリクスのロジックが独立
   - 責任範囲が明確
   - テストが容易（個別にテスト可能）

3. **一貫性**
   - 全てのメトリクスが同じインターフェース
   - データ保存・アラート判定ロジックの重複を排除
   - 統一されたエラーハンドリング

4. **可読性**
   - メトリクス一覧がレジストリで一目瞭然
   - 各メトリクスの実装が独立したファイルで管理

### 懸念事項とトレードオフ

1. **初期実装コスト**
   - シンプルな実装と比べて初期設計に時間がかかる
   - しかし長期的なメンテナンスコストは大幅に削減

2. **学習コスト**
   - ABCパターンの理解が必要
   - ただし一度理解すれば再利用可能

3. **オーバーエンジニアリングのリスク**
   - メトリクスが2-3個程度ならシンプルな実装でも十分
   - ただし要件に「拡張性」が明示されているため正当化できる

## 代替案

### 案1: 関数ベースのアプローチ

```python
def evaluate_update_frequency(feed_id):
    # 実装
    pass

def evaluate_hatena_bookmarks(feed_id):
    # 実装
    pass

METRICS = [
    evaluate_update_frequency,
    evaluate_hatena_bookmarks,
]
```

**却下理由**:
- 共通機能（save_metric, check_alerts）の重複
- メトリクスのメタデータ（名前、タイプ）の管理が困難
- インターフェースの統一が弱い

### 案2: 設定ファイルベース（YAML/JSON）

```yaml
metrics:
  - type: update_frequency
    query: "SELECT COUNT(*) FROM entries WHERE ..."
    threshold: 1.0
```

**却下理由**:
- 複雑なロジック（データ加工、条件分岐）の実装が困難
- SQLインジェクションのリスク
- デバッグが難しい
- Pythonコードの柔軟性を活かせない

### 案3: デコレータベース

```python
@register_metric('update_frequency')
def update_frequency_metric(feed_id):
    # 実装
    pass
```

**却下理由**:
- メトリクス固有のメタデータや状態管理が困難
- クラスベースに比べてコードの構造化が弱い
- 共通機能の共有が難しい

### 案4: プラグインシステム（動的ロード）

プラグインディレクトリから動的にモジュールをロード

**却下理由**:
- 現時点では過剰な複雑さ
- デプロイメントが複雑になる
- セキュリティリスク
- 静的型チェックが効かない

## 実装例

初期実装として以下の2つのメトリクスを実装：

1. **UpdateFrequencyEvaluator** (`app/metrics/update_frequency.py`)
   - 過去24時間のエントリ数を計測
   - 1時間あたりのエントリ数を計算

2. **HatenaBookmarksEvaluator** (`app/metrics/hatena_bookmarks.py`)
   - 過去7日間のエントリの平均ブックマーク数を計算
   - はてなブックマークAPIから取得したデータを使用

## 参考資料

- [Python ABC (Abstract Base Classes)](https://docs.python.org/3/library/abc.html)
- [Design Patterns: Registry Pattern](https://refactoring.guru/design-patterns/registry)
- [Python Plugin System](https://packaging.python.org/guides/creating-and-discovering-plugins/)
