import json, os, urllib.request
key = os.environ.get("GEMINI_API_KEY")
prompt = (
    "You are analyzing a Python module.\n"
    "Respond with ONLY valid JSON (no markdown fences):\n"
    "{\"intent\":\"test\",\"critical_path\":true,\"what_to_fix\":[\"fix a\"],"
    "\"break_risk\":[\"thing b\"],\"autonomous_directive\":\"do x\",\"reasoning\":\"because y\"}"
)
payload = {
    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024}
}
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={key}"
req = urllib.request.Request(url, json.dumps(payload).encode(), {"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=45) as r:
    res = json.loads(r.read())
    parts = res.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text = parts[0].get("text", "") if parts else ""
    print("RAW repr:", repr(text[:300]))
    print()
    print("RAW:")
    print(text[:400])
    print()
    # test parse
    import re
    cleaned = re.sub(r"^```[a-z]*\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    print("CLEANED repr:", repr(cleaned[:200]))
    try:
        parsed = json.loads(cleaned)
        print("PARSED OK:", list(parsed.keys()))
    except Exception as ex:
        print("PARSE FAILED:", ex)
