# 1. ベースとなるPythonのバージョンを指定
FROM python:3.11-slim

# 2. コンテナ内の作業ディレクトリを決める
WORKDIR /app

# 3. 必要なパッケージ（ライブラリ）のリストをコピー
COPY requirements.txt .

# 4. ライブラリをインストール
RUN pip install --no-cache-dir -r requirements.txt

# 5. あなたの書いたコードをすべてコンテナの中にコピー
COPY . .

# 6. FastAPIを起動するコマンド
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]