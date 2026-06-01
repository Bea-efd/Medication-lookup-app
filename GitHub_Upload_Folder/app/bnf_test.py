import requests
from bs4 import BeautifulSoup
import sys

url = "https://bnf.nice.org.uk/drugs/atorvastatin/medicinal-forms/"
response = requests.get(url, timeout=10)
soup = BeautifulSoup(response.text, 'html.parser')

print(soup.get_text(separator='\n', strip=True))
