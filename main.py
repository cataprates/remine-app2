from fastapi import FastAPI, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import google.generativeai as genai
from PIL import Image
import io
import os
from dotenv import load_dotenv
from typing import List

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

instrucoes_sistema = """
You are RE-MINE, an expert AI in urban mining. 
If photos are uploaded, analyze ALL of them together and provide the table breakdown for all objects detected.
(Keep the rest of your formatting rules: Table, Beginner/Intermediate/Advanced Upcycling, and Where to Sell).
"""

model = genai.GenerativeModel('models/gemini-2.5-flash', system_instruction=instrucoes_sistema)
chat_session = model.start_chat(history=[])

@app.get("/")
async def serve_frontend():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/chat")
async def chat_endpoint(text: str = Form(""), files: List[UploadFile] = File(None)): # Changed to List
    gemini_input = []
    
    if files:
        for file in files:
            image_data = await file.read()
            img = Image.open(io.BytesIO(image_data))
            gemini_input.append(img)
    
    if text:
        gemini_input.append(text)
    elif files:
        gemini_input.append("Analyze these photos and give me the RE-MINE breakdown.")
        
    try:
        res = chat_session.send_message(gemini_input)
        return {"response": res.text}
    except Exception as e:
        return {"response": f"Error: {str(e)}"}
