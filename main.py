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

# UPGRADED INSTRUCTIONS: High accuracy, reuse hypotheses, and local selling advice.
instrucoes_sistema = """
You are RE-MINE, a highly accurate urban mining and e-waste expert.
When analyzing hardware, you must provide:

1. ### 📱 Object Identification: Be highly accurate about the model and components.
2. **💎 Materials Table:** (Material | Location | Est. Weight | Est. Value).
3. 💰 **Estimated Total Value:** $X.XX.
4. ♻️ **Creative Reuse Ideas:** Provide hypotheses for reuse in various situations. Include both SIMPLE uses and PROFESSIONAL uses (e.g., using an old tablet as a restaurant menu).
5. 🌍 **Where to Sell:** Tell the user exactly where to sell separated components (e.g., copper vs PCBs). IMPORTANT: If the user hasn't told you their city or region, ASK them where they live so you can provide specific local businesses.
"""

# Fixed Model String to bypass the 404 error
model = genai.GenerativeModel(
    model_name='gemini-2.0-flash', 
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
        gemini_input.append("Analyze this hardware with high accuracy.")

    try:
        res = chat_session.send_message(gemini_input)
        return {"response": res.text}
    except Exception as e:
        return {"response": f"Server Error: {str(e)}"}
