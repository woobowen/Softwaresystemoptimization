import concurrent.futures,datetime,hashlib,io,json,re,subprocess,sys,time,urllib.request
from pathlib import Path
from urllib.parse import urlsplit,unquote
from PIL import Image
sha=sys.argv[1];out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
repository='woobowen/Softwaresystemoptimization'
def fetch(url):
 for attempt in range(3):
  try:
   request=urllib.request.Request(url,headers={'User-Agent':'A2-final-file-verification','Accept':'application/vnd.github+json'})
   with urllib.request.urlopen(request,timeout=40) as response:
    return response.status,response.read()
  except Exception:
   if attempt==2:raise
   time.sleep(2)
remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],text=True).split()[0]
assert remote==sha,(remote,sha)
tree_url=f'https://api.github.com/repos/{repository}/git/trees/{sha}?recursive=1'
status,data=fetch(tree_url);tree=json.loads(data);assert status==200 and tree['sha']==sha and not tree['truncated']
paths={x['path'] for x in tree['tree']}
required=[Path('A2/README.md'),Path('A2/evidence/requirement-matrix.md'),Path('A2/evidence/formal-campaign/final-timing-audit.md'),Path('A2/evidence/formal-campaign/final-data-audit.json'),Path('A2/evidence/formal-campaign/final-statistics.json'),Path('A2/evidence/formal-campaign/restore.json'),Path('A2/evidence/final/final-value-map.md')]
required+=sorted(Path('A2/scripts').glob('*'))+sorted(Path('A2/images').glob('*.png'))
required+=[p for p in sorted(Path('A2/results').rglob('*')) if p.is_file()]
assert all(str(p) in paths for p in required)
def check(p):
 url=f'https://raw.githubusercontent.com/{repository}/{sha}/{p}'
 status,data=fetch(url);digest=hashlib.sha256(data).hexdigest()
 assert status==200 and digest==hashlib.sha256(p.read_bytes()).hexdigest(),p
 if p.suffix.lower() in ('.png','.jpg'):
  with Image.open(io.BytesIO(data)) as image:image.verify()
 return {'path':str(p),'url':url,'http_status':status,'bytes':len(data),'sha256':digest,'matches_local':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 records=list(pool.map(check,required))
url=f'https://raw.githubusercontent.com/{repository}/{sha}/A2/README.md'
status,data=fetch(url);readme=data.decode()
links=[]
for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',readme):
 u=urlsplit(link)
 if not u.scheme and not u.netloc and u.path:
  assert not u.path.startswith('/')
  target=str(Path('A2')/unquote(u.path)).rstrip('/')
  assert target in paths,target
  links.append(target)
assert [int(n) for n in re.findall(r'^## (\d+)\.',readme,re.M)]==list(range(1,8))
assert not re.search(r'\b(?:Codex|ChatGPT|AI|Prompt|TODO|PASS|BLOCKED|UNVERIFIED|audit|campaign)\b',readme,re.I)
assert not any(v in readme for v in ['482.49','801.24','787.96','812.58','800.59','800.08','804.42','806.48','803.66'])
record={'at':datetime.datetime.now().astimezone().isoformat(),'sha':sha,'git_remote_sha':remote,'local_equals_remote':True,'tree_url':tree_url,'tree_response_sha256':hashlib.sha256(json.dumps(tree,sort_keys=True).encode()).hexdigest(),'remote_tree_entries':len(tree['tree']),'files_actually_downloaded':records,'readme_relative_links':links,'readme_Q1_Q7_complete':True,'old_values_TODO_internal_terms_absent':True,'passed':True}
(out/'file-verification.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'sha':sha,'remote':remote,'downloaded_files':len(records),'bytes':sum(r['bytes'] for r in records),'relative_links':len(links),'passed':True},indent=2))
