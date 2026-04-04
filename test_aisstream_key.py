import asyncio
import json
import websockets
import os
from dotenv import load_dotenv

load_dotenv()

async def test_aisstream():
    api_key = os.getenv("AISSTREAM_API_KEY")
    if not api_key:
        print("Error: AISSTREAM_API_KEY not found in .env")
        return

    url = "wss://stream.aisstream.io/v0/stream"
    
    # Singapore Strait bounding box
    bounding_boxes = [[[1.1, 103.5], [1.4, 104.1]]]
    
    print(f"Connecting to AISStream with key: {api_key[:5]}...")
    
    try:
        async with websockets.connect(url) as websocket:
            subscribe_msg = {
                "APIKey": api_key,
                "BoundingBoxes": bounding_boxes,
            }
            await websocket.send(json.dumps(subscribe_msg))
            
            print("Subscription sent. Waiting for message...")
            
            # Wait for first message
            async for message in websocket:
                data = json.loads(message)
                print(f"Received message type: {data.get('MessageType')}")
                # Just one message is enough for verification
                break
            
            print("AISStream key verified successfully!")
            
    except Exception as e:
        print(f"AISStream verification failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_aisstream())
