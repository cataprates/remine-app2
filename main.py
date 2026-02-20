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

# PORTUGUESE INSTRUCTIONS: Exact phrasing from your notes!
instrucoes_sistema = """
Você é o RE-MINE, um especialista em mineração urbana.
A sua análise deve ter **mais accuracy** (máxima precisão).
Para cada foto de hardware, forneça:

1. ### 📱 Objeto: Identificação exata do modelo.
2. **💎 Tabela de Materiais:** (Material | Localização | Peso Est. | Valor Est.)
3. 💰 **Valor Total Estimado:** $X.XX.
4. ♻️ **Reutilização:** Colocar hipótese de reutilização em diversas situações mais simples ou professional (tipo usar um tablet velho como um menu de restaurante, ou para gerir uma casa).
5. 🌍 **Onde Vender/Entregar:** Adicionar específicos onde se possa entregar/vender os componentes separados. (Tipo onde entregar cobre ou então onde vender uma placa dependendo onde o user mora). 
IMPORTANTE: Se o usuário não disser onde mora na mensagem, pergunte a localização dele para dar as opções locais exatas!
"""

# To this:
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash', 
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
        gemini_input.append("Analise este hardware.")

    try:
        res = chat_session.send_message(gemini_input)
        return {"response": res.text}
    except Exception as e:
        return {"response": f"Server Error: {str(e)}"}

