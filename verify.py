"""Check generated routes, assets, semantics and supplied catalogue completeness."""
from pathlib import Path
from html.parser import HTMLParser
import json
from urllib.parse import urlsplit,unquote
root=Path(__file__).parent/'public'
errors=[]
class Page(HTMLParser):
    def __init__(self,path):
        super().__init__();self.path=path;self.h1=0;self.title=False;self.canonical=False;self.description=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='h1':self.h1+=1
        if tag=='title':self.title=True
        if tag=='link' and a.get('rel')=='canonical':self.canonical=True
        if tag=='meta' and a.get('name')=='description':self.description=True
        if tag=='img' and 'alt' not in a:errors.append(f'{self.path}: missing alt')
        for k in ('href','src'):
            value=a.get(k,'')
            if not value.startswith('/') or value.startswith('//'):continue
            path=root/unquote(urlsplit(value).path).lstrip('/')
            if not path.exists():errors.append(f'{self.path}: broken {value}')
for path in root.rglob('*.html'):
    p=Page(path.relative_to(root));p.feed(path.read_text())
    if p.h1!=1 or not(p.title and p.canonical and p.description):errors.append(f'{p.path}: page metadata/h1')
data=json.loads((root.parent/'data.json').read_text())
for app in data:
    path=root/'apps'/app['slug']/'index.html'
    assert path.exists(),app['slug']
    expected=len(list((root.parent/'assets/screens').glob(app['slug']+'-[1-5].jpg')))
    if path.read_text().count('app screenshot ')!=expected:errors.append(f'{app["slug"]}: screenshot count differs from supplied assets')
assert (root/'privacy.html').exists()
if errors:raise SystemExit('\n'.join(errors))
print(f'PASS: {len(data)} apps; all generated pages have one h1, SEO metadata, image alt attributes, valid internal links and assets; all supplied marketing screenshots; /privacy exists.')
