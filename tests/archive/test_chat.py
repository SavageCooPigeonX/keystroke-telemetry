"""Quick test: send a chat message to the WS server and print the reply."""
import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    print("websockets not installed — installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets


async def test_chat():
    uri = "ws://127.0.0.1:8769"
    try:
        async with websockets.connect(uri) as ws:
            print(f"Connected to {uri}")
            # Send chat
            await ws.send(json.dumps({
                "type": "chat",
                "message": "Say hello in exactly 5 words.",
            }))
            print("Sent chat message, waiting for response...")
            # Read responses until we get chat_response
            for _ in range(10):
                raw = await asyncio.wait_for(ws.recv(), timeout=30)
                data = json.loads(raw)
                if data.get("type") == "chat_response":
                    print(f"REPLY: {data.get('text', '')[:300]}")
                    return
                else:
                    print(f"  (got {data.get('type', '?')} — skipping)")
            print("No chat_response received in 10 messages")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_chat())
