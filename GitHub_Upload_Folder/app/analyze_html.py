from bs4 import BeautifulSoup

with open('bnf_archive.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

# Find the first element containing "Atorvastatin 10mg tablets A A H" or something similar
# Or just find elements that have "Active ingredients"
for b in soup.find_all(string=lambda t: "Active ingredients" in t if t else False):
    parent = b.parent
    while parent and parent.name != 'li' and parent.name != 'div' and len(parent.find_all('div')) < 5:
        parent = parent.parent
    if parent:
        print("TAG:", parent.name, "ATTRS:", parent.attrs)
        print("HTML Snippet:", str(parent)[:1000])
        break
