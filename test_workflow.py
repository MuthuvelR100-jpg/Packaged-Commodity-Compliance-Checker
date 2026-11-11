import requests
import json

base = 'http://127.0.0.1:5000/api'

# 1. Health check
print('=== HEALTH ===')
health = requests.get(f'{base}/health').json()
print(json.dumps(health, indent=2))

# 2. Categories
print('\n=== CATEGORIES ===')
cats = requests.get(f'{base}/categories').json()
print(json.dumps(cats, indent=2))

# 3. Rules for food category
print('\n=== RULES (food) ===')
rules = requests.get(f'{base}/rules?category=food').json()
for r in rules['items']:
    print(f"  {r['rule_code']}: {r['field_name']} | {r['validation_type']} | {r['severity']} | active={r['active']}")

# 4. Test extraction with sample OCR text
print('\n=== EXTRACTION TEST ===')
sample_text = """NESTLE MAGGI NOODLES
NET QTY: 280g
MRP: ₹55
MFD: 01/2024
MANUFACTURED BY: NESTLE INDIA LTD
CUSTOMER CARE: 1800-123-4567
EMAIL: care@nestle.in"""
extract_resp = requests.post(f'{base}/extract', json={'text': sample_text}).json()
print(json.dumps(extract_resp, indent=2))

# 5. Validate extracted fields
print('\n=== VALIDATION TEST (food category) ===')
fields = extract_resp['extraction']['fields']
validate_resp = requests.post(f'{base}/validate', json={'category': 'food', 'fields': fields}).json()
print(json.dumps(validate_resp, indent=2))

# 6. Score
print('\n=== SCORE TEST ===')
score_resp = requests.post(f'{base}/score', json={'validation': validate_resp['validation']}).json()
print(json.dumps(score_resp, indent=2))

# 7. Dashboard
print('\n=== DASHBOARD ===')
dash = requests.get(f'{base}/dashboard').json()
print(json.dumps(dash, indent=2))