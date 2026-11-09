"""Populate cached contents/figure/table page references from a verified PDF render.

The editable Word TOC field remains present and requests refresh on open.
Only document.xml is changed. This never uses a LibreOffice save on the DOCX.
Usage: bundled-python scripts/update_fyp_document_fields.py KIND RENDER_FOLDER
"""
from pathlib import Path
import sys,re,zipfile,json
from lxml import etree as E
from pypdf import PdfReader

root=Path(__file__).resolve().parents[1]
kind=sys.argv[1];folder=Path(sys.argv[2]);pdf=next(folder.glob('*.pdf'))
target=root/'output/fyp-i'/f'MediSummarize_AI_FYP-I_{kind}.docx'
pages=[p.extract_text() or '' for p in PdfReader(pdf).pages]
toc_pages={i for i,p in enumerate(pages) if re.search(r'^Table of Contents\s*$',p,re.M)}
normalize=lambda s:re.sub(r'\s+',' ',s).strip()
labels=[]
for i,text in enumerate(pages):
 hits=re.findall(r'Page\s+([ivxlcdm]+|\d+)\b',text,re.I)
 labels.append(hits[-1] if hits else str(i+1))
def page_for(text):
 key=normalize(text);found=[]
 for i,page in enumerate(pages):
  # TOC cache has no page numbers yet. The final occurrence is the body heading/caption.
  if key in normalize(page):found.append(i)
 if not found:raise ValueError('Missing rendered reference: '+text)
 outside_toc=[i for i in found if i not in toc_pages]
 if outside_toc:found=outside_toc
 return labels[found[-1]]
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W='{'+NS['w']+'}'
with zipfile.ZipFile(target) as z:parts={n:z.read(n) for n in z.namelist()}
doc=E.fromstring(parts['word/document.xml']);inside=False;entries=[]
def reference(p,label):
 pr=p.find('w:pPr',NS)
 if pr is None:pr=E.Element(W+'pPr');p.insert(0,pr)
 tabs=pr.find('w:tabs',NS)
 if tabs is None:tabs=E.SubElement(pr,W+'tabs')
 tab=E.SubElement(tabs,W+'tab');tab.set(W+'val','right');tab.set(W+'leader','dot');tab.set(W+'pos','8800')
 # A tab run and page label preserve the editable field's existing cache text.
 r=E.Element(W+'r');E.SubElement(r,W+'tab');t=E.SubElement(r,W+'t');t.text=label
 end=p.xpath('./w:r[w:fldChar[@w:fldCharType="end"]]',namespaces=NS)
 if end:p.insert(list(p).index(end[0]),r)
 else:p.append(r)
def remove_cached_number(p):
 for r in list(p):
  if r.tag==W+'r' and r.find('w:tab',NS) is not None and r.find('w:t',NS) is not None:p.remove(r)
for p in doc.iter(W+'p'):
 instr=''.join(p.xpath('.//w:instrText/text()',namespaces=NS))
 if 'TOC ' in instr:inside=True
 if inside:remove_cached_number(p)
 text=''.join(p.xpath('.//w:t/text()',namespaces=NS))
 if inside and text:
  label=page_for(text);reference(p,label);entries.append([text,label])
 if inside and p.xpath('.//w:fldChar[@w:fldCharType="end"]',namespaces=NS):inside=False
 # Captions in the list of figures/tables are plain paragraphs. Skip real captions,
 # which immediately follow an image or precede an actual table.
for heading in doc.findall('.//w:body/w:p',NS):
 text=''.join(heading.xpath('.//w:t/text()',namespaces=NS))
 if text not in {'List of Figures','List of Tables'}:continue
 following=heading.getnext()
 while following is not None and following.tag==W+'p':
  if following.find('w:pPr/w:pStyle',NS) is not None:break
  remove_cached_number(following)
  caption=''.join(following.xpath('.//w:t/text()',namespaces=NS))
  if not caption.startswith(('Figure ','Table ')):break
  reference(following,page_for(caption));following=following.getnext()
for t in doc.iter(W+'t'):
 if t.text:t.text=t.text.replace('approved-scope proposal','supplied proposal')
 if t.text=='Nullable':t.text='Null?'
 if t.text=='SDS reference':t.text='SDS section'
parts['word/document.xml']=E.tostring(doc,xml_declaration=True,encoding='UTF-8',standalone=True)
tmp=target.with_suffix('.fields.docx')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
 for n,data in parts.items():z.writestr(n,data)
tmp.replace(target)
(folder/'cached-page-references.json').write_text(json.dumps(entries,indent=2),encoding='utf-8')
print(kind,'cached page references',len(entries))
