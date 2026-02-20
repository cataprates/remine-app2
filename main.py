from fastapi import FastAPI, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import google.generativeai as genai
from PIL import Image
import io
import os
from dotenv import load_dotenv
from typing import List

# Load local .env file
load_dotenv()

app = FastAPI()

# Enable CORS for all origins to prevent connection errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Securely fetch API Key
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

instrucoes_sistema = """
You are RE-MINE, an expert AI in urban mining. 
Analyze ALL uploaded photos together and provide a detailed breakdown.
FORMAT:
1. ### 📱 Object Detected: [Name]
2. 💰 **Estimated Total Value:** [Value]
3. **💎 Precious Metals Table:** (Material | Location | Est. Weight | Est. Value)
4. **♻️ Upcycle Ideas:** (Beginner, Intermediate, Advanced)
5. **🛠️ Tear-Down Guide**
6. **🌍 Where to Sell:** (Ask for City/Country for local buyers)
"""

model = genai.GenerativeModel('models/gemini-2.5-flash', system_instruction=instrucoes_sistema)
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
            # Open and resize image slightly to prevent timeouts on mobile
            image_data = await file.read()
            img = Image.open(io.BytesIO(image_data))
            img.thumbnail((1024, 1024)) 
            gemini_input.append(img)
    
    if text:
        gemini_input.append(text)
    elif files:
        gemini_input.append("Analyze these items for urban mining.")
        
    try:
        res = chat_session.send_message(gemini_input)
        return {"response": res.text}
    except Exception as e:
        return {"response": f"Error: {str(e)}"}
