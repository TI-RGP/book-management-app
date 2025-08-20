# 図書管理システム

Python/FastAPI/SQLite/SQLAlchemy/Jinja2を使用したサーバーサイドレンダリング型の貸し出し図書管理Webアプリケーションです。

## 機能

- **本の管理**
  - 本の新規登録（タイトル、著者）
  - 本の一覧表示
  - キーワード検索（タイトル・著者）
  - 本の詳細表示

- **貸出管理**
  - 本の貸出（借り手名、返却期限を指定）
  - 本の返却
  - 貸出状況の表示（在庫あり/貸出中）

- **ダッシュボード**
  - 総登録数、在庫数、貸出中数のサマリ表示
  - 最近追加された本の表示

- **履歴管理**
  - 各本の貸出履歴を記録・表示

## 技術スタック

- **バックエンド**: FastAPI (Python)
- **データベース**: SQLite + SQLAlchemy ORM
- **フロントエンド**: Jinja2テンプレート + HTML/CSS
- **バリデーション**: Pydantic
- **Webサーバー**: Uvicorn

## プロジェクト構成

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPIエントリポイント
│   ├── database.py          # データベース接続設定
│   ├── models.py            # SQLAlchemyモデル
│   ├── schemas.py           # Pydanticスキーマ
│   └── routers/
│       ├── __init__.py
│       └── books.py         # 本管理のAPIルーター
├── templates/               # Jinja2テンプレート
│   ├── base.html
│   ├── index.html           # ダッシュボード
│   ├── books_list.html      # 本一覧
│   ├── book_detail.html     # 本詳細
│   ├── book_new.html        # 新規登録フォーム
│   └── checkout.html        # 貸出フォーム
├── static/
│   └── styles.css           # CSSスタイル
├── requirements.txt         # 依存関係
├── library.db              # SQLiteデータベース（自動生成）
└── README.md
```

## セットアップ手順

### 1. 依存関係のインストール

#### pip を使用する場合:
```bash
pip install -r requirements.txt
```

#### uv を使用する場合:
```bash
uv pip install -r requirements.txt
```

### 2. アプリケーションの起動

```bash
uvicorn app.main:app --reload
```

### 3. ブラウザでアクセス

アプリケーションが正常に起動したら、以下のURLにアクセスしてください：

```
http://localhost:8000
```

## 画面構成

- `/` - ダッシュボード（統計情報と最近の本）
- `/books` - 本一覧・検索
- `/books/new` - 新規本登録
- `/books/{id}` - 本詳細・貸出履歴
- `/books/{id}/checkout` - 貸出フォーム
- `/books/{id}/return` - 返却処理（POST）

## データベーススキーマ

### Books テーブル
- `id`: 主キー
- `title`: 本のタイトル
- `author`: 著者名
- `status`: ステータス（available/borrowed）
- `borrower`: 借り手名（貸出中のみ）
- `due_date`: 返却予定日（貸出中のみ）
- `created_at`: 作成日時
- `updated_at`: 更新日時

### Loans テーブル
- `id`: 主キー
- `book_id`: 本ID（外部キー）
- `borrower`: 借り手名
- `checkout_at`: 貸出日時
- `due_date`: 返却予定日
- `returned_at`: 返却日時（返却済みのみ）

## サンプルデータ

初回起動時に以下のサンプルデータが自動的に登録されます：

1. 「Pythonプログラミング入門」- 山田太郎（在庫あり）
2. 「FastAPI実践ガイド」- 佐藤花子（在庫あり）
3. 「データベース設計」- 田中次郎（貸出中）

## 特徴

- **シンプルなUI**: 最小限のCSSで実装された直感的なインターフェース
- **レスポンシブデザイン**: モバイルデバイスにも対応
- **バリデーション**: フォーム入力の検証とエラーメッセージ表示
- **履歴管理**: 各本の貸出返却履歴を完全に記録
- **検索機能**: タイトルや著者名での部分一致検索

## 開発・拡張

このアプリケーションは最小構成で実装されており、以下のような拡張が可能です：

- ユーザー認証機能の追加
- 本のカテゴリ分類
- 返却期限のリマインダー機能
- CSVエクスポート機能
- API エンドポイントの追加
- フロントエンド フレームワークとの分離

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。