from fastapi import FastAPI , HTTPException , Depends, UploadFile, File
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import bcrypt
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.errors import UniqueViolation
import os
from dotenv import load_dotenv
import requests
import numpy as np
from pypdf import PdfReader
import io
load_dotenv()
http_bearer = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

app = FastAPI()
app.mount("/static",StaticFiles(directory="static"),name = "static")

def create_tables():
    conn, cursor = get_db()
    try:
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        """)

       
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            filename TEXT NOT NULL,
            sentences TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        print("テーブルの作成（または確認）が完了しました")
    except Exception as e:
        print(f"テーブル作成でエラーが発生しました: {e}")


    finally:
        conn.close()


@app.on_event("startup")
def startup_event():
    create_tables()

def get_db():
    
    conn = psycopg2.connect(
        host="db",
        port=5432,
        dbname="my_log_db",
        user="my_user",
        password="my_password"
    )
   
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    return conn, cursor
class User(BaseModel):
    username: str
    password: str



@app.get("/")
def read_root():
    return {"message": "User Management API"}




@app.post("/users")
def create_user(user: User):
    conn, cursor = get_db()
    try:
        hash_pass = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())

        hashed_str = hash_pass.decode('utf-8')
        
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
            (user.username, hashed_str)
        )

        new_user = cursor.fetchone()
        conn.commit()

        return {"id": new_user["id"], "username": user.username}

    except UniqueViolation:
        raise HTTPException(status_code=400, detail="そのユーザー名は既に使われています")
    
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="サーバーエラーが発生しました")
    
    finally:
        conn.close()

def get_current_user_id(auth: HTTPAuthorizationCredentials = Depends(http_bearer)):
    try:
        token = auth.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")

        if user_id is None:
            raise HTTPException(status_code=401, detail="IDがトークンにありません")

        return user_id

    except JWTError:
        raise HTTPException(status_code=401, detail="無効なトークンです")

@app.get("/users/me")
def get_my_info(current_user_id: int = Depends(get_current_user_id)):
    conn, cursor = get_db()
    cursor.execute("SELECT id, username FROM users WHERE id = %s", (current_user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
   
    
    return user
    
@app.get("/users/{user_id}")
def get_user(user_id: int):


    conn, cursor = get_db()
    cursor.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    return user


@app.put("/users/{user_id}")
def update_user(user_id: int, user: User, current_user_id: int = Depends(get_current_user_id)):
    if current_user_id != user_id:
      raise HTTPException(status_code=403,detail="他人の情報は確認できません")

    conn, cursor = get_db()

    hashed_password = bcrypt.hashpw(user.password.encode("utf-8"),bcrypt.gensalt())
    cursor.execute(
        "UPDATE users SET username = %s, password = %s WHERE id = %s",
        (user.username, hashed_password, user_id)
    )

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    conn.commit()
    conn.close()

    return {"message": "User updated"}

@app.delete("/users/{user_id}")
def delete_user(user_id: int,current_user_id:int = Depends(get_current_user_id)):
    if current_user_id != user_id:
      raise HTTPException(status_code=403,detail="本人のIDしか使えません")

    
    conn, cursor = get_db()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    conn.commit()
    conn.close()
    return {"message": "User deleted"}

@app.post("/login")

def login_user(user: User):
    conn, cursor = get_db()

    cursor.execute(
        "SELECT id, username, password FROM users WHERE username = %s",
        (user.username,)
    )
    result = cursor.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    stored_password = result['password']
    if isinstance(stored_password, str):
        stored_password = stored_password.encode('utf-8')

    is_valid = bcrypt.checkpw(
    user.password.encode('utf-8'),
    stored_password
)

    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid password")

    token = jwt.encode({"id": result["id"], "username": result["username"]}, SECRET_KEY, algorithm=ALGORITHM)

    return {"message": "Login successful", "username": user.username, "token": token}




from groq import Groq

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

chat_messages = [
    {"role": "system", "content": "あなたは親切なAIアシスタントです。"}
]

@app.post("/chat")
def chat(message: str):
    chat_messages.append({"role": "user", "content": message})
    
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=chat_messages
    )
    
    reply = response.choices[0].message.content
    chat_messages.append({"role": "assistant", "content": reply})
    
    return {"reply": reply}


JINA_API_KEY = os.environ.get("JINA_API_KEY")

with open("data.txt", "r") as f:
    content = f.read()

sentences = [s.strip() for s in content.split("。") if s.strip()]

def embed(texts: list[str]):
    response = requests.post(
        "https://api.jina.ai/v1/embeddings",
        headers={"Authorization": f"Bearer {JINA_API_KEY}"},
        json={"input": texts, "model": "jina-embeddings-v3"}
    )
    return [d["embedding"] for d in response.json()["data"]]

sentence_vectors = embed(sentences)

class RagRequest(BaseModel):
    message: str

@app.post("/rag")
def rag(request: RagRequest, current_user_id: int = Depends(get_current_user_id)):

    conn,cursor = get_db()
    cursor.execute(
        "SELECT sentences FROM documents WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
        (current_user_id,)
        )
    result = cursor.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=400, detail="ドキュメントがアップロードされていません")
    
    sentences = [s.strip() for s in result["sentences"].split("。") if s.strip()]
    vectors = embed(sentences)

    question_vector = embed([request.message])[0]
    
    scores = []
    for vec in vectors:
        score = np.dot(question_vector, vec)
        scores.append(score)
    
    best_index = int(np.argmax(scores))
    best_sentence = sentences[best_index]
    best_score = scores[best_index]

    if best_score < 0.5:
        return {"reply": "その質問に答える情報がありません", "source": None}
    
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": f"以下の情報だけを使って答えてください。それ以外の知識は使わないでください：{best_sentence}"},
            {"role": "user", "content": request.message}
        ]
    )
    
    return {
        "reply": response.choices[0].message.content,
        "source": best_sentence
    }



@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    current_user_id: int = Depends(get_current_user_id)
    ):
   
    
    content = await file.read()
    
    if file.filename.endswith(".pdf"):
        pdf_file = io.BytesIO(content)
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    else:
        text = content.decode("utf-8")
    
    sentences = [s.strip() for s in text.split("。") if s.strip()]
    vectors = embed(sentences)

    conn,cousor = get_db()
    sentence_str = "。".join(sentences)
    cousor.execute(
        "INSERT INTO documents (user_id, filename, sentences) VALUES (%s,%s,%s)",
        (current_user_id,file.filename,sentence_str)
    )
    conn.commit()
    conn.close()
    
    return {"filename": file.filename, "sentences": len(sentences)}