from pigeon_compiler.rename_engine import bump_version, mutate_compressed_stem
e = {
    'path': 'test.py', 'name': 'test', 'seq': 1, 'ver': 1,
    'date': '0401', 'desc': 'x', 'intent': 'fix',
    'history': [{'ver': 1}]
}
r = bump_version(e, new_desc='new', new_intent='build')
print(f"bump_version: ver={r['ver']}, date={r['date']}")

m = mutate_compressed_stem('改名f_rr_s006_v005_d0401_追跑拆谱建_λA', new_ver=6, new_intent='FX')
print(f"mutate_compressed: {m}")
print("ALL OK")
