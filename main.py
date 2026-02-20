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

# 1. FIXED CORS: This allows the phone to talk to the server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Key configuration
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

instrucoes_sistema = """
You are RE-MINE, an urban mining expert. 
1. Provide a clear object name.
2. Estimated Total Value: Return $[Amount] (e.g. $0.50).
3. Precious Metals Table: Material | Location | Weight | Value.
4. Tear-Down Checklist.
5. Local Disposal based on coordinates.
"""

model = genai.GenerativeModel('models/gemini-1.5-flash', system_instruction=instrucoes_sistema)
chat_session = model.start_chat(history=[])

@app.get("/")
async def serve_frontend():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/chat")
async def chat_endpoint(
    text: str = Form(""), 
    files: List[UploadFile] = File(None), 
    lat: str = Form(None), 
    lon: str = Form(None)
):
    gemini_input = []
    
    if files:
        for file in files:
            image_data = await file.read()
            img = Image.open(io.BytesIO(image_data))
            img.thumbnail((800, 800)) # Resizing for mobile data speeds
            gemini_input.append(img)
    
    location_data = f" (User Location: {lat}, {lon})" if lat and lon else ""
    user_prompt = f"{text}{location_data}"
    
    if user_prompt:
        gemini_input.append(user_prompt)
    elif not gemini_input:
        gemini_input.append("Analyze these hardware components.")

    try:
        res = chat_session.send_message(gemini_input)
        return {"response": res.text}
    except Exception as e:
        # This will show up in your phone screen if the API Key is wrong
        return {"response": f"Gemini Error: {str(e)}"}
