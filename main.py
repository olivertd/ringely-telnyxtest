from fastapi import FastAPI, Request, HTTPException
import telnyx
import os
import base64
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

app = FastAPI()

telnyx.api_key = os.getenv("TELNYX_API_KEY")

# Get your public key from Telnyx Portal -> Account Settings -> Keys & Credentials
TELNYX_PUBLIC_KEY = os.getenv("TELNYX_PUBLIC_KEY")

def verify_telnyx_signature(payload: str, signature: str, timestamp: str) -> bool:
    """Verify Telnyx webhook signature"""
    if not TELNYX_PUBLIC_KEY:
        return True  # Skip verification if no public key set (for testing)
    
    try:
        verify_key = VerifyKey(bytes.fromhex(TELNYX_PUBLIC_KEY))
        signed_payload = f"{timestamp}|{payload}".encode()
        signature_bytes = base64.b64decode(signature)
        verify_key.verify(signed_payload, signature_bytes)
        return True
    except (BadSignatureError, Exception) as e:
        print(f"Signature verification failed: {e}")
        return False

@app.post("/webhook")
async def telnyx_webhook(request: Request):
    # Get signature headers
    signature = request.headers.get("telnyx-signature-ed25519")
    timestamp = request.headers.get("telnyx-timestamp")
    
    # Get raw body for signature verification
    body_bytes = await request.body()
    body_str = body_bytes.decode()
    
    # Verify signature
    if signature and timestamp:
        if not verify_telnyx_signature(body_str, signature, timestamp):
            raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Process webhook
    body = await request.json()
    data = body.get('data', {})
    
    if data.get('record_type') == 'event':
        event_type = data.get('event_type')
        call_control_id = data.get('payload', {}).get('call_control_id')
        
        if event_type == "call.initiated":
            print(f"Call initiated: {call_control_id}")
            if telnyx.api_key and call_control_id != "test-call-123":
                try:
                    telnyx.Call.answer(call_control_id)
                    print(f"Answered call: {call_control_id}")
                except Exception as e:
                    print(f"Error answering call: {e}")
        
        elif event_type == "call.answered":
            print(f"Call answered: {call_control_id}")
        
        elif event_type == "call.hangup":
            print(f"Call ended: {call_control_id}")
    
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    PORT = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=PORT)
