import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

base = 'http://127.0.0.1:5000/api'

sample_text = """SUNRISE DETERGENT POWDER
NET QTY: 1kg
MRP: Rs 180
MFD: 03/2024
MANUFACTURED BY: SUNRISE PRODUCTS PVT LTD
ADDRESS: PLOT 12, INDUSTRIAL AREA, DELHI
CUSTOMER CARE: 1800-456-7890
EMAIL: support@sunrise.in"""

print('=== EXTRACTION ===')
extract_resp = requests.post(f'{base}/extract', json={'text': sample_text}).json()
extraction = extract_resp['extraction']
print(f"Detected: {extraction['detected_count']}/{extraction['field_count']} fields")
for fname, fdata in extraction['fields'].items():
    if fdata['status'] == 'detected':
        print(f"  {fname}: {fdata['value']}")

print('\n=== VALIDATION (other_packaged_commodities) ===')
validate_resp = requests.post(f'{base}/validate', json={
    'category': 'other_packaged_commodities',
    'fields': extraction['fields']
}).json()
validation = validate_resp['validation']
print(f"Overall status: {validation['status']}")
print(f"Rule count: {validation['rule_count']}")
for result in validation['results']:
    print(f"  {result['field_name']}: {result['status']} | {result['message']} | mandatory={result['mandatory']} severity={result['severity']}")

print('\n=== SCORE ===')
score_resp = requests.post(f'{base}/score', json={'validation': validation}).json()
score = score_resp['score']
print(f"Score: {score['score']}%")
print(f"Status: {score['status']}")
print(f"Message: {score['message']}")
print(f"Passed: {score['passed_count']}/{score['applicable_count']}")
print(f"Failed: {score['failed_count']} - {score['failed_fields']}")
print(f"Critical failures: {len(score['critical_failures'])}")