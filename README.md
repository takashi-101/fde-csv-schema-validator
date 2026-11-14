# FDE CSV Schema Validator（CSVの行のID欠損・ID重複・日付形式の検査）

CSVから読み込んだ行（列名をキーにした辞書のリスト）について、ID列の欠損と重複、日付列の形式を検査し、件数と行番号付きのエラーの一覧を返すPythonの関数です。標準ライブラリだけで動きます。

## 30秒で読む要点
- **検査するのは指定した2列だけ**：ID列の欠損・重複と、日付列が `YYYY-MM-DD`、`YYYY/MM/DD`、`YYYY年M月D日` のどれかで読めるかを調べます。名前に Schema とありますが、列の型や必須列の一覧といったスキーマ（表の列の定義）全体の検査はしません。
- **結果は件数とエラー文**：`validate_csv_rows` は、総行数、問題のない行数、重複したID、行番号付きのエラー文を返します。正規化（表記を `YYYY-MM-DD` にそろえること）した日付は返しません。正規化した文字列が必要な場合は `normalize_japanese_date` を使います。
- **読めない日付はエラーにするだけ**：和暦（`令和8年11月9日` など）や、区切り文字のある1桁の月日（`2026/11/9` など）はエラーになります。月日の範囲（2月30日など）は検査しません。

## 実行
```
python examples/run_example.py
```
`examples/sample_applications.csv`（架空の申請データ8行）を `csv.DictReader` で読み、`申請ID` をID列、`申請日` を日付列として検査します。出力：
```
input: examples/sample_applications.csv (id_col=申請ID, date_col=申請日)
total_rows: 8
valid_rows: 3
duplicate_ids: ['R-0002']
errors:
  row 4: duplicate 申請ID=R-0002
  row 5: missing 申請ID
  row 6: Unrecognized date format: 令和8年11月9日
  row 7: Unrecognized date format: 2026/11/9
  row 8: Unrecognized date format: 
```

テスト：
```
python -m unittest discover -s tests -v
```

## 検査の内容
各行を上から順に、次の順で検査します。1行につきエラーは最大1件で、最初に見つかった問題だけを記録します。

| 順 | 検査 | エラー文（`errors` の要素） |
|---|---|---|
| 1 | ID列の値が空（列が無い、`None`、空白だけ） | `row N: missing <ID列名>` |
| 2 | IDがそれより前の行と同じ（前後の空白を除いて比較） | `row N: duplicate <ID列名>=<ID>` |
| 3 | 日付列の値が読めない（空欄を含む） | `row N: Unrecognized date format: <値>` |

- `N` は見出し行を除いたデータ行の番号（1始まり）です。
- 重複した行は、そのIDを `duplicate_ids` にも加えます。同じIDが3回出ると2回加えます。
- 日付が読めない行のIDも記録するため、同じIDが後の行に出ると重複になります。
- `valid_rows` は3つの検査をすべて通った行の数です。

## 日付の形式
前後の空白を除いてから判定します。

| 入力 | `normalize_japanese_date` の結果 |
|---|---|
| `2026-11-01` | `2026-11-01` |
| `2026/11/02` | `2026-11-02` |
| `2026年1月5日` | `2026-01-05` |
| `2026-02-30` | `2026-02-30`（月日の範囲は検査しません） |
| `令和8年11月3日`、`2026/1/2`、`20261101`、`2026-11-01T09:00`、空欄 | `ValueError`（`Unrecognized date format: <値>`） |

## 公開している関数
| 名前 | 内容 |
|---|---|
| `csv_validator.validate_csv_rows(rows, id_col, date_col)` | 行のリストを検査し、`ValidationSummary` を返します。 |
| `csv_validator.ValidationSummary` | 結果のデータクラス（値をまとめて持つクラス。`frozen` 指定で変更できません）。`total_rows`、`valid_rows`、`duplicate_ids`、`errors` を持ちます。 |
| `csv_validator.validator.normalize_japanese_date(raw)` | 日付の文字列を `YYYY-MM-DD` にして返します。読めない場合は `ValueError` です。 |

CSVファイルの読み込みはしません。`csv.DictReader` などで読んだ行を渡します（例：`examples/run_example.py`）。パッケージは `src/` にあり、インストール用の設定（`pyproject.toml`）はありません。テストと `examples/run_example.py` は、先頭で `src` をimportパスに加えています。

## テスト（24件）
- 正常系：3つの形式の日付の正規化、すべての行が問題なしの場合、引数で指定した列名とエラー文の形式
- 境界値：空の入力、前後に空白のあるIDの重複、3回出るID、日付が読めない行のIDによる重複、1行1件のエラー、範囲外の月日と全角数字がそのまま通ること、結果が変更できないこと
- 異常系：和暦・1桁の月日・その他の形式の拒否、IDの欠損（空文字・空白・`None`・列なし）、日付の欠損、列名の指定違い
- READMEの「実行」に載せた出力が、`examples/run_example.py` の実際の出力と一致すること

## 制約
- 和暦、区切り文字のある1桁の月日、時刻付き、区切りなしの日付は読めません。
- 月日の範囲は検査しません。`2026-02-30` も問題なしになります。
- 正規表現（文字列のパターン）の `\d` は全角数字にも一致するため、`２０２６-11-01` のような全角数字のISO形式（`YYYY-MM-DD`）は問題なしとなり、全角のまま返ります。
- 値は文字列か `None` を前提にしています（`csv.DictReader` の出力）。

## ファイル構成
```
src/csv_validator/
  validator.py               検査と日付の正規化
  __init__.py                validate_csv_rows と ValidationSummary を公開
examples/
  sample_applications.csv    見本データ（架空）
  run_example.py             見本データを検査して結果を表示
tests/                       ユニットテスト
```

## 根拠（学習）

| 求められる力 | 機能 | 裏付けになる学習（発行元・名称・発行日） | 照会先（Credly） |
|---|---|---|---|
| データ活用（Python・SQL・BI） | ID列の欠損・重複の検出 | Coursera（認定：IBM）「Data Analysis with Python」2026年11月9日 | https://www.credly.com/badges/a1425bcf-2c74-43eb-a7f9-2edd448788db |
| データ活用（Python・SQL・BI） | 日付の表記の確認と統一 | Coursera（認定：IBM）「Python for Data Science and AI」2026年11月9日 | https://www.credly.com/badges/517da8b6-38f8-49c5-8126-d33b8cf1f33a |

「求められる力」の分け方は、[プロフィール](https://github.com/takashi-101) の「FDE・AXで求められる力と、その根拠」と同じです。

## ライセンス
MIT（[LICENSE](LICENSE)）
