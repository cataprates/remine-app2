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

# Configure API Key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

instrucoes_sistema = """
You are RE-MINE, an urban mining expert. 
Analyze hardware and provide:
1. ### 📱 Object: [Name]
2. 💰 **Estimated Value:** $[Amount] (Example: $0.50)
3. **💎 Materials Table:** (Material | Location | Weight | Value)
4. **🛠️ Tear-Down Checklist**
"""

# FIXED MODEL PATH
model = genai.GenerativeModel(
    model_name='models/gemini-1.5-flash', 
    system_instruction=instrucoes_sistema
)
chat_session = model.start_chat(history=[])

@app.get("/")
async def serve_frontend():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/chat")
async def chat_endpoint(text: str = Form(""), files: List[UploadFile] = File(None)):
    gemini_input = []
    if files:
        for file in files:
            image_data = await file.read()
            img = Image.open(io.BytesIO(image_data))
            img.thumbnail((800, 800))
            gemini_input.append(img)
    
    if text:
        gemini_input.append(text)
    elif not gemini_input:
        gemini_input.append("Analyze these items.")

    try:
        res = chat_session.send_message(gemini_input)
        return {"response": res.text}
    except Exception as e:
        return {"response": f"Server Error: {str(e)}"}
