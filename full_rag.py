from fastapi import FastAPI, UploadFile, File, Form
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
    return JSONResponse(content={"answer": answer}, ensure_ascii=False)
