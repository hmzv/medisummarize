import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'backend'))
import app.models
from app.db.base import Base
result={}
for t in Base.metadata.sorted_tables:
 rows=[]
 for c in t.columns:
  default='None'
  if c.default is not None:
   default='Generated value' if c.default.is_callable else str(c.default.arg)
  keys=['PK' if c.primary_key else '', 'UNIQUE' if c.unique else '']+[str(f.column) for f in c.foreign_keys]
  rows.append([c.name,str(c.type),'Yes' if c.nullable else 'No',default,', '.join(k for k in keys if k) or 'Non-key'])
 result[t.name]=rows
(Path(__file__).resolve().parents[1] / 'tmp/artifacts/schema.json').write_text(json.dumps(result,indent=2))
