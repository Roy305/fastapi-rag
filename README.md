# このアプリについて
- ユーザー管理ができるRAGアプリです。
ユーザーごとにPDFを登録し自分のドキュメントに対してのみ質問できてその質問に近いものをドキュメントから検索してくれるアプリです。
## 苦労した点
未経験のため、最初はコードの意味を理解せずに
動かすことだけを優先していました。
コードの意図が理解できないと自分で改修や説明ができないと思い、一つ一つのコードについて理由を調べながら実装しました。
例えばJWTのdecodeの仕組み、%sがSQLインジェクション対策であること、グローバル変数の問題点とDB管理への移行理由など
を理解することを意識しました。

# 技術スタック
- fastapi バックエンドワークフレーム
- uvicorn アプリサーバー
- Docker 環境コンテナ化
- groq レスポンス用AI
- jina ベクトル変換AI
- numpy 類似度計算
- pypdf PDF読み取り
- bcrypt パスワードハッシュ化

# 機能一覧
## エンドポイント
- GET / トップページ 
- POST /users ユーザー作成　
- GET /users/me 自身の情報
- GET /users/{user_id} {user_id}の情報
- PUT /users/{user_id} {user_id}の情報変更
- DELETE /users/{user_id} {user_id}の情報削除
- POST /login トークンを使ったログイン
- POST /chat チャット機能
- POST /rag rag検索機能
- POST /uploadファイルアップロード機能

# セットアップ
## リポジトリをダウンロード
- git clone <url>

## .envファイル作成しAPIキー設定
- GROQ_API_KEY=your-key
- JINA_API_KEY=your-key
- SECRET_KEY=your-key

## 起動コマンド
- docker-compose up --build