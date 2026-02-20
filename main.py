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

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Upgraded Instructions: AI now handles Location and precise Value formatting
instrucoes_sistema = """
You are RE-MINE, a global expert in urban mining and e-waste.
If the user provides coordinates (Latitude/Longitude), identify their city/region and suggest the nearest specialized e-waste recycling centers.
Analyze all photos and provide:
1. ### 📱 Object: [Name]
2. 💰 **Estimated Value:** [Value in USD] (Always provide a single number here like 0.50 for the tracker to read)
3. **💎 Materials Table:** (Material | Location | Est. Weight | Est. Value)
4. **🛠️ Tear-Down Checklist**
5. **🌍 Local Disposal:** Suggest local buyers based on provided location.
"""

model = genai.GenerativeModel('models/gemini-1.5-flash', system_instruction=instrucoes_sistema)
chat_session = model.start_chat(history=[])

@app.get("/")
async def serve_frontend():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/chat")
async def chat_endpoint(text: str = Form(""), files: List[UploadFile] = File(None), lat: str = Form(None), lon: str = Form(None)):
    gemini_input = []
    
    # Add Location context if available
    location_context = f" User Location: Lat {lat}, Lon {lon}." if lat and lon else ""
    
    if files:
        for file in files:
            image_data = await file.read()
            img = Image.open(io.BytesIO(image_data))
            img.thumbnail((1024, 1024)) 
            gemini_input.append(img)
    
    full_prompt = f"{text}{location_context}"
    if full_prompt:
        gemini_input.append(full_prompt)
    elif files:
        gemini_input.append("Analyze these items.")
        
    try:
        res = chat_session.send_message(gemini_input)
        return {"response": res.text}
    except Exception as e:
        return {"response": f"Error: {str(e)}"}
