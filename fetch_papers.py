"""
fetch_papers.py — 每天自动从 arXiv 拉取最新论文
由 GitHub Actions 调用，结果写入 papers_today.json
"""
import json, time, urllib.request, urllib.parse, os
from datetime import datetime, date

DATA_FILE = 'papers_today.json'

QUERIES = [
    {'q': 'ti:artificial+intelligence+AND+ti:cognition',    'cat': 'ai'},
    {'q': 'ti:large+language+model+AND+ti:human',           'cat': 'ai'},
    {'q': 'ti:psychology+AND+ti:computational',             'cat': 'psychology'},
    {'q': 'ti:mental+health+AND+ti:machine+learning',       'cat': 'psychology'},
    {'q': 'ti:digital+humanities+AND+ti:text',              'cat': 'humanities'},
    {'q': 'ti:culture+AND+ti:natural+language+processing',  'cat': 'humanities'},
]

def fetch_arxiv(query, cat, max_results=2):
    base = 'http://export.arxiv.org/api/query?'
    params = urllib.parse.urlencode({
        'search_query': query,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending',
        'max_results': max_results
    })
    try:
        with urllib.request.urlopen(base + params, timeout=12) as r:
            return parse_arxiv(r.read().decode('utf-8'), cat)
    except Exception as e:
        print(f'  error ({query[:40]}): {e}')
        return []

def get_tag(entry, tag):
    s = entry.find(f'<{tag}')
    if s < 0: return ''
    s = entry.find('>', s) + 1
    e = entry.find(f'</{tag}>', s)
    return entry[s:e].strip().replace('\n', ' ') if e > 0 else ''

def parse_arxiv(xml, cat):
    papers = []
    for entry in xml.split('<entry>')[1:]:
        title = get_tag(entry, 'title')
        abstract = get_tag(entry, 'summary')
        auth = ''
        ai = entry.find('<name>')
        if ai >= 0:
            ae = entry.find('</name>', ai)
            auth = entry[ai+6:ae].strip() if ae > 0 else ''
        link = ''
        li = entry.find('<id>')
        if li >= 0:
            le = entry.find('</id>', li)
            link = entry[li+4:le].strip()
        pub = get_tag(entry, 'published')[:4] or str(datetime.now().year)
        if not title: continue
        papers.append({
            'id': link.split('/')[-1] or title[:20],
            'title': title,
            'abstract': abstract[:600],
            'authors': (auth + ' et al.') if auth else 'Unknown',
            'year': pub,
            'venue': 'arXiv',
            'url': link,
            'cat': cat,
        })
    return papers

def run():
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M")}] Fetching papers...')
    all_papers, seen = [], set()
    for q in QUERIES:
        papers = fetch_arxiv(q['q'], q['cat'], max_results=2)
        for p in papers:
            if p['id'] not in seen:
                seen.add(p['id'])
                all_papers.append(p)
                print(f'  ✓ [{p["cat"]}] {p["title"][:55]}...')
        time.sleep(1.2)
    result = all_papers[:8]
    output = {
        'date': str(date.today()),
        'papers': result,
        'generated_at': datetime.now().isoformat()
    }
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f'Done — {len(result)} papers saved.')

if __name__ == '__main__':
    run()
