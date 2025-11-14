from fastapi import FastAPI, Request
import telnyx
import os

app = FastAPI()

# Set your Telnyx API key from environment variable
telnyx.api_key = os.getenv("TELNYX_API_KEY")

@app.post("/webhook")
async def telnyx_webhook(request: Request):
    body = await request.json()
    data = body.get('data', {})
    
    if data.get('record_type') == 'event':
        event_type = data.get('event_type')
        call_control_id = data.get('payload', {}).get('call_control_id')
        
        if event_type == "call.initiated":
            telnyx.Call.answer(call_control_id)
            print(f"Answered call: {call_control_id}")
        
        elif event_type == "call.answered":
            print(f"Call answered: {call_control_id}")
            # TODO: Start Deepgram streaming
        
        elif event_type == "call.hangup":
            print(f"Call ended: {call_control_id}")
    
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    PORT = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=PORT)
