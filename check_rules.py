import requests, json

base = 'http://127.0.0.1:5000/api'
for cat in ['other_packaged_commodities', 'household_products', 'cosmetics', 'electronics', 'clothing', 'personal_care']:
    r = requests.get(f'{base}/rules?category={cat}').json()
    active = [x for x in r['items'] if x['active']]
    print(f'{cat}: {len(active)} active rules')
    for a in active:
        print(f'  {a["rule_code"]}: {a["field_name"]} | {a["validation_type"]} | {a["severity"]}')