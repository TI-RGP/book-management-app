# データベース設定とデプロイ手順

## 問題の解決

Renderの無料プランではSQLiteファイルがデプロイ毎にリセットされる問題を解決するため、PostgreSQLデータベースを使用するように設定を変更しました。

## データベース設定

### 開発環境
- **データベース**: SQLite (`./library.db`)
- **設定**: 環境変数`DATABASE_URL`が設定されていない場合に自動的に使用

### 本番環境 (Render)
- **データベース**: PostgreSQL 
- **設定**: 環境変数`DATABASE_URL`から自動取得

## デプロイ手順

### 1. 初回デプロイ
render.yamlファイルにPostgreSQLデータベースが含まれているため、Renderが自動的に：
- PostgreSQLデータベースを作成
- 環境変数`DATABASE_URL`を設定
- アプリケーションをデプロイ

### 2. データの永続化
- PostgreSQLデータベースは永続化されるため、デプロイ後もデータは保持されます
- サンプルデータは初回のみ作成され、既存データがある場合はスキップされます

### 3. 既存データの移行（必要な場合）
既存のSQLiteデータをPostgreSQLに移行するには：

```bash
# ローカル環境で実行
export DATABASE_URL="your_postgresql_url"
python migrate_data.py
```

## 環境変数

### 必要な環境変数
- `DATABASE_URL`: PostgreSQL接続URL（Renderで自動設定）

### オプション環境変数
- `PYTHON_VERSION`: Python バージョン（デフォルト: 3.11.0）

## データベース構造

### テーブル
1. **genres**: ジャンル管理（階層構造対応）
2. **books**: 書籍情報
3. **loans**: 貸出履歴
4. **reservations**: 予約管理

### リレーション
- books ← genre_id → genres
- loans ← book_id → books  
- reservations ← book_id → books

## 確認方法

デプロイ後、以下を確認：

1. **アプリケーションアクセス**: https://your-app.onrender.com
2. **データ永続化**: 
   - 本を新規登録
   - アプリを再デプロイ
   - 登録した本が残っていることを確認

## トラブルシューティング

### データが消える場合
1. DATABASE_URL環境変数が正しく設定されているか確認
2. PostgreSQLデータベースが作成されているか確認
3. Renderのログでエラーを確認

### データベース接続エラー
1. PostgreSQL接続文字列の形式確認
2. データベースユーザーの権限確認
3. ネットワーク接続確認

## 開発環境でのテスト

PostgreSQL環境でのテストを行う場合：

```bash
# PostgreSQLを起動
export DATABASE_URL="postgresql://user:password@localhost/dbname"
python -m uvicorn app.main:app --reload
```