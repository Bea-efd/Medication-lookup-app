import requests

url = "http://web.archive.org/web/20240101000000/https://bnf.nice.org.uk/drugs/atorvastatin/medicinal-forms/"
try:
    response = requests.get(url, timeout=20)
    with open('bnf_archive.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("Success")
except Exception as e:
    print(f"Error: {e}")
