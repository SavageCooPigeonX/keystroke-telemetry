import json

p = json.load(open("pigeon_brain/prediction_cache.json"))
preds = p["predictions"]
print(f"{len(preds)} predictions cached")
for x in preds[-3:]:
    mode = x["mode"]
    conf = x["confidence"]
    path = x.get("result", {}).get("path", [])[:5]
    print(f"  [{mode}] conf={conf:.2f} path={path}")
