from fastapi import FastAPI, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import google.generativeai as genai
from PIL import Image
import io
import os
from dotenv import load_dotenv
from typing import List

# 1. Load Environment Variables
load_dotenv()

app = FastAPI()

# 2. CORS - This allows your phone to talk to Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

instrucoes_sistema = """
You are RE-MINE, a professional urban mining AI. 
Analyze all photos and provide a structured breakdown.
If the user provides GPS coordinates, suggest local disposal sites.
Format your value as: 💰 **Estimated Value:** $[Amount]
"""

model = genai.GenerativeModel('models/gemini-1.5-flash', system_instruction=instrucoes_sistema)
chat_session = model.start_chat(history=[])

@app.get("/")
async def serve_frontend():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# Simple health check to see if server is alive
@app.get("/health")
async def health():
    return {"status": "online"}

@app.post("/chat")
async def chat_endpoint(
    text: str = Form(""), 
    files: List[UploadFile] = File(None), 
    lat: str = Form(None), 
    lon: str = Form(None)
):
    gemini_input = []
    
    # Process Images
    if files:
        for file in files:
            image_data = await file.read()
            img = Image.open(io.BytesIO(image_data))
            img.thumbnail((800, 800)) # Smaller size = Faster upload
            gemini_input.append(img)
    
    # Process Text & Location
    location_info = f" (Location: {lat}, {lon})" if lat and lon else ""
    full_prompt = f"{text}{location_info}"
    
    if full_prompt:
        gemini_input.append(full_prompt)
    elif not gemini_input:
        gemini_input.append("Analyze these items for recycling.")

    try:
        res = chat_session.send_message(gemini_input)
        return {"response": res.text}
    except Exception as e:
        return {"response": f"Error: {str(e)}"}
