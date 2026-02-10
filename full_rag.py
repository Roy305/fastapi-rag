import json
from fastapi import FastAPI, UploadFile, File, Form,Response
from fastapi.responses import HTMLResponse , JSONResponse
import os
from dotenv import load_dotenv
load_dotenv() # .envファイルから設定を読み込む

app = FastAPI()
UPLOADED_FILE = None

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <h1>RAGシステム</h1>
    <form action="/upload" enctype="multipart/form-data" method="post">
        <input type="file" name="file"><input type="submit" value="アップロード">
    </form>
    <hr>
    <form action="/chat" method="post">
        <input type="text" name="question" placeholder="質問">
        <input type="submit" value="RAG検索">
    </form>
    """

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    global UPLOADED_FILE
    content = await file.read()
    with open("uploaded_file.txt", "wb") as f:
        f.write(content)
    UPLOADED_FILE = content.decode()
    return {"message": f"{file.filename} RAG用に読み込み完了！"}


@app.post("/chat")
async def chat(question: str = Form(...)):
    
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    # アップロードファイルからRAG（本物！）
    if UPLOADED_FILE:
        context = UPLOADED_FILE[:4000]  # トークン制限内
    else:
        context = "FastAPIドキュメント..."
    
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": f"文書内容:\n{context}\n\nこの文書に基づいて回答"},
            {"role": "user", "content": question}
        ]
    )
    answer = response.choices[0].message.content

    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
        <head>
            <meta charset="utf-8">
            <title>RAG回答結果</title>
            <style>
                body {{ font-family: sans-serif; padding: 20px; line-height: 1.6; background-color: #f4f4f9; }}
                .container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
                p {{ white-space: pre-wrap; word-wrap: break-word; }}
                .back-link {{ display: inline-block; margin-top: 20px; text-decoration: none; color: #007bff; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>AIからの回答</h1>
                <p>{answer}</p>
                <a href="/" class="back-link">← 戻ってまた質問する</a>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)