"""叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc_call_deepseek_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
import json
import urllib.request

def _call_deepseek(prompt: str, api_key: str) -> str | None:
    body = json.dumps({
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 800,
        'temperature': 0.45,
    }).encode('utf-8')
    req = urllib.request.Request(
        'https://api.deepseek.com/chat/completions',
        data=body,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'  [push_narrative] DeepSeek call failed: {type(e).__name__}: {e}')
        return None
