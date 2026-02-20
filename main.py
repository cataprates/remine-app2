from fastapi import FastAPI, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import google.generativeai as genai
from PIL import Image
import io
import os  # <--- THIS IS THE MISSING LINE!
from dotenv import load_dotenv

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🚨 REPLACE WITH YOUR NEW API KEY 🚨
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

instrucoes_sistema = """
You are RE-MINE, an expert AI in urban mining, electronics recycling, and upcycling. 

BEHAVIOR RULES:
1. If the user uploads a photo, provide the FULL BREAKDOWN using the exact format below.
2. If the user asks a follow-up question (e.g., "Where can I sell the copper in London?"), answer ONLY their question naturally and conversationally. DO NOT repeat the full breakdown.

FULL BREAKDOWN FORMAT:
### 📱 Object Detected: [Detailed Name & Model]

💰 **Estimated Total Value:** $[Amount] USD (Provide a realistic range)

**💎 Precious Metals & Materials Inside:**
*(Note: Weights and values are educated estimates based on industry averages)*

| Material | Exact Location | Est. Weight | Est. Value |
| :--- | :--- | :--- | :--- |
| **[Material]** | [Location] | ~[Weight] | $[Value] |

**♻️ Upcycle & Repurpose:**
* 🟢 **Beginner:** [Simple, no-tools-required idea]
* 🟡 **Intermediate:** [Requires some basic tools or crafting]
* 🔴 **Advanced:** [Complex engineering, wiring, or coding idea]

**🛠️ Tear-Down Guide:**
Provide detailed, step-by-step instructions.

**🌍 Where to Sell:**
* **As a Whole Device:** [Specific platforms to sell it intact]
* **As Separated Components:** [Where to sell the extracted copper, RAM, circuit boards, etc.]
* **📍 Local Buyers:** "To give you exact scrap yards or buyers for these specific components, **please reply with your City and Country!**"
"""

model = genai.GenerativeModel('models/gemini-2.5-flash', system_instruction=instrucoes_sistema)
chat_session = model.start_chat(history=[])

@app.get("/")
async def serve_frontend():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/chat")
async def chat_endpoint(text: str = Form(""), file: UploadFile = File(None)):
    gemini_input = []
    
    if file:
        image_data = await file.read()
        img = Image.open(io.BytesIO(image_data))
        gemini_input.append(img)
    
    if text:
        gemini_input.append(text)
    elif file:
        gemini_input.append("I have uploaded a photo. Please give me the complete RE-MINE breakdown.")
        
    if not gemini_input:
        return {"response": "Please send text or an image."}

    try:
        res = chat_session.send_message(gemini_input)
        return {"response": res.text}
    except Exception as e:

        return {"response": f"Error: {str(e)}"}

