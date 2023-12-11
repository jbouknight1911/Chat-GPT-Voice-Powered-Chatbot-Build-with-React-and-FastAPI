# uvicorn main:app --reload
# uvicorn main:app

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from decouple import config
import openai

# Custom function imports
from functions.openai_requests import convert_audio_to_text, get_chat_response
from functions.database import store_messages
from functions.database import reset_messages
from functions.text_to_speech import convert_text_to_speech

# Get Environment Vars
openai.organization=config("OPEN_AI_ORG")
openai.api_key = config("OPEN_AI_KEY")

app = FastAPI()

origins =[
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:4173",
    "http://localhost:4174",
    "http://localhost:3000"
]


# CORS - Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET","POST","PUT","DELETE"],
    allow_headers=["Authorization","Content-Type"],  
)


# check health
@app.get("/health")
async def check_health():
    return {"response": "healthy"}

# reset messages
@app.get("/reset")
async def reset_chat():
    reset_messages()
    return {"response": "conversation reset"}


# Post audio
@app.post("/post-audio/")
async def post_audio(file: UploadFile=File(...)):
    
    # Save file from frontend
    with open(file.filename, "wb") as buffer:
        buffer.write(file.file.read())
    audio_input = open(file.filename, "rb")

    # Decode Audio
    message_decoded = convert_audio_to_text(audio_input)

    # Gaurd: Ensure message decoded
    if not message_decoded:
        return HTTPException(status_code=400, detail='Failed to decode audio')

    # Get ChatGPT response
    chat_response = get_chat_response(message_decoded)

    # Gaurd: Ensure chat responded
    if not chat_response:
        return HTTPException(status_code=400, detail='Failed to get chat response')

    # Store messages
    store_messages(message_decoded, chat_response)

    # Convert chat response to audio
    audio_output = convert_text_to_speech(chat_response)
    
    # Gaurd: Ensure chat responded
    if not audio_output:
        return HTTPException(status_code=400, detail='Failed to audio response')

    # Create a generator that yields chunks of data
    def iterfile():
        yield audio_output

    # Return audio file
    return StreamingResponse(iterfile(), media_type="application/octet-stream")

