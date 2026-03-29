"""Quick e2e test: send a chat message to the WS server and print the response."""
import asyncio
import json

async def test():
    try:
        import websockets
    except ImportError:
        print("ERROR: websockets not installed")
        return

    uri = "ws://127.0.0.1:8769"
    try:
        async with websockets.connect(uri) as ws:
            # Send a chat message
            msg = json.dumps({
                "type": "chat",
                "message": "What modules are in the pigeon_brain folder?",
                "selectedNode": None,
            })
            await ws.send(msg)
            print("Sent chat message, waiting for response...")

            # Wait for chat_response (skip events/history)
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=45)
                data = json.loads(raw)
                if data.get("type") == "chat_response":
                    text = data.get("text", "")
                    print(f"\n=== GEMINI RESPONSE ({len(text)} chars) ===")
                    print(text[:500])
                    if len(text) > 500:
                        print(f"... ({len(text)-500} more chars)")
                    break
                else:
                    print(f"  (got {data.get('type', '?')} message, waiting for chat_response...)")
    except asyncio.TimeoutError:
        print("ERROR: Timeout waiting for Gemini response (45s)")
    except Exception as e:
        print(f"ERROR: {e}")

asyncio.run(test())
