import urllib.request, json
r = urllib.request.urlopen('http://localhost:8234/state', timeout=5)
data = json.loads(r.read())
print(f'state keys: {list(data.keys()) if isinstance(data, dict) else type(data)}')
if isinstance(data, dict):
    for k, v in data.items():
        print(f'  {k}: {type(v).__name__} = {str(v)[:200]}')

# Try a test chat
payload = json.dumps({'module': 'file_heat_map', 'message': 'ping'}).encode()
req = urllib.request.Request('http://localhost:8234/chat', data=payload,
                             headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=30)
d = json.loads(resp.read())
print(f'\nchat with file_heat_map: {d.get("response", "?")[:100]}')
