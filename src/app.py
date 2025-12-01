import logging
import os
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse
from src.ai_agent import AIAgent
from src.whatsapp import WhatsAppSender

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("src.app")

app = FastAPI()
agent = AIAgent()
whatsapp = WhatsAppSender()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

@app.get("/")
async def root():
    return {"message": "🔥 WhatsApp Chatbot Running"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    if params.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(content=params.get("hub.challenge"), status_code=200)
    return PlainTextResponse(content="Invalid verification token", status_code=403)

async def handle_message(text: str, from_number: str):
    """Process message in background"""
    try:
        logger.info(f"🔄 Processing message: {text}")
        response = await agent.generate_response(text)
        logger.info(f"📤 Sending response to {from_number}")
        await whatsapp.send_text(from_number, response["text"])
    except Exception as e:
        logger.exception(f"❌ Error processing message: {e}")

@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    logger.info(f"Webhook data: {data}")

    try:
        entry = data["entry"][0]["changes"][0]["value"]

        if "messages" in entry:
            message = entry["messages"][0]
            from_number = message["from"]
            mtype = message["type"]

            if mtype == "text":
                text = message["text"]["body"]
                logger.info(f"✅ Text received: {text}")
                # Process in background to prevent timeout
                background_tasks.add_task(handle_message, text, from_number)
            else:
                logger.info("✅ Ignored message type (only text supported)")
                return {"status": "ignored"}

    except Exception as e:
        logger.exception(f"❌ Error handling webhook: {e}")

    return {"status": "ok"}

