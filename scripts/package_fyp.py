"""Create a source and deliverable archive from an explicit safe file allowlist."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/fyp-i'
ARCHIVE=OUT/'MediSummarize_AI_FYP-I_Package.zip'
files=[]
for name in ['README.md','.env.example','.gitignore','docker-compose.yml','backend/README.md','backend/pyproject.toml','backend/alembic.ini','frontend/package.json','frontend/package-lock.json','frontend/index.html','frontend/vite.config.ts','frontend/tsconfig.json','frontend/tsconfig.app.json','frontend/tsconfig.node.json']:
 p=ROOT/name
 if p.is_file():files.append((p,name))
for name in ['backend/app','backend/tests','backend/migrations','frontend/src','docs','scripts','data/synthetic','output/fyp-i']:
 for p in (ROOT/name).rglob('*'):
  if not p.is_file() or p.suffix in {'.pyc','.zip'} or '__pycache__' in p.parts:continue
  if p.name.startswith('.env') or p.name.startswith('~$'):continue
  files.append((p,p.relative_to(ROOT).as_posix()))
for name in ['FYP-I_Final_Report_Template.docx','FYP-I_SRS_Template.docx','FYP-I_SDS_Template.docx']:
 p=Path.home()/'Downloads'/name
 if p.exists():files.append((p,'references/templates/'+name))
# The originals containing personal contact details are deliberately outside this allowlist.
manifest={'project_code':'CS-FYP-1019','prepared_date':'2026-11-09','generation_status':'MOCK ONLY; real-model baseline pending','files':[{'path':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p,name in sorted(files,key=lambda x:x[1])]}
with zipfile.ZipFile(ARCHIVE,'w',zipfile.ZIP_DEFLATED) as z:
 for p,name in files:z.write(p,name)
 z.writestr('PACKAGE_MANIFEST.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(ARCHIVE) as z:
 names=z.namelist()
 assert z.testzip() is None
 assert not any('/.venv/' in n or '/node_modules/' in n or n.endswith('/.env') or '/data/runtime/' in n or '/storage/' in n for n in names)
 print(json.dumps({'archive':str(ARCHIVE),'files':len(names),'bytes':ARCHIVE.stat().st_size},indent=2))
