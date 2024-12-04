import os
import json
import base64
import asyncio
import websocket
from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PORT = int(os.getenv('PORT', 5050))
SYSTEM_MESSAGE = (
    "Você é a Ju, atendente do Distrito."
    "Você está fazendo um atendimento por voz via telefone e a sua função é ajudar o usuário restrito ao tema Distrito."
    "Ofereça respostas rápidas, claras e práticas, ideais para uma conversa por voz."
    "Você NUNCA fala sobre nada que não esteja relacionado ao Distrito."
    "Certifique-se em não falar de concorrentes ou denegrir a imagem do Distrito de maneira alguma."
    "O Distrito é uma plataforma de inovação aberta que conecta startups, empresas e investidores."
)
VOICE = 'alloy'
LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated',
    'response.done', 'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
    'session.created'
]
SHOW_TIMING_MATH = False

BASE_URL = os.getenv('BASE_URL', 'https://1306-177-126-10-185.ngrok-free.app')  # Update with your public domain

app = FastAPI()

if not OPENAI_API_KEY:
    raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_NUMBER')

if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_NUMBER]):
    raise ValueError('Missing Twilio configuration in the environment variables.')

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.get("/", response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}

@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    response = VoiceResponse()
    response.say("...")
    response.pause(length=1)
    response.say("...")
    connect = Connect()
    connect.stream(url=f'{BASE_URL.replace("https", "wss")}/media-stream')
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.api_route("/outbound-call", methods=["GET", "POST"])
async def handle_outbound_call(request: Request):
    """Handle outbound call and return TwiML response to connect to Media Stream."""
    response = VoiceResponse()
    response.say("Conectando sua chamada. Por favor, aguarde.")
    connect = Connect()
    connect.stream(url=f'{BASE_URL.replace("https", "wss")}/media-stream')
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.post("/make-call")
async def make_call(request: Request):
    data = await request.json()
    to_number = data.get('to')
    if not to_number:
        raise HTTPException(status_code=400, detail="Missing 'to' phone number")

    url = f'{BASE_URL}/outbound-call'

    try:
        call = twilio_client.calls.create(
            to=to_number,
            from_=TWILIO_NUMBER,
            url=url
        )
        return JSONResponse(content={"message": "Call initiated", "call_sid": call.sid})
    except Exception as e:
        print(f"Error initiating call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    # Existing implementation...
    # (Your existing code for the media stream)
    pass  # Replace with your existing media stream handler code

# Existing functions like initialize_session, send_initial_conversation_item, etc.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)