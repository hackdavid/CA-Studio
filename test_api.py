import urllib.request, json

resp = urllib.request.urlopen('http://localhost:8000/api/rules/')
rules = json.loads(resp.read().decode())
for r in rules:
    if 'Conway' in r['name'] or 'Life' in r['name']:
        print(f"ID: {r['id']}, Name: {r['name']}")
