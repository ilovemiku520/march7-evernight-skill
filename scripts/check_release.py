"""Check release structure, language parity, links and obvious credential leaks."""
from pathlib import Path
import json
import re
import sys

def check(root):
    root=root.resolve()
    errors=[]
    scanned=[]
    secret=re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{16,})\b')
    personal_path=re.compile(r'(?i)[A-Z]:[\\/]+Users[\\/]+(?!Public\b|Default\b|Example\b)[^\s"\'<>]+')
    blocked_names={'external_dialogue_memory.json','webui.json','backend-login.txt','.env'}
    for file in root.rglob('*'):
        relative=file.relative_to(root)
        if '.git' in relative.parts: continue
        if file.is_symlink(): errors.append(str(relative)+': symlink'); continue
        if not file.is_file(): continue
        if '__pycache__' in relative.parts or file.suffix in {'.pyc','.pyo','.sqlite3','.db','.log'} or file.name in blocked_names:
            errors.append(str(relative)+': private/runtime artifact'); continue
        try: text=file.read_text(encoding='utf-8-sig')
        except UnicodeError:
            errors.append(str(relative)+': unexpected binary'); continue
        scanned.append(relative.as_posix())
        if secret.search(text): errors.append(str(relative)+': credential-like literal')
        if personal_path.search(text): errors.append(str(relative)+': personal absolute path')
        if file.suffix=='.md':
            for target in re.findall(r'(?<!!)\[[^\]\n]+\]\(([^)\s]+)\)',text):
                target=target.split('#',1)[0]
                if not target or '://' in target or target.startswith(('mailto:','#')): continue
                if not (file.parent/target).resolve().is_file(): errors.append(str(relative)+': broken link '+target)
    skill=root/'skills/march7-evernight'
    canonical=json.loads((skill/'data/knowledge.zh-CN.json').read_text(encoding='utf-8'))['records']
    expected={r['id']:r for r in canonical}
    if len(expected)!=45: errors.append('summary card count')
    for code in ('en','ja','ko'):
        for required in (root/f'README.{code}.md',root/f'docs/{code}/deployment.md',skill/f'SKILL.{code}.md',
                         skill/f'references/{code}/persona-rules.md',skill/f'references/{code}/memory-policy.md'):
            if not required.is_file(): errors.append(str(required.relative_to(root))+': missing language file')
        path=skill/f'data/knowledge.{code}.json'
        if not path.is_file(): errors.append(str(path.relative_to(root))+': missing'); continue
        localized=json.loads(path.read_text(encoding='utf-8'))['records']
        if len(localized)!=45 or {r['id'] for r in localized}!=set(expected): errors.append(code+': card IDs differ')
        for r in localized:
            if r['id'] not in expected: continue
            for key in ('subject','sources','spoiler','evidence_kind'):
                if r[key]!=expected[r['id']][key]: errors.append(code+': invariant differs '+r['id']+' '+key)
    source=json.loads((skill/'data/source-index.json').read_text(encoding='utf-8'))
    if len(source['records'])!=1000: errors.append('source-index count')
    if any(set(r)!={'id','actor','title','scene','source_url','text_sha256'} for r in source['records']): errors.append('source-index field allowlist')
    config=json.loads((root/'qq-adapter/plugin/_conf_schema.json').read_text(encoding='utf-8'))
    if config['owner_qq']['default']!='' or config['enable_computer_operations']['default'] is not False:
        errors.append('unsafe public permission defaults')
    return {'result':'PASS' if not errors else 'FAIL','files_checked':len(scanned),
            'languages':['zh-CN','en','ja','ko'],'summary_cards_per_language':45,
            'source_records_without_text':1000,'errors':errors}

if __name__=='__main__':
    result=check(Path(__file__).resolve().parents[1])
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(bool(result['errors']))
