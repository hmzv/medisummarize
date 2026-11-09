"""Create the FYP I documentation in copies of the supplied university templates."""
from pathlib import Path
from copy import deepcopy
import json, re, zipfile, hashlib, math, sys
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/fyp-i'; TMP=ROOT/'tmp/artifacts'; FIG=ROOT/'docs/fyp-i/figures'
for d in [OUT,TMP,FIG]:d.mkdir(parents=True,exist_ok=True)
DOWNLOADS=Path.home()/'Downloads'
SUP='Dr. Muhammad Yaseen Khan'; CODE='CS-FYP-1019'; DATE='09 November 2026'
TEAM=['Muhammad Humayun Dar - 23K-0795','Muhammad Hamza Siddiqui - 23K-0500','Hassan Sheikh - 22K-5157']
TITLE='MediSummarize AI'
ABSTRACT=('Clinical information can be distributed across laboratory reports, prescriptions, discharge notes, and scanned pages. MediSummarize AI is a research prototype that organizes synthetic clinical documents into a structured summary with links to source passages. The prototype combines authenticated record ownership, file validation, page-aware extraction, optical character recognition, chunking, record-specific retrieval, and a summary review interface. The current implementation uses React and TypeScript for the interface and FastAPI with SQLAlchemy for the application services. A local SQLite database supports the demonstration, while PostgreSQL remains the intended deployment database. The default retrieval configuration uses lexical hashing and exact cosine search. A separately configurable language-model adapter supports a local compatible inference server, but the current environment uses explicitly labeled mock generation. Automated tests exercise authentication, isolation, ingestion, extraction, retrieval, structured output, and source lifecycle behavior. The evaluation harness compares retrieved chunks with a full-text baseline under the same generation provider and excludes mock scores from reportable results. FYP I establishes the document workflow and evaluation procedure. Real-model comparative results remain outstanding. FYP II will investigate semantic embeddings, model adaptation where feasible, expanded evaluation, role-based authorization, and deployment security. The system requires source verification and provides no diagnosis or prescribing capability.')
REFERENCES=[
'[1] P. Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," Advances in Neural Information Processing Systems, vol. 33, pp. 9459-9474, 2020. https://arxiv.org/abs/2005.11401.',
'[2] E. Alsentzer et al., "Publicly Available Clinical BERT Embeddings," Proceedings of the 2nd Clinical Natural Language Processing Workshop, pp. 72-78, 2019. doi: 10.18653/v1/W19-1909. https://aclanthology.org/W19-1909/.',
'[3] C.-Y. Lin, "ROUGE: A Package for Automatic Evaluation of Summaries," Text Summarization Branches Out, pp. 74-81, 2004. https://aclanthology.org/W04-1013/.',
'[4] MediSummarize AI project team, "FYP I Project Proposal," FAST NUCES Karachi, Fall 2026, supplied project proposal.',
'[5] MediSummarize AI project team, "Prototype source code and verification record," repository snapshot, 09 Nov. 2026. See docs/project-status.md, backend/tests, and frontend/src.'
]
# Requirement, statement, use case, SDS section, verification and implementation status.
FR=[
('FR-001','The system shall register a demonstration account using a unique email and a password of at least 10 characters.','UC-USER-01','5.6','TC-001 / test_auth.py','Implemented'),
('FR-002','The system shall authenticate a registered user and allow the user to end the browser session.','UC-USER-01','5.6','TC-002 / test_auth.py','Implemented'),
('FR-003','The system shall create and list fictional patient records owned by the authenticated account.','UC-USER-02','5.1','TC-003 / test_records.py','Implemented'),
('FR-004','The system shall filter the visible record list by case label and order it by label or creation date.','UC-USER-02','5.5.1','TC-004 / manual UI check','Implemented; browser check pending'),
('FR-005','The system shall accept PDF, PNG, JPEG and UTF-8 text uploads only after server-side content validation.','UC-USER-03','5.3.2','TC-005 / test_documents.py','Implemented'),
('FR-006','The system shall retain each accepted original outside the web root and permit only its owner to download it.','UC-USER-03','5.6','TC-006 / test_documents.py','Implemented'),
('FR-007','The system shall extract text by page and apply OCR to images or PDF pages with insufficient native text.','UC-USER-04','5.4','TC-007 / test_extraction.py','Implemented'),
('FR-008','The system shall show extracted text with page number, extraction method, and available OCR warnings.','UC-USER-04','5.5.1','TC-008 / extraction tests and UI review','Implemented; browser check pending'),
('FR-009','The system shall chunk extracted pages with document and page provenance and index each record independently.','UC-USER-05','5.4','TC-009 / test_chunking.py, test_retrieval.py','Implemented'),
('FR-010','The system shall retrieve passages only after authorizing the requested record for the current user.','UC-USER-05','5.6','TC-010 / test_retrieval.py','Implemented'),
('FR-011','The system shall produce fixed sections for history, findings, medications, allergies, laboratory findings and unresolved information.','UC-USER-05','5.4','TC-011 / test_summaries.py','Mock verified; real provider pending'),
('FR-012','The system shall move claims with no valid source ID into unresolved information and expose valid citations to the reviewer.','UC-USER-06','5.4','TC-012 / test_summaries.py, SummaryReview.test.tsx','Implemented'),
('FR-013','The system shall export text or JSON including sources, provider metadata, disclaimer and mock labeling.','UC-USER-06','5.5.1','TC-013 / export inspection','Implemented; download check pending'),
('FR-014','The system shall invalidate stored summaries after a source upload, re-extraction or deletion.','UC-USER-07','5.6','TC-014 / test_summaries.py lifecycle test','Implemented'),
('FR-015','The system shall run retrieved-context and non-retrieval baseline conditions while quarantining mock scores.','UC-EVAL-01','5.4','TC-015 / test_evaluation.py, test_evaluation_harness.py','Mock dry run complete'),
('FR-016','The system shall classify uploads by supported file kind and preserve the detected media type.','UC-USER-03','5.1','TC-016 / test_documents.py','Implemented; clinical classification deferred'),
]
NFR=[
('NFR-001','Performance','The client shall end a summary request after 120 seconds and display a recoverable error.','UC-USER-05','5.5.2','TC-017 / timeout inspection','Implemented timeout; latency unvalidated'),
('NFR-002','Performance','Each evaluation condition shall record generation duration and the retrieved condition shall record retrieval duration in milliseconds.','UC-EVAL-01','5.4','TC-018 / evaluation JSON','Implemented'),
('NFR-003','Safety','Every application view and exported summary shall display the research and source-verification disclaimer.','UC-USER-06','5.5.1','TC-019 / disclaimer test and export inspection','Implemented'),
('NFR-004','Safety','All mock summaries shall carry MOCK/TEST OUTPUT and all mock evaluation rows shall have reportable=false.','UC-EVAL-01','5.4','TC-020 / generation and evaluation tests','Verified'),
('NFR-005','Security','Protected requests from a different owner shall return 404 without disclosing record contents.','UC-USER-02','5.6','TC-021 / isolation tests','Verified'),
('NFR-006','Security','Passwords shall persist only as bcrypt hashes and bearer tokens shall never enter application URLs.','UC-USER-01','5.6','TC-022 / auth tests and source inspection','Implemented'),
('NFR-007','Security','Default upload limits shall be 15 MiB per file, 50 pages per PDF and 2 MiB per text file, enforced on the server.','UC-USER-03','5.6','TC-023 / validation tests','Implemented; configurable'),
('NFR-008','Reliability','Unavailable generation shall produce an explicit error without silently substituting mock output.','UC-USER-05','5.4','TC-024 / provider inspection','Implemented; real outage run pending'),
('NFR-009','Usability','Core views shall operate at 375 px and 1280 px viewport widths with visible keyboard focus and labeled fields.','UC-USER-06','5.5.1','TC-025 / browser and keyboard check','Implemented; visual check pending'),
('NFR-010','Maintainability','The project shall document commands for backend tests, frontend tests and a production frontend build.','UC-EVAL-01','7','TC-026 / verification record','Verified'),
('NFR-011','Portability','The prototype shall support SQLite locally and retain a configurable PostgreSQL connection.','UC-EVAL-01','3.3','TC-027 / configuration tests','SQLite verified; PostgreSQL pending'),
('NFR-012','Reliability','The UI shall retain only unsuccessful files after a partial batch upload so retries do not duplicate successful files.','UC-USER-03','5.5.1','TC-028 / RecordDetailPage.test.tsx','Verified'),
]
STACK=[['Interface','React 19, TypeScript 5, Vite 7, Tailwind CSS 4','Typed browser interface and responsive styles'],['API','FastAPI, Pydantic, SQLAlchemy, Alembic','Validated routes, ownership and migrations'],['Local data','SQLite and protected local files','Current demonstration configuration'],['Intended data','PostgreSQL 16 or newer','Multi-user deployment remains unverified'],['Extraction','PyMuPDF, Pillow, Tesseract','Native text, image validation and OCR'],['Retrieval','hashed-token-v1, NumPy exact cosine','Current lexical baseline without model download'],['Generation','mock-test-v1; local-model adapter','Mock verified; real LLM remains pending']]
RISKS=[['Unsupported output','High','High','Validate structure and sources; require manual review.'],['OCR noise or lost negation','Medium','High','Compare OCR warnings with original pages.'],['No model or GPU','High','High','Reserve compute; exclude mock performance claims.'],['Cross-record leakage','Medium','High','Authorize before search and run isolation tests.'],['Clinical-data access','Medium','High','Use fictional cases and institutional approval.'],['Schedule and sign-off','Medium','Medium','Freeze scope and review outstanding evaluation.']]
TEAM_ROWS=[['Muhammad Humayun Dar','23K-0795','Model research and evaluation design'],['Muhammad Hamza Siddiqui','23K-0500','Ingestion, OCR and API/RAG services'],['Hassan Sheikh','22K-5157','Authentication, frontend and security checks']]
ABBR=[['API','Application Programming Interface'],['FYP','Final Year Project'],['JWT','JSON Web Token'],['LLM','Large Language Model'],['OCR','Optical Character Recognition'],['RAG','Retrieval-Augmented Generation'],['SDS','Software Design Specification'],['SRS','Software Requirements Specification']]
T=lambda headers,rows:('table',headers,rows)
I=lambda name,caption:('image',name,caption)
B=lambda text:('sub',text)
UCS=[
('UC-USER-01','Manage session','FR-001, FR-002, NFR-006','Reviewer opens registration or login.','An unused fictional email for registration or an existing account for login.','A session opens Records; sign-out clears it.','Enter credentials and submit; validate; return session and open Records.','Invalid or duplicate credentials: display error. Network failure: retry. No account lockout is claimed.'),
('UC-USER-02','Manage records','FR-003, FR-004, NFR-005','Reviewer opens Records.','An authenticated session.','An owned record exists or matching owned records appear.','Enter fictional label; create record; search or sort labels; open record.','Blank label: reject. No matches: clear search. Missing or foreign record: 404.'),
('UC-USER-03','Upload and download documents','FR-005, FR-006, FR-016, NFR-007, NFR-012','Reviewer selects or drops files.','An owned record.','Validated sources persist and remain owner-downloadable.','Choose files; validate each file; store metadata and bytes; list documents; request original.','Reject unsupported or oversized files. Partial batch retains failed and unattempted files. Foreign access: 404.'),
('UC-USER-04','Extract and review text','FR-007, FR-008','Reviewer requests extraction or text review.','An accepted source in an owned record.','Pages and warnings are available, or processing reports failure.','Extract native text or apply OCR; preserve metadata; display text for verification.','Missing OCR, unreadable file or empty text: report failure and permit retry with a clearer source.'),
('UC-USER-05','Generate summary','FR-009, FR-010, FR-011, NFR-001, NFR-008','Reviewer chooses Generate summary.','An owned record with extracted or indexed text.','Structured output persists with passages and provider metadata.','Authorize; retrieve section-relevant chunks; build prompt; call provider; validate JSON and sources; display result.','Provider or JSON failure: explicit error. Missing evidence: state unavailable. Mock mode: persistent mock label.'),
('UC-USER-06','Verify and export summary','FR-012, FR-013, NFR-003, NFR-009','Reviewer opens Summary and evidence.','A current stored summary.','Reviewer can locate sources and export the research result.','Choose citation; highlight passage; open source page; compare original; export text or JSON.','Missing source: unavailable error and regenerate. No claim: display unavailable information. Browser download settings may need user action.'),
('UC-USER-07','Remove source or record','FR-014','Reviewer chooses Delete.','Ownership and explicit in-app confirmation.','Resource is removed and stale summaries cannot return.','Confirm; authorize; remove bytes and derived text/chunks; invalidate summary; refresh.','Cancel: no changes. Foreign or missing resource: 404. File-system errors require operator investigation.'),
('UC-EVAL-01','Evaluate prototype','FR-015, NFR-002, NFR-004, NFR-010, NFR-011','Evaluator runs scripts/evaluate.py.','Synthetic cases and explicitly configured provider.','JSON and CSV record both conditions and reporting eligibility.','Load fixed splits; chunk; retrieve top four per section; run same provider on both conditions; score; quarantine mock or invalid output.','Provider failure stops run. Image cases use labeled text companions in this harness. Mock execution makes no real-model quality claim.'),
]
TRACE=[list((r[0],r[2],'SDS '+r[3],r[4],r[5],'Must')) for r in FR]+[list((r[0],r[3],'SDS '+r[4],r[5],r[6],'Must')) for r in NFR]
MANIFEST=json.loads((ROOT/'data/synthetic/manifest.json').read_text(encoding='utf-8'))
DATA_ROWS=[[c['id'],c['split'],c['purpose'],', '.join(c['files'])] for c in MANIFEST['cases']]
SRS={
'1.1': ['This Software Requirements Specification defines release 1.0 of MediSummarize AI, project '+CODE+'. It provides a testable baseline for the prototype described in the supplied proposal [4]. Requirements represent the intended FYP I release. Status columns distinguish implementation from verification and outstanding research work.'],
'1.2':[T(['Audience','Use'],[['Supervisor and committee','Review scope, evidence and acceptance.'],['Project team','Implement, test and maintain requirements.'],['Reviewer / demonstrator','Complete the synthetic document workflow.']])],
'1.3':[T(['Term','Definition'],ABBR)],
'1.4':['FR identifiers name functional requirements. NFR identifiers name measurable quality requirements. UC identifies use cases and TC identifies verification cases. Must means required for FYP I acceptance. Implemented does not imply clinical validation. This specification uses the source template typography and numbering.'],
'2.1':['The proposal concerns fragmented clinical documents and document-grounded summarization [4]. Retrieval can supply external passages to a language model [1]. This project tests a local workflow on fictional records rather than assuming general-domain generation is reliable for clinical use.'],
'2.2':['A reviewer needs to consolidate mixed file formats while retaining the evidence behind each generated claim. The prototype must expose failed extraction, absent information and invalid citations. It must keep accounts and fictional patient records isolated.'],
'2.3':['The product is a standalone academic web application. It has no hospital information system, live EHR, pharmacy or clinical-decision integration. Figure 1 defines the external actors and local provider boundary.',I('context','Figure 1: System context and external entities')],
'2.4':['The product supports account sessions, owned record organization, validated document ingestion, page-text review, isolated retrieval, structured summaries, evidence navigation, export, and an offline evaluation command. Detailed behavior appears in Section 4.'],
'2.5':['FYP I includes synthetic-data preparation, requirements, design documentation, basic OCR and retrieval, a protected web interface, and an initial evaluation procedure. An actual language-model baseline assessment is still required before the research success criterion can close.','FYP II includes semantic retrieval experiments, optional model adaptation, broader evaluation, role permissions, audit logging, encryption and deployment hardening. Diagnosis, prescribing, hospital integration and identifiable patient records remain outside this release.'],
'2.6':['O1: Process accepted sample files into reviewable text and retain page provenance. O2: Return structured output with valid source references or unavailable information. O3: Reject cross-account access to records and derived data. O4: Compare retrieved-context and full-text conditions using the same real provider and fixed held-out cases. O5: provide a reproducible demo and traceable specification package. O4 remains open in the current environment.'],
'2.7':[T(['Stakeholder','Interest','Concern'],[['Supervisor','Academic scope and approval','Evidence matches implementation.'],['Project team','Delivery and maintainability','Reproducibility and clear ownership.'],['Academic reviewer','Assess feasibility','No fabricated quality claims.'],['Intended clinician reviewer','Future usability feedback','Source traceability and unsupported claims.']])],
'2.8':[T(['User class','Characteristics','Skill','Functions'],[['Research reviewer','Account holder using fictional cases','Basic web skills','Upload, inspect, summarize and export.'],['Evaluator / developer','Runs local services and harness','Technical','Configure provider and collect evidence.']]),'No separate administrator or clinician role exists in FYP I. Account ownership supplies the authorization boundary.'],
'2.9':['Development uses Windows and Python 3.11 or newer with Node.js 20 or newer. The browser loads a local React interface; FastAPI serves the API. SQLite supports the current local demo. PostgreSQL is planned but has not been validated here. Tesseract is needed for scan OCR. A real compatible generation server is a separate optional service until configured.'],
'2.10':['The release uses the existing React, TypeScript and FastAPI codebase. It must run without mandatory cloud APIs or automatic large-model downloads. File validation limits are configurable. The project has a semester deadline and no documented GPU allocation. The interface and synthetic text currently target English.'],
'2.11':['Assumptions: synthetic records remain fictional, the reviewer checks every generated claim, and local storage is available. Dependencies: Python/Node packages, Tesseract for scans, and a compatible local inference service for real-model experiments. No availability guarantee or institutional approval for patient data is assumed.'],
'2.12':[T(['Rule','Required behavior','Source'],[['BR-01','One record represents one fictional patient.','Proposal [4]'],['BR-02','Only the account owner accesses a record and its sources.','Ownership design [5]'],['BR-03','Missing evidence must remain unresolved.','Proposal [4]'],['BR-04','Mock output is excluded from model-quality findings.','Evaluation design [5]']])],
'2.13':['Use only synthetic material in the current prototype. Future access to clinical datasets requires the applicable authorization, terms and institutional process. The project makes no regulatory certification claim. Dependencies and future model weights need license review before redistribution. Supervisor review, declaration signatures and similarity checking remain human submission steps.'],
'3.1':['The interface provides login, registration, record list/search, record detail, documents, summary/evidence, demo guide and system status views. Controls must have clear action labels, visible focus, loading and error states. Destructive actions require confirmation. Detailed screen design is in SDS Section 5.5.1.'],
'3.2':['Not applicable: the prototype has no direct sensor, scanner-driver or medical-device interface. Existing files can originate from a scan, but upload uses the browser file picker. Compute capacity for a real model must be assessed separately.'],
'3.3':[T(['Interface','Version / contract','Purpose','Data'],[['FastAPI','/api/v1','Application endpoints','JSON, multipart files, bytes'],['SQLAlchemy','Installed backend dependency','Metadata persistence','Rows and foreign keys'],['Tesseract','Local executable','Image OCR','Images, text and confidence'],['Inference server','Compatible /v1/chat/completions','Real generation when configured','Prompt messages and JSON text']])],
'3.4':['Local development uses HTTP over loopback. The frontend proxy forwards /api to port 8000. Protected requests use bearer tokens in the Authorization header. Uploads use multipart/form-data and other responses use JSON. HTTPS/TLS, production origin configuration and deployment key management belong to FYP II. No email, SMS or WebSocket interface exists.'],
'4.1':['1. Session management: registration, login and sign-out (UC-USER-01). 2. Record organization: create, search, sort and open (UC-USER-02). 3. Sources: validate, upload and download (UC-USER-03), extract and review (UC-USER-04), delete (UC-USER-07). 4. Summarization: retrieve and generate (UC-USER-05), verify and export (UC-USER-06). 5. Evaluation: run both conditions and preserve evidence (UC-EVAL-01).'],
'4.2':['Figure 2 shows the reviewer and evaluator use cases. Provider and OCR interactions are supporting services within the system context.',I('usecases','Figure 2: Prototype use cases')],
'4.3':[],
'4.4':[T(['ID','Requirement','Priority','Use case','Source'],[[r[0],r[1],'Must',r[2],'Proposal [4] / prototype [5]'] for r in FR])],
'5.':['The following requirements are acceptance targets and verifiable conditions. A stated target is not a measured performance result. No clinical accuracy threshold is asserted before a real-model pilot and supervisor agreement.'],
'6.':[T(['Entity','Description','Key attributes'],[['User','Demonstration account','ID, unique email, password hash'],['PatientRecord','Owned fictional case','ID, owner, display label'],['Document','Validated original metadata','Kind, checksum, storage name, status'],['ExtractedPage','Page text with provenance','Page, method, warnings, OCR confidence'],['Chunk','Searchable passage','Offsets, source page, embedding model'],['Summary','Generated review snapshot','JSON, evidence, provider, model, mock flag']]),'Data remains local until the owner deletes the source or record. Derived summaries invalidate on source changes. There is no scheduled retention or backup service. The operator should copy the synthetic demonstration database and uploads consistently while services are stopped. Real patient data is excluded.'],
'7.':['Deliver README setup commands, the in-app Demo guide, docs/demo-script.md, API/security/architecture notes, the evaluation protocol, this SRS and the companion SDS/report. The user guide includes common recovery actions for connection, extraction and provider failures.'],
'8.':[T(['Req. ID','Acceptance condition','Verification'],[[r[0],r[1].replace('The system shall','Given an owned synthetic record, verify the system can'),r[4]] for r in FR]),'All Must requirements require passing evidence or an explicitly accepted deviation. The supervisor approves academic scope and final acceptance. Real-model baseline comparison, manual browser checks and supervisor sign-off remain open. No approval is implied by generating this document.'],
'9.':[T(['Req. ID','Use case','SDS reference','Test case','Status','Priority'],TRACE)],
'References':REFERENCES,
'Appendices':[B('Appendix A Outstanding acceptance items'),T(['Issue','Owner','Closure condition'],[['Real-model baseline','Muhammad Humayun Dar','Run fixed held-out conditions and review claims.'],['Browser and export checks','Hassan Sheikh','Verify desktop/mobile views and downloaded artifacts.'],['Deployment and embeddings','Muhammad Hamza Siddiqui','Record selected provider and database configuration.'],['Sign-off and similarity','Project team and supervisor','Complete institutional review and signature process.']])]
}
for uc in UCS:
 SRS['4.3'] += [B(uc[0]+' '+uc[1]),T(['Field','Value'],[['Actor','Evaluator' if uc[0].startswith('UC-EVAL') else 'Research reviewer'],['Priority','Must'],['Trigger',uc[3]],['Preconditions',uc[4]],['Postconditions',uc[5]],['Related requirements',uc[2]]]),B('Main scenario'),uc[6],B('Alternate scenarios and exceptions'),uc[7]]
for sec,cat in [('5.1','Performance'),('5.2','Safety'),('5.3','Security'),('5.4','Reliability'),('5.5','Usability'),('5.6','Maintainability')]:
 chosen=[r for r in NFR if r[1]==cat or (sec=='5.6' and r[1]=='Portability')]
 SRS[sec]=[T(['ID','Requirement','Verification','Priority'],[[r[0],r[2],r[5],'Must'] for r in chosen])]
SDS={
'Document Information':[T(['Field','Value'],[['Customer','FAST NUCES Karachi FYP I academic review'],['Project',TITLE+' / '+CODE],['Document','Software Design Specification'],['Document version','1.0'],['Related SRS','1.0'],['Status','Prepared for supervisor review'],['Authors','; '.join(TEAM)],['Approver',SUP+' (approval pending)'],['Issue date',DATE],['Location','D:/fyp/output/fyp-i']])],
'Definitions, Acronyms and Abbreviations':[T(['Term','Description'],ABBR)],
'1.1':['This SDS explains how release 1.0 satisfies the companion SRS. Developers use it for implementation, testers derive verification from its interfaces, and reviewers compare design intent with the current source snapshot [5].'],
'1.2':['The project team, supervisor, evaluation committee and future maintainers are the intended readers. Requirements, actors and scope are defined in SRS Sections 1 and 2.'],
'1.3':['The design separates the browser, authenticated API, document processing, isolated retrieval and generation providers. See SRS Section 2 for product purpose and constraints. The proposal defines the phased delivery boundary [4].'],
'1.4':['This design covers FYP I session ownership, sources, page extraction, lexical retrieval, summary validation and review. It also identifies interfaces for a real model and semantic embedding provider. Role-based workflows, durable queues, encryption, audit logs and model adaptation remain FYP II designs rather than implemented capabilities.'],
'1.5':['UML-style component, sequence and state views describe structure and behavior. DFDs distinguish processes, data stores and actors. Entity diagrams show primary/foreign keys and one-to-many relations. Section 6 maps every SRS FR and NFR to a design element and verification case.'],
'2.1':['Design dependencies include SQLAlchemy sessions, Alembic migration head 0006_summaries, Tesseract on PATH for OCR, and the compatible generation response contract. Embedding vectors must use the same model identifier and dimension during indexing and querying. The client assumes /api is proxied or configured explicitly.'],
'2.2':['See SRS Sections 2.9 and 2.10. The current design retains a local lexical baseline and avoids automatic neural-model downloads. A record index uses exact cosine search; the implementation does not currently use FAISS or Milvus. Requests and in-process jobs lack distributed coordination, limiting multi-worker operation.'],
'2.3':[T(['Goal','Priority','Design support'],[['Ownership isolation','1','Authorize record before retrieving its index.'],['Source traceability','1','Carry document, page, offsets and citation IDs.'],['Honest research evidence','1','Explicit provider identity and mock quarantine.'],['Maintainability','2','Typed schemas and provider boundaries.'],['Local feasibility','2','SQLite and lexical embeddings without downloads.']])],
'2.4':[T(['Volatile area','Impact','Design mitigation'],[['Generation model','High','Provider interface, fixed schema and explicit errors.'],['Embedding selection','High','Persist model and dimension; reject mismatched index.'],['OCR accuracy','High','Preserve original and warnings; manual verification.'],['Concurrency / deletion','High','Use one local worker for demo; add transactional job/version controls in FYP II.'],['Storage migration','Medium','Database URL and storage paths remain configuration.']])],
'3.1':['Figure 1 partitions the runtime. The reviewer enters through the browser. The API coordinates independently replaceable extraction, retrieval and generation services. Metadata, source bytes and vectors persist in separate stores.',I('architecture','Figure 1: System level component architecture'),T(['Component','Responsibility','Interface'],[['React UI','Session, source and summary review','JSON API / multipart'],['FastAPI routes','Validate request and ownership','Pydantic schemas'],['Ingestion / extraction','Validate, store and extract pages','Document and ExtractedPage'],['Retrieval','Build and search owned indexes','Chunk IDs and evidence text'],['Generation','Call configured provider','Structured JSON text'],['Persistence','Metadata, bytes and vectors','SQLAlchemy and local paths']])],
'3.2':['The client calls API routes. Route dependencies supply an authenticated user and database session. Services enforce ownership and coordinate processing. SQLAlchemy models define metadata. Provider modules isolate generation and embedding choices. Data does not pass directly from a browser to a filesystem path.',I('layers','Figure 2: Layered software architecture')],
'3.3':['The verified configuration is a single local development machine. Vite uses port 5173, FastAPI uses 8000 and SQLite stores local metadata. A real inference service would use a separate loopback endpoint, commonly 11434. Production TLS, PostgreSQL and multiple workers remain unverified.',I('deployment','Figure 3: Local deployment and planned inference node')],
'3.4':[T(['Layer','Technology','Version / status','Justification'],[[r[0],r[1],'See lockfile / backend environment',r[2]] for r in STACK])],
'4.':[B('Future extension and reuse'),'GenerationProvider and EmbeddingProvider define replacement points. A SentenceTransformers adapter exists but no neural model has been validated in this environment. React, FastAPI, SQLAlchemy and Tesseract provide existing framework capabilities. Dependency/model licenses require review before redistribution.',B('User interface paradigm'),'A responsive browser workspace uses persistent navigation, a searchable record list and separate document/summary tabs. It exposes loading, empty and failure states. No clinical assessment controls exist.',B('Data management'),'Metadata uses SQLAlchemy. Source bytes use UUID-based local paths outside the web root. Per-record vectors and mappings persist as NumPy and JSON files. Uploaded filenames are display metadata rather than trusted path components.',B('Concurrency and synchronization'),'Database transactions protect individual writes. Per-record threading locks protect local index operations. In-process extraction jobs are not durable. Multi-process locks, cancellation/versioning and concurrent source mutation require further work. Use a single-process synthetic demo.',B('Error handling and logging'),'AppError carries public HTTP errors. Pydantic validates requests and outputs. Provider timeouts and unavailable services fail explicitly. No durable audit-event store exists. Logs must not be treated as a privacy-safe production audit trail.'],
'5.1':['SQLAlchemy defines six metadata entities. Ownership foreign keys exist on records and derived entities. Source text remains linked to its originating document and page. Figures and the data dictionary below describe the current schema rather than a proposed replacement.'],
'5.1.1':[I('er','Figure 4: Entity relationship diagram'), 'Each User owns many PatientRecords. A record contains many Documents, ExtractedPages, Chunks and Summaries. Each page and chunk references one source document. UUID keys are opaque identifiers, not access credentials.'],
'5.1.2':[],
'5.2':[I('components','Figure 5: Service interfaces and domain components'),T(['Component','Responsibility','Key functions'],[['Auth / records','Identity and owned containers','register_account, login, get_owned_record'],['Ingestion','Validate and protect originals','upload_document, get_owned_document'],['Extraction','Page text and OCR','extract_document, list_extracted_pages'],['Retrieval','Chunk and search','index_owned_record, retrieve_for_record'],['Summarization','Generate and validate citations','generate_record_summary, _parse_and_validate'],['Summary lifecycle','Prevent stale stored snapshots','invalidate_summaries']])],
'5.3':['The following views describe data movement, request order, source lifecycle and the reviewer workflow. They complement the structural views in Section 3.'],
'5.3.1':[I('context','Figure 6: DFD Level 0 system context'),'The external reviewer submits credentials and files and receives processing results and summaries. The evaluator receives experimental logs.',I('dfd','Figure 7: DFD Level 1 document and summary processing'),'Processes validate sources, extract pages, index chunks, retrieve text and persist a validated summary. Stores distinguish metadata, source bytes and vector mappings.'],
'5.3.2':[],
'5.3.3':[I('states','Figure 11: Document state transitions'),'An accepted source starts uploaded. Extraction enters processing, then extracted or failed. Successful indexing normally marks it indexed. The schema also defines ready for future compatibility. Deletion hides metadata and removes bytes and derived page/chunk data. Re-extraction invalidates stored summaries before processing.'],
'5.3.4':[I('activity','Figure 12: Reviewer activity workflow'),'A reviewer checks extracted text before requesting generation, follows citations and decides whether to export. Failure branches return to source review or retry rather than producing a silent substitute.'],
'5.4':[B('Extraction and chunking'),'Native PDF pages with at least 40 non-whitespace characters use extracted text. Sparse pages render at 200 DPI for OCR. The pipeline does not silently correct clinical strings. Text chunks default to 800 characters with 120-character overlap, remain within pages and use deterministic IDs derived from document/page/offsets.',B('Retrieval'),'hashed-token-v1 maps normalized tokens into 256 dimensions with signed hashing and normalization. It is a lexical baseline, not a biomedical encoder. The runtime retrieves up to four chunks for each of five fixed section queries, deduplicates IDs, and passes passage text to the generator. NumPy exact cosine search runs within one authorized record.',B('Generation and validation'),'The versioned prompt requests fixed JSON sections and treats source content as data. Mock generation exercises structure only. The compatible provider uses temperature 0 and configured token/time limits. Pydantic parses output; unknown source IDs are removed; uncited claims move to unresolved information. Valid source IDs do not establish clinical entailment.',B('Evaluation'),'The script uses the same chunker and embedding provider for section-query retrieval, then compares retrieved context with concatenated full extracted text. Both conditions use the same provider and prompt schema. It records context size and durations. Image fixtures use labeled companion transcripts, so this is not an OCR benchmark. ROUGE [3], lexical fact coverage and citation-ID metrics complement future manual unsupported-claim review. Mock and malformed output are non-reportable. Section 7 states remaining verification.'],
'5.5':['SRS Section 3 defines the external interface requirements. The following views specify navigation, major screens, API contracts and failure messages.'],
'5.5.1':[I('navigation','Figure 13: Navigation between main screens'),I('wireframe','Figure 14: Record review wireframe'),'The wireframe is a design schematic, not a captured browser screenshot. Login/register lead to Records. Records supports create, search and sort. Record detail offers source upload, extraction review and a Summary and evidence tab. Citation selection highlights an excerpt; Open source page opens the matching extracted page. Text/JSON exports include provider metadata and mock labels. Demo guide and System status support demonstration recovery. Responsive composition uses a top navigation strip on narrow screens.'],
'5.5.2':[T(['Method','Endpoint','Input','Output / errors','Auth'],[['POST','/api/v1/auth/register','email, password','token and user / 422, 409','No'],['POST','/api/v1/auth/login','email, password','token and user / 401','No'],['GET / POST','/api/v1/records','label for POST','owned records / 401','Yes'],['GET / DELETE','/api/v1/records/{r}','record UUID','record or 204 / 404','Yes'],['GET / POST','/api/v1/records/{r}/documents','multipart on POST','document metadata / 400, 413','Yes'],['GET','.../documents/{d}/file','document UUID','original bytes / 404','Yes'],['POST','.../documents/{d}/extract','document UUID','page text / 400, 404','Yes'],['GET','.../documents/{d}/extracted','document UUID','page text / 404','Yes'],['DELETE','.../documents/{d}','document UUID','204 / 404','Yes'],['GET / POST','/api/v1/records/{r}/summary','record UUID','summary / 404, 502, 503, 504','Yes'],['GET','/api/v1/health, /ready, /generation','none','service and provider state','No']])],
'5.6':['Passwords use bcrypt and sessions use JWT bearer tokens stored in browser sessionStorage. This exposes tokens to script execution if XSS occurs; httpOnly cookies and CSRF protections are future design work. Server-side record ownership gates every source and summary operation, including retrieval. Invalid sources and excessive file sizes fail validation. Files live outside the web root. CORS uses an origin allowlist; secrets live in ignored environment configuration.','Uploading, re-extracting or deleting a source removes stored summary snapshots. Document deletion also removes extracted pages and chunk rows. Record deletion removes associated data and files. The prototype does not provide encrypted storage, production TLS, roles, audit logs, secure erasure guarantees or a compliance certification. Concurrent mutation during generation still needs versioning and transaction design in FYP II.'],
'6.':[T(['SRS requirement','Use case','Design element','Section','Test'],[[r[0],r[2],'Record/processing service or React view',r[3],r[4]] for r in FR]+[[r[0],r[3],'Client/provider/persistence boundary',r[4],r[5]] for r in NFR])],
'7.':['Provider abstractions and isolated test storage support deterministic tests without patient data or a model download. Backend tests cover authorization, validation, extraction, indexing, summary validation and invalidation. Frontend tests check disclaimer/provider labeling, citation navigation and batch retry behavior. A mock dry run verifies output files and reporting quarantine.','FYP II verification must add real-model failure tests, concurrent mutations, semantic retrieval quality, fixed held-out comparative generation, human entailment review, browser file upload/download flows, keyboard/mobile review, PostgreSQL integration, backup recovery and production access controls. No mock injection test establishes robustness against a real adversarial language-model prompt.'],
'References':REFERENCES,
'Appendices':[B('Appendix A Configuration and reproducibility'),'See .env.example for public configuration names. Secrets and real runtime data do not belong in the submission archive. The demonstration uses the default lexical embedding and mock provider. Record selected model license, memory requirement and checkpoint before real inference.',B('Appendix B Design limitations'),'Processing is synchronous or in-process. Large records may exceed prompt budget. Lexical hash collisions and character chunking limit retrieval. Date/clinical-field normalization and clinical document classification remain incomplete. The harness lacks live OCR and independent clinical reviewers.']
}
for fig_no,uc in enumerate([UCS[0],UCS[2],UCS[4]],start=8):
 name={'UC-USER-01':'sequence_login','UC-USER-03':'sequence_upload','UC-USER-05':'sequence_summary'}[uc[0]]
 SDS['5.3.2'] += [I(name,f'Figure {fig_no}: Sequence diagram for {uc[1].lower()}'),uc[6]+' Exceptions: '+uc[7]]
REPORT={
'Acknowledgements':['We acknowledge the guidance of '+SUP+' and the academic review process of FAST NUCES Karachi. We also acknowledge the authors and maintainers of the research and open-source tools cited in this report. This acknowledgement does not imply that a clinician or hospital has validated the prototype.'],
'Abstract':[ABSTRACT,'Keywords: clinical documents, retrieval augmented generation, source traceability, optical character recognition, synthetic data'],
'List of Abbreviations':[T(['Abbreviation','Full form'],ABBR)],
'1.':['This chapter defines the project problem, objectives and delivery boundary. MediSummarize AI is an academic research prototype for organizing fictional clinical documents. The project requires a reviewer to check source passages before relying on a summary.'],
'1.1':['Laboratory reports, prescriptions and discharge notes can arrive as heterogeneous files. The supplied proposal identifies the burden of reviewing these records and the risk of unsupported model output [4]. Retrieval-augmented generation supplies external passages to a generator [1], motivating a prototype that keeps provenance visible throughout review.'],
'1.2':['The project addresses the gap between storing clinical documents and presenting a concise, inspectable account of their content. A useful prototype must process scans, preserve page provenance, keep records isolated and expose absent information. A summary with a valid citation ID still requires a reviewer to determine whether the passage supports its wording.'],
'1.3':['The project objectives are: process sample PDF/image/text files into reviewable pages; retrieve within an authorized record; produce fixed summary sections with source references or explicit unavailable information; protect record access; and compare a real model with and without retrieval on fixed synthetic cases. The final objective remains outstanding in this environment.'],
'1.4':['FYP I covers the protected proof of concept, requirements/design artifacts, synthetic dataset and initial evaluation procedure. Current generation is mock, current embeddings are lexical hashing, and the vector backend is exact NumPy cosine search.','FYP II covers real-model experiments and optional adaptation, semantic retrieval, expanded evaluation, role-based authorization, audit events, encryption and deployment. The prototype excludes diagnosis, prescriptions, identifiable patient records and hospital integration.'],
'1.5':['Chapter 2 reviews relevant approaches. Chapter 3 explains methodology and feasibility. Chapters 4 and 5 summarize the companion SRS and SDS. Chapter 6 reports implementation and test evidence. Chapter 7 describes the project plan and risks. Chapter 8 states the conclusion and future work.'],
'2.':['The literature review starts with the proposal references and checks primary research pages for retrieval augmentation, clinical encoders and summary evaluation. Search terms included retrieval augmented generation, clinical BERT embeddings and ROUGE. This is a focused feasibility review rather than a systematic review. The committee minimum paper count has not been supplied.'],
'2.1':['Retrieval and generation: Lewis et al. combine a generator with retrieved external information [1]. That work motivates providing passages rather than expecting all facts to reside in model parameters. Its findings do not establish performance for this project or synthetic clinical records.','Clinical representation: Alsentzer et al. release clinical BERT representations and evaluate them on clinical NLP tasks [2]. A clinical encoder is a candidate for later comparison. It is not currently installed or used in the default lexical index, and encoder quality for one task does not establish summarization safety.','Summary evaluation: ROUGE measures overlap with a reference summary [3]. This project implements token-overlap measures, lexical fact coverage and citation-ID metrics, then plans claim-level human review. Word overlap and a valid source reference do not establish medical correctness or entailment.'],
'2.2':[T(['Approach','Method','Strength','Limitation','Project relevance'],[['RAG [1]','Retrieve external passages','Provides explicit context','Task/domain transfer needs testing','Basis for retrieved condition'],['Clinical BERT [2]','Clinical contextual encoder','Domain representation research','Not a full summary workflow','Future encoder comparison'],['ROUGE [3]','Reference overlap','Reproducible comparison','Cannot establish factual support','Automatic metric component'],['MediSummarize AI','Owned sources and evidence review','Inspectable end-to-end prototype','Mock generator and small fictional set','Current proof of concept']])],
'2.3':['The project contribution is an inspectable implementation and evaluation procedure that combine ingestion, record isolation and source-linked review. It does not claim a new model architecture or an experimentally established advantage. Whether retrieval improves completeness and faithfulness remains a hypothesis for a real-model baseline assessment.'],
'3.1':['Figure 1 shows the intended document workflow. The reviewer uploads fictional records, checks extracted pages and inspects a structured summary with citations. The current mock generator exercises this workflow without asserting clinical facts.',I('pipeline','Figure 1: High level prototype workflow')],
'3.2':['Development follows short increments: validate uploads, preserve pages, test chunking and ownership, add generation schemas, then complete reviewer flows. Each increment has automated checks and explicit limitations. The synthetic manifest fixes development and held-out labels before experiments.','The corrected evaluation condition chunks each case, embeds passages, retrieves up to four chunks for each summary-section query and deduplicates the passages. The baseline supplies the full concatenated extracted text to the same provider and prompt schema. Context length and durations are recorded. Small cases can retrieve nearly all source material, so the pilot cannot demonstrate retrieval benefit without a larger and carefully controlled set.'],
'3.3':[T(['Layer / purpose','Technology','Justification'],STACK)],
'3.4':[B('Technical feasibility'),'The document and review workflow runs on the local Python/Node environment. SQLite and lexical hashing allow an offline prototype. Real-model feasibility still depends on selected weights, memory and inference capacity.',B('Operational feasibility'),'The interface offers familiar upload and record review steps. No clinician usability study has been performed, so acceptance by practitioners remains unproven.',B('Economic feasibility'),'The current demo requires no paid model API. Hardware, hosting and model-license costs have not been quoted. GPU experiments should use approved university or other available compute and record actual costs and licenses.'],
'4.':['The complete requirements appear in SRS release 1.0. The following subset summarizes the prototype functions and quality constraints without repeating all use-case detail.'],
'4.1':[T(['ID','Requirement','Priority'],[[r[0],r[1],'Must'] for r in FR if r[0] in {'FR-001','FR-003','FR-005','FR-007','FR-010','FR-011','FR-012','FR-014','FR-015'}])],
'4.2':[T(['ID','Requirement','Category'],[[r[0],r[2],r[1]] for r in NFR if r[0] in {'NFR-002','NFR-003','NFR-004','NFR-005','NFR-007','NFR-009'}])],
'4.3':[I('usecases','Figure 2: Reviewer and evaluator use cases'),'The research reviewer controls the document workflow. The evaluator runs the offline comparison. No administrator role or autonomous clinical decision actor exists in the current implementation.'],
'5.':['The SDS provides full design detail. This chapter summarizes the implemented architecture, persistence model and reviewer interface. Planned services remain visibly distinguished from verified runtime components.'],
'5.1':[I('architecture','Figure 3: Prototype system architecture'),'React calls authenticated FastAPI routes. Services validate sources, extract pages, build isolated indexes and validate generated JSON. SQLite stores metadata, while protected files and NumPy indexes live outside the frontend. The compatible inference adapter is implemented but a real local language model has not been verified.'],
'5.2':[I('er','Figure 4: Metadata entity relationship diagram'),'The database contains users, patient_records, documents, extracted_pages, chunks and summaries. UUID ownership and provenance links connect each derived artifact to its owner and source. Alembic migrations currently end at 0006_summaries.'],
'5.3':[I('sequence_summary','Figure 5: Summary request sequence'),'The service authorizes ownership before retrieval, constructs the prompt from source text, validates provider output and stores provider metadata. Source upload, re-extraction and deletion invalidate earlier snapshots. Per-record locks do not yet coordinate distributed workers.'],
'5.4':[I('wireframe','Figure 6: Reviewer interface wireframe'),'The figure is a schematic of the implemented screen organization rather than a captured screenshot. Records provides create/search/sort. Record detail separates documents from summary and evidence. Citation selection highlights an excerpt; a second action opens its source page. The interface provides batch upload retry, export, loading/error/empty states and guidance. Desktop/mobile browser verification remains outstanding because the available browser-control session timed out.'],
'6.':['Only observed implementation and executed checks support this chapter. Existing code and test files provide the technical evidence [5]. Mock generation establishes integration behavior rather than model quality.'],
'6.1':[T(['Module','Current implementation','Verification boundary'],[['Identity and ownership','bcrypt/JWT and owner-scoped APIs','Automated authorization tests'],['Ingestion','PDF, image and text validation/protected files','Content and isolation checks'],['Extraction','Page-aware native text and Tesseract OCR','Synthetic extraction tests'],['Retrieval','800/120 character chunks, lexical hashing, exact cosine','Chunking/index/isolation checks'],['Generation','Mock plus compatible adapter; fixed JSON and source validation','Mock verified, real model pending'],['Frontend','Record workspace, source/summary tabs, export and guide','Component tests and build; browser check pending'],['Source lifecycle','Invalidate summaries when documents change','Regression test'],['Evaluation','Actual chunk retrieval versus full text','18 mock rows quarantined']])],
'6.2':['The current verification record reports 60 passing backend tests and 9 passing frontend tests, with a successful production frontend build. A mock evaluation dry run produced 18 condition rows across nine manifest entries and zero reportable rows. This is evidence that the harness runs and enforces quarantine.','Real-model ROUGE, factual coverage, retrieval quality, unsupported-claim rate and clinician usability results are not available. No improvement over a non-retrieval model is claimed. Image cases in the harness use companion text, so the experiment does not measure OCR quality. Date normalization, clinical document classification and a medical embedding model remain gaps against the broader proposed design.'],
'6.3':[T(['Test ID','Requirement / feature','Approach','Phase'],[['TC-001/002','Account and session','Backend positive/negative auth tests','FYP I executed'],['TC-005/007','Upload and extraction','Synthetic text/PDF/image cases','FYP I executed'],['TC-009/010','Chunking and isolation','Index and cross-account checks','FYP I executed'],['TC-012/014','Citations and stale snapshots','Citation and lifecycle regression','FYP I executed'],['TC-015/018','Evaluation protocol','Mock dry run then real-model paired run','Dry run done; real run pending'],['TC-025','Usability and responsive behavior','Desktop/mobile, keyboard, upload/export walkthrough','Pending manual verification'],['FYP II extension','Security and deployment','Load, concurrency, backups, roles and TLS','Planned']])],
'7.1':['The original proposal allocates 16 weeks to feasibility and defense preparation [4]. The timeline below preserves that plan as a target sequence rather than fabricated actual completion dates. Source and verification evidence establish current implementation status.',T(['Phase','Original window','Work package','Current status'],[['FYP I','Weeks 1-4','Literature, requirements, proposal','Documentation prepared for review'],['FYP I','Weeks 5-7','Ingestion, OCR and API','Prototype implemented'],['FYP I','Weeks 8-10','Chunking and retrieval','Lexical baseline implemented'],['FYP I','Weeks 11-12','UI and baseline assessment','UI implemented; real assessment pending'],['FYP I','Weeks 13-16','Demo, report and defense','Package prepared; supervisor review pending'],['FYP II','Proposed weeks 1-4','Semantic retrieval and real-model benchmark','Planned'],['FYP II','Proposed weeks 5-10','Optional adaptation, roles and audit','Planned'],['FYP II','Proposed weeks 11-16','Full evaluation and hardened deployment','Planned']]),I('timeline','Figure 7: Planned FYP I and FYP II work windows')],
'7.2':[T(['Member','Student ID','Primary responsibility'],TEAM_ROWS),'All members share requirements review, demo preparation and integration. These responsibilities follow the supplied proposal; they are not claims about individual authorship of every repository change.'],
'7.3':[T(['Risk','Likelihood','Impact','Mitigation'],RISKS)],
'7.4':['First complete the outstanding FYP I real-model pilot and manual demo check. Then establish a larger fixed dataset, compare semantic embedding candidates, define retrieval metrics and collect independent claim-support review. Add adaptation experiments only after a reproducible baseline.','Harden storage and transport, define least-privilege roles and durable audit events, introduce job/version concurrency controls, validate PostgreSQL and backup recovery, and complete deployment documentation. The roadmap does not require hospital integration or a regulatory compliance claim.'],
'8.1':['MediSummarize AI demonstrates an owned-document workflow with extraction, lexical retrieval and source-linked structured output in mock mode. The frontend and documentation make the prototype reviewable. Automated checks support application behavior, while real-model comparative findings remain outstanding. The project therefore establishes technical feasibility of the workflow without closing its research hypothesis.'],
'8.2':['Complete real-model baseline comparison and manual browser verification before declaring all FYP I acceptance criteria satisfied. Future work should measure semantic retrieval, unsupported claims, missing-data handling and OCR effects separately. FYP II should add stronger security, concurrency controls and broader human evaluation.'],
'References':REFERENCES,
'Appendices':[B('Appendix A Synthetic dataset'),T(['Case','Split','Purpose','Upload files'],DATA_ROWS),B('Appendix B Reproduction'),'README.md and docs/demo-script.md provide setup and walkthrough commands. scripts/evaluate.py writes labeled JSON and CSV. docs/fyp-i/submission-checklist.md records open acceptance items.',B('Appendix C Academic review'),'Supervisor review, approval signatures, student declaration signatures and institutional similarity checking remain pending. This generated package does not assert their completion.']
}
def font(size=30,bold=False):
 return ImageFont.truetype('C:/Windows/Fonts/arial'+('bd' if bold else '')+'.ttf',size)
def lines(draw,text,maxw,f):
 result=[]
 for raw in text.split('\n'):
  current=''
  for word in raw.split():
   if current and draw.textlength(current+' '+word,font=f)>maxw:result.append(current);current=word
   else:current=(current+' '+word).strip()
  result.append(current)
 return result
def text_center(draw,box,text,size=29,bold=False):
 f=font(size,bold); a,b,c,d=box; ls=lines(draw,text,c-a-24,f); lh=size+9;y=(b+d-len(ls)*lh)/2
 for line in ls:
  w=draw.textlength(line,font=f);draw.text(((a+c-w)/2,y),line,font=f,fill='#172a26');y+=lh
def arrow(draw,a,b,label=''):
 draw.line([a,b],fill='#416057',width=3);ang=math.atan2(b[1]-a[1],b[0]-a[0]); l=15
 draw.polygon([b,(b[0]-l*math.cos(ang-.5),b[1]-l*math.sin(ang-.5)),(b[0]-l*math.cos(ang+.5),b[1]-l*math.sin(ang+.5))],fill='#416057')
 if label:
  x=(a[0]+b[0])/2;y=(a[1]+b[1])/2;f=font(23);w=draw.textlength(label,font=f);draw.rectangle((x-w/2-6,y-18,x+w/2+6,y+18),fill='white');draw.text((x-w/2,y-14),label,font=f,fill='#304e44')
def graph(name,nodes,edges,w=1700,h=850):
 im=Image.new('RGB',(w,h),'white');dr=ImageDraw.Draw(im)
 for a,b,label in edges:
  A=nodes[a][1];B_=nodes[b][1]; ac=((A[0]+A[2])/2,(A[1]+A[3])/2);bc=((B_[0]+B_[2])/2,(B_[1]+B_[3])/2)
  if abs(ac[0]-bc[0])>abs(ac[1]-bc[1]):
   start=(A[2] if bc[0]>ac[0] else A[0],ac[1]);end=(B_[0] if bc[0]>ac[0] else B_[2],bc[1])
  else:start=(ac[0],A[3] if bc[1]>ac[1] else A[1]);end=(bc[0],B_[1] if bc[1]>ac[1] else B_[3])
  arrow(dr,start,end,label)
 for key,(text,box,*kind) in nodes.items():
  if kind and kind[0]=='oval':dr.ellipse(box,fill='#f1f6f2',outline='#46665a',width=3)
  else:dr.rectangle(box,fill='#f1f6f2',outline='#46665a',width=3)
  text_center(dr,box,text,30,False)
 im.save(FIG/(name+'.png'))
 (FIG/(name+'.json')).write_text(json.dumps({'nodes':nodes,'edges':edges},indent=2),encoding='utf-8')
def sequence(name,labels,messages):
 w=1700;h=120+len(messages)*105; im=Image.new('RGB',(w,h+80),'white');d=ImageDraw.Draw(im);xs=[130+i*(1440/(len(labels)-1)) for i in range(len(labels))]
 for x,label in zip(xs,labels):
  d.rectangle((x-120,15,x+120,95),fill='#edf3ee',outline='#46665a',width=3);text_center(d,(x-120,15,x+120,95),label,27,True)
  for y in range(110,h,18):d.line((x,y,x,y+9),fill='#82958a',width=2)
 for i,(a,b,label) in enumerate(messages):
  y=160+i*105;arrow(d,(xs[a],y),(xs[b],y));f=font(25);tw=d.textlength(label,font=f);x=(xs[a]+xs[b]-tw)/2;d.rectangle((x-6,y-43,x+tw+6,y-10),fill='white');d.text((x,y-42),label,font=f,fill='#203c30')
 im.save(FIG/(name+'.png'))
 (FIG/(name+'.json')).write_text(json.dumps({'lifelines':labels,'messages':messages},indent=2),encoding='utf-8')
def make_figures():
 graph('pipeline',{'a':('Upload sources',(50,70,500,270)),'b':('Extract / OCR\nPreserve page provenance',(625,70,1075,270)),'c':('Chunk and index\nOwned record only',(1200,70,1650,270)),'d':('Retrieve section passages',(1200,510,1650,710)),'e':('Generate and validate JSON\nMock by default',(625,510,1075,710)),'f':('Reviewer checks citations\nExport research output',(50,510,500,710))},[('a','b',''),('b','c',''),('c','d',''),('d','e',''),('e','f','')])
 graph('context',{'u':('Research reviewer\ncredentials / synthetic files',(40,100,450,330)),'s':('MediSummarize AI\nowned document workflow',(650,100,1090,330)),'g':('Generation provider\nmock or configured LLM',(1280,100,1660,330)),'e':('Evaluator\nrun configuration',(40,580,450,780)),'d':('Local stores\nmetadata / sources / vectors',(650,580,1090,780)),'r':('Evaluation log\nJSON and CSV',(1280,580,1660,780))},[('u','s','request / review'),('s','g','prompt text'),('s','d','owned data'),('e','s','evaluate'),('s','r','results')])
 graph('architecture',{'a':('React browser client\nrecords / sources / evidence',(50,60,500,280)),'b':('FastAPI / Pydantic\nJWT and ownership',(625,60,1075,280)),'c':('Processing services\nvalidate / OCR / retrieve',(1200,60,1650,280)),'d':('SQLAlchemy metadata\nSQLite now, PostgreSQL planned',(50,560,500,790)),'e':('Protected source files\nNumPy record indexes',(625,560,1075,790)),'f':('GenerationProvider\nmock / compatible local server',(1200,560,1650,790))},[('a','b','/api/v1'),('b','c','orchestrate'),('b','d','persist'),('c','e','sources / vectors'),('c','f','passage text')])
 graph('layers',{'a':('Presentation\nReact pages and components',(250,30,1450,165)),'b':('HTTP boundary\nFastAPI routes / auth dependencies / Pydantic',(250,235,1450,370)),'c':('Application services\ningestion / extraction / retrieval / summarization',(250,440,1450,575)),'d':('Persistence and providers\nSQLAlchemy / files / vectors / embeddings / generation',(250,645,1450,800))},[('a','b',''),('b','c',''),('c','d','')])
 graph('deployment',{'a':('Browser\nhttp://localhost:5173',(50,80,500,300)),'b':('Local Vite dev server\n/api proxy to :8000',(625,80,1075,300)),'c':('Local FastAPI process\n127.0.0.1:8000',(1200,80,1650,300)),'d':('Development machine\nSQLite + protected storage',(1200,550,1650,780)),'e':('Optional inference service\n127.0.0.1:11434/v1\nNot currently verified',(625,550,1075,780))},[('a','b','HTTP'),('b','c','HTTP'),('c','d','local I/O'),('c','e','JSON')])
 graph('er',{'u':('users\nPK id\nemail UNIQUE / password_hash',(40,50,500,300)),'r':('patient_records\nPK id / FK owner_id\ndisplay_label',(620,50,1080,300)),'s':('summaries\nPK id / FK owner_id, record_id\nsummary_json / evidence_json\nprovider / model / is_mock',(1200,50,1660,300)),'d':('documents\nPK id / FK owner_id, record_id\nfilename / kind / status',(620,550,1080,800)),'p':('extracted_pages\nPK id / FK document_id\npage / text / method',(40,550,500,800)),'c':('chunks\nPK id / FK document_id\npage / offsets / text',(1200,550,1660,800))},[('u','r','1 to many'),('r','s','1 to many'),('r','d','1 to many'),('d','p','1 to many'),('d','c','1 to many')])
 graph('components',{'a':('Auth / records\nget_owned_record()',(40,60,500,280)),'b':('Ingestion / extraction\nupload_document()\nextract_document()',(620,60,1080,280)),'c':('Retrieval\nindex_owned_record()\nretrieve_for_record()',(1200,60,1660,280)),'d':('Summary lifecycle\ninvalidate_summaries()',(40,560,500,780)),'e':('Summarization\ngenerate_record_summary()\n_parse_and_validate()',(620,560,1080,780)),'f':('Provider interfaces\nembed() / generate()',(1200,560,1660,780))},[('a','b','authorize'),('b','c','index'),('b','d','source change'),('c','e','evidence'),('e','f','generate')])
 graph('dfd',{'a':('Reviewer\nupload / review request',(40,60,480,270)),'b':('P1 Validate and store\nD1 originals + metadata',(630,60,1070,270)),'c':('P2 Extract and chunk\nD2 page and chunk rows',(1220,60,1660,270)),'d':('P3 Embed and retrieve\nD3 record vectors',(1220,560,1660,780)),'e':('P4 Generate and validate\nD4 summary snapshot',(630,560,1070,780)),'f':('Reviewer\nclaim and source review',(40,560,480,780))},[('a','b','files'),('b','c','validated bytes'),('c','d','text chunks'),('d','e','passages'),('e','f','summary + evidence')])
 graph('states',{'a':('uploaded',(50,80,450,240),'oval'),'b':('processing',(650,80,1050,240),'oval'),'c':('extracted',(1250,80,1650,240),'oval'),'d':('indexed',(1250,580,1650,740),'oval'),'e':('failed',(650,580,1050,740),'oval'),'f':('deleted',(50,580,450,740),'oval')},[('a','b','extract'),('b','c','text found'),('c','d','index'),('b','e','failure'),('e','b','retry'),('a','f','delete'),('e','f','delete')])
 graph('activity',{'a':('Create fictional case',(50,70,480,240),'oval'),'b':('Upload and validate sources',(630,70,1070,240)),'c':('Extract / inspect text',(1220,70,1650,240)),'d':('Generate summary\nexplicit error on failure',(1220,580,1650,780)),'e':('Check claim and source\nrecord unavailable information',(630,580,1070,780)),'f':('Export labeled research result',(50,580,480,780),'oval')},[('a','b',''),('b','c','accepted'),('c','d','reviewed'),('d','e','valid JSON'),('e','f','review complete')])
 graph('navigation',{'a':('Login / register',(50,70,480,250)),'b':('Records\ncreate / search / sort',(630,70,1070,250)),'c':('Record detail\nDocuments tab',(1220,70,1650,250)),'d':('Summary and evidence\ncitation / source page',(1220,580,1650,780)),'e':('Demo guide',(630,580,1070,780)),'f':('System status',(50,580,480,780))},[('a','b','session'),('b','c','open case'),('c','d','generate'),('b','e','navigation'),('b','f','navigation')])
 graph('wireframe',{'n':('Navigation\nRecords\nDemo guide\nSystem status\nSign out',(40,40,365,810)),'h':('Case label and date                              Generate summary',(410,40,1650,160)),'t':('Add documents      /      Review text      /      Verify summary',(410,205,1650,330)),'s':('Documents tab\nUpload files\nOriginal / Extract / Review',(410,390,985,810)),'e':('Summary and evidence tab\nFixed summary sections\nCitation passage and source page\nExport text / JSON',(1040,390,1650,810))},[])
 sequence('sequence_login',['Reviewer','React','Auth API','Database'],[(0,1,'submit(email, password)'),(1,2,'POST /auth/login'),(2,3,'lookup email / bcrypt verify'),(3,2,'user identity'),(2,1,'JWT + public user'),(1,0,'open owned Records')])
 sequence('sequence_upload',['Reviewer','API','Validation / OCR','Stores'],[(0,1,'POST documents(file)'),(1,2,'check kind / limits'),(2,3,'store protected original + metadata'),(1,2,'extract_document(id)'),(2,3,'pages + chunks + vectors'),(1,0,'metadata / text status')])
 sequence('sequence_summary',['Reviewer','API','Retrieval','Provider / DB'],[(0,1,'POST record summary'),(1,2,'authorize / retrieve(section queries)'),(2,1,'passage text + source IDs'),(1,3,'generate(system, user prompt)'),(3,1,'structured JSON text'),(1,3,'validate IDs / persist snapshot'),(1,0,'summary + evidence + mock flag')])
 # Use-case view uses UML-style ellipses within the system boundary.
 im=Image.new('RGB',(1700,1100),'white');d=ImageDraw.Draw(im);d.rectangle((400,30,1670,1060),outline='#46665a',width=3);d.text((435,50),'MediSummarize AI',font=font(31,True),fill='#172a26')
 d.ellipse((125,340,185,400),outline='#172a26',width=4);d.line((155,400,155,550,100,640),fill='#172a26',width=4);d.line((155,550,210,640),fill='#172a26',width=4);d.line((90,455,220,455),fill='#172a26',width=4);text_center(d,(25,665,325,765),'Research reviewer',28)
 for i,uc in enumerate(UCS):
  col=i%2;row=i//2;box=(460+col*610,140+row*220,1000+col*610,300+row*220);d.ellipse(box,fill='#f1f6f2',outline='#46665a',width=3);text_center(d,box,uc[0]+'\n'+uc[1],27)
  if i<7:d.line((220,455,box[0],(box[1]+box[3])/2),fill='#9baba1',width=2)
 d.text((480,1020),'UC-EVAL-01 actor: evaluator / developer',font=font(25),fill='#324e42');im.save(FIG/'usecases.png')
 # Timeline visual distinguishes proposal work windows from observations.
 im=Image.new('RGB',(1700,880),'white');d=ImageDraw.Draw(im)
 labels=['Planning and requirements','Ingestion and OCR','Retrieval prototype','Frontend and initial assessment','Demo and documentation','FYP II expanded evaluation']
 windows=[(0,1),(1,2),(1,3),(2,4),(3,4),(4,5)]
 for i,txt in enumerate(['I W1-4','I W5-8','I W9-12','I W13-16','II W1-16']):text_center(d,(600+i*210,30,800+i*210,120),txt,26,True)
 for i,(label,(a,b)) in enumerate(zip(labels,windows)):
  y=150+i*105;d.text((25,y+15),label,font=font(29),fill='#172a26')
  for j in range(5):d.rectangle((600+j*210,y,800+j*210,y+65),fill='#e1ebe3' if a<=j<b else '#f8faf8',outline='#9daf9f',width=2)
 d.text((30,815),'Planned windows from proposal; bars do not assert actual completion dates.',font=font(26),fill='#324e42');im.save(FIG/'timeline.png')
def add_paragraph(doc,text,style=None):
 p=doc.add_paragraph(text,style=style)
 p.paragraph_format.widow_control=True
 return p._p
def add_table(doc,headers,rows,prototype):
 # Clone an actual source table, then rebuild its rows while preserving its table properties.
 tbl=deepcopy(prototype)
 for c in list(tbl):
  if c.tag in {qn('w:tr'),qn('w:tblGrid')}:tbl.remove(c)
 grid=OxmlElement('w:tblGrid')
 total=9020; n=len(headers)
 if n==2: widths=[int(total*.29),int(total*.71)]
 elif n==3 and headers[0] in {'ID','Req. ID'}: widths=[1000,6200,1820]
 elif n==4 and headers[0]=='ID':widths=[1100,4600,2220,1100]
 elif n==4:widths=[1700,2200,2320,2800]
 elif n==5 and headers[0]=='ID':widths=[1100,3650,1050,1400,1820]
 elif n==5 and headers[0]=='Column':widths=[2000,1600,900,1700,2820]
 elif n==6:widths=[1100,1250,1000,2300,2300,1070]
 elif n>=5:widths=[1350]+[int((total-1350)/(n-1))]*(n-1)
 else:widths=[int(total/n)]*n
 for width in widths:
  gc=OxmlElement('w:gridCol');gc.set(qn('w:w'),str(width));grid.append(gc)
 tbl.insert(1,grid)
 for ri,row in enumerate([headers]+rows):
  tr=OxmlElement('w:tr');pr=OxmlElement('w:trPr')
  if ri==0:pr.append(OxmlElement('w:tblHeader'))
  # Do not split short matrix rows over page boundaries.
  pr.append(OxmlElement('w:cantSplit'));tr.append(pr)
  for ci,value in enumerate(row):
   tc=OxmlElement('w:tc');tcPr=OxmlElement('w:tcPr');ww=OxmlElement('w:tcW');ww.set(qn('w:w'),str(widths[min(ci,n-1)]));ww.set(qn('w:type'),'dxa');tcPr.append(ww)
   shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E5EBE7' if ri==0 else ('F7F9F7' if ri%2==0 else 'FFFFFF'));tcPr.append(shade)
   tc.append(tcPr);p=OxmlElement('w:p');pp=OxmlElement('w:pPr');spacing=OxmlElement('w:spacing');spacing.set(qn('w:after'),'80');spacing.set(qn('w:before'),'80');spacing.set(qn('w:line'),'240');spacing.set(qn('w:lineRule'),'auto');pp.append(spacing);p.append(pp)
   run=OxmlElement('w:r');rp=OxmlElement('w:rPr');size=OxmlElement('w:sz');size.set(qn('w:val'),'20');rp.append(size)
   if ri==0:rp.append(OxmlElement('w:b'))
   color=OxmlElement('w:color');color.set(qn('w:val'),'000000');rp.append(color);run.append(rp)
   parts=str(value).split('\n')
   for k,part in enumerate(parts):
    if k:run.append(OxmlElement('w:br'))
    tt=OxmlElement('w:t');tt.text=part;run.append(tt)
   p.append(run);tc.append(p);tr.append(tc)
  tbl.append(tr)
 # Use explicit, quiet borders and padding, source-derived geometry.
 pr=tbl.find(qn('w:tblPr'))
 for name in ['tblBorders','tblCellMar','tblW']:
  old=pr.find(qn('w:'+name))
  if old is not None:pr.remove(old)
 borders=OxmlElement('w:tblBorders')
 for side in ['top','left','bottom','right','insideH','insideV']:
  b=OxmlElement('w:'+side);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'D9D9D9');borders.append(b)
 pr.append(borders);m=OxmlElement('w:tblCellMar')
 for side in ['top','left','bottom','right']:
  x=OxmlElement('w:'+side);x.set(qn('w:w'),'90');x.set(qn('w:type'),'dxa');m.append(x)
 pr.append(m);tw=OxmlElement('w:tblW');tw.set(qn('w:w'),str(total));tw.set(qn('w:type'),'dxa');pr.append(tw)
 return tbl
def render_items(doc,items,prototype,captions):
 result=[]
 subject=captions.get('section','Project details')
 for item in items:
  if isinstance(item,str):
   el=add_paragraph(doc,item)
   if captions.get('kind')=='Final_Report':
    from docx.text.paragraph import Paragraph
    p=Paragraph(el,doc._body);p.paragraph_format.line_spacing=1.5;p.paragraph_format.space_after=Pt(6);p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    for r in p.runs:r.font.size=Pt(12)
   result.append(el)
  elif item[0]=='sub':
   subject=item[1]
   p=doc.add_paragraph();r=p.add_run(item[1]);r.bold=True;p.paragraph_format.keep_with_next=True;result.append(p._p)
  elif item[0]=='table':
   table_no=len(captions['tables'])+1; caption=f'Table {table_no}: '+subject;captions['tables'].append(caption)
   p=doc.add_paragraph(caption);p.paragraph_format.keep_with_next=True;result.append(p._p)
   result.append(add_table(doc,item[1],item[2],prototype));result.append(add_paragraph(doc,''))
  elif item[0]=='image':
   p=doc.add_paragraph();p.paragraph_format.keep_with_next=True;p.add_run().add_picture(str(FIG/(item[1]+'.png')),width=Inches(6.05));result.append(p._p)
   p=doc.add_paragraph(item[2]);captions['figures'].append(item[2]);result.append(p._p)
 return result
def key_for(text):
 m=re.match(r'^(\d+(?:\.\d+)*\.?)[ ]+',text)
 if m:
  k=m.group(1);return k if '.' in k.rstrip('.') else k.rstrip('.')+'.'
 return text
def replace_section(doc,heading,items,prototype,captions):
 node=heading._p;following=node.getnext()
 while following is not None and following.tag!=qn('w:sectPr'):
  if following.tag==qn('w:p'):
   sty=following.find('w:pPr/w:pStyle',doc._element.nsmap)
   if sty is not None and (sty.get(qn('w:val'),'').lower().startswith('heading') or sty.get(qn('w:val'),'').lower()=='tocheading'):break
   if ''.join(t.text or '' for t in following.iter(qn('w:t')))=='Table of Contents':break
   # Retain section boundaries and their page-numbering semantics.
   if following.find('w:pPr/w:sectPr',doc._element.nsmap) is not None:break
  nxt=following.getnext();following.getparent().remove(following);following=nxt
 new=render_items(doc,items,prototype,captions);anchor=node
 for el in new:anchor.addnext(el);anchor=el
def set_plain_text(p,text):
 for child in list(p):
  if child.tag!=qn('w:pPr'):p.remove(child)
 # Preserve existing paragraph properties; insert textual values only.
 r=OxmlElement('w:r')
 for i,line in enumerate(text.split('\n')):
  if i:r.append(OxmlElement('w:br'))
  t=OxmlElement('w:t');t.text=line;r.append(t)
 p.append(r)
def fill_front(doc,kind):
 count=0
 for p in doc._element.iter(qn('w:p')):
  text=''.join(p.itertext()) if False else ''.join(t.text or '' for t in p.iter(qn('w:t')))
  if text=='[Student Name]  [Student ID]' or text=='[Student Name – Student ID]':
   replacement=TEAM[count%3];count+=1
  else:
   replacement=text
   pairs={'[TITLE OF YOUR PROJECT]':TITLE,'[Project Title]':TITLE,'[Title of Your Project]':TITLE,'[Title of your project]':TITLE,'[Dr./Mr./Ms. Supervisor Name]':SUP,'[Dr./Mr./Ms. Co-Supervisor Name]':'Not applicable - no co-supervisor','[Project code]':CODE,'[Name or "N/A"]':'Not applicable - no co-supervisor','[Month Year]':'November 2026','[DD Month YYYY]':DATE,'[DD/MM/YYYY]':'09/11/2026','[DD/MM/YY]':'09/11/26','[1.0]':'1.0','[Draft / Reviewed / Approved]':'Prepared for supervisor review','[Supervisor name]':SUP,'[Organization / client]':'FAST NUCES Karachi academic project','[Repository / drive link]':'D:/fyp','[Names]':'; '.join(TEAM),'[Name]':SUP}
   for a,b in pairs.items():replacement=replacement.replace(a,b)
  if replacement!=text:set_plain_text(p,replacement)
 # Remove instruction and formatting boxes rather than treating them as project content.
 for tbl in list(doc._element.iter(qn('w:tbl'))):
  txt=' '.join(t.text or '' for t in tbl.iter(qn('w:t')))
  if '[Instructions]' in txt or 'Formatting Guidelines (defaults' in txt:
   tbl.getparent().remove(tbl)
 # Drop old TOC caches; they describe the blank template.
 for el in list(doc._element.iter(qn('w:sdt'))):
  txt=' '.join(t.text or '' for t in el.iter(qn('w:instrText')))
  if 'TOC' in txt:el.getparent().remove(el)
 for p in list(doc.paragraphs):
  if p.text.startswith('[Maintain a record') or p.text.startswith('[People to whom') or p.text.startswith('[Once prepared'):
   p._p.getparent().remove(p._p)
 # Set a field-update request without using a LibreOffice save on the template copy.
 settings=doc.settings.element;old=settings.find(qn('w:updateFields'))
 if old is None:old=OxmlElement('w:updateFields');settings.append(old)
 old.set(qn('w:val'),'true')
def add_toc(doc):
 for p in doc.paragraphs:
  if p.text.strip()=='Table of Contents':
   anchor=p._p
   headings=[q for q in doc.paragraphs if q.style.name.startswith('Heading') and q.text not in {'Table of Contents','List of Figures','List of Tables'}]
   for i,h in enumerate(headings):
    el=OxmlElement('w:p');pr=OxmlElement('w:pPr');spacing=OxmlElement('w:spacing');spacing.set(qn('w:after'),'20');pr.append(spacing);el.append(pr)
    if i==0:
     r=OxmlElement('w:r');b=OxmlElement('w:fldChar');b.set(qn('w:fldCharType'),'begin');r.append(b);el.append(r)
     r=OxmlElement('w:r');ins=OxmlElement('w:instrText');ins.text='TOC \\o "1-3" \\h \\z \\u';r.append(ins);el.append(r)
     r=OxmlElement('w:r');b=OxmlElement('w:fldChar');b.set(qn('w:fldCharType'),'separate');r.append(b);el.append(r)
    r=OxmlElement('w:r');t=OxmlElement('w:t');t.text=h.text;r.append(t);el.append(r)
    if i==len(headings)-1:
     r=OxmlElement('w:r');b=OxmlElement('w:fldChar');b.set(qn('w:fldCharType'),'end');r.append(b);el.append(r)
    anchor.addnext(el);anchor=el
   break
def reindex_references(content,headings):
 # IEEE order follows first citation; unused bibliography entries are omitted.
 used=[]
 def scan(x):
  if isinstance(x,str):
   for n in re.findall(r'\[(\d+)\]',x):
    if int(n) not in used:used.append(int(n))
  elif isinstance(x,(tuple,list)):
   for v in x:scan(v)
 for p in headings:
  key=key_for(p.text)
  if key!='References':scan(content.get(key,[]))
 mapping={n:i+1 for i,n in enumerate(used)}
 def remap(x):
  if isinstance(x,str):return re.sub(r'\[(\d+)\]',lambda m:'['+str(mapping.get(int(m.group(1)),int(m.group(1))))+']',x)
  if isinstance(x,list):return [remap(v) for v in x]
  if isinstance(x,tuple):return tuple(remap(v) for v in x)
  return x
 result={k:remap(v) for k,v in content.items()}
 result['References']=[re.sub(r'^\[\d+\]',f'[{mapping[n]}]',REFERENCES[n-1]) for n in used]
 return result
def build(kind,content):
 source=DOWNLOADS/f'FYP-I_{kind}_Template.docx';doc=Document(source)
 original_heads=[p for p in doc.paragraphs if p.style.name.startswith('Heading')]
 content=reindex_references(content,original_heads)
 prototype=deepcopy(doc.tables[-1]._tbl)
 fill_front(doc,kind)
 captions={'figures':[],'tables':[],'kind':kind}
 # Snapshot original heading nodes because new content uses only plain or caption styles.
 for p in original_heads:
  key=key_for(p.text)
  captions['section']=re.sub(r'^\d+(?:\.\d+)*\.?\s+','',p.text)
  if key in content:replace_section(doc,p,content[key],prototype,captions)
 if kind=='Final_Report':
  for p in doc.paragraphs:
   if p.text=='Approval Page':p.paragraph_format.page_break_before=False
 # Build actual figure/table lists after all figures are known.
 for p in doc.paragraphs:
  if p.text=='List of Figures':replace_section(doc,p,captions['figures'],prototype,{'figures':[],'tables':[]})
  if p.text=='List of Tables':replace_section(doc,p,captions['tables'],prototype,{'figures':[],'tables':[]})
 add_toc(doc)
 # Remove leftover guidance and restore source section geometry exactly.
 for p in list(doc.paragraphs):
  if p.text.strip().startswith('[') and not re.match(r'^\[\d+\]',p.text):
   p._p.getparent().remove(p._p)
 # Front metadata records review state without inventing sign-off.
 for table in doc.tables:
  for row in table.rows:
   vals=[c.text for c in row.cells]
   if vals and vals[0]=='Co-Supervisor' and len(row.cells)>1:row.cells[1].text='Not applicable - no co-supervisor'
 # All source-derived headings remain, including nonapplicable chapters.
 draft=TMP/f'{kind}.docx';doc.save(draft)
 final=OUT/f'MediSummarize_AI_FYP-I_{kind}.docx'
 # Preserve unrelated OOXML parts byte for byte instead of accepting library normalization.
 with zipfile.ZipFile(source) as before,zipfile.ZipFile(draft) as after,zipfile.ZipFile(final,'w',zipfile.ZIP_DEFLATED) as z:
  allowed={'word/document.xml','word/_rels/document.xml.rels','word/settings.xml','[Content_Types].xml'}
  for n in before.namelist():
   data=after.read(n) if n in allowed else before.read(n)
   if re.match(r'word/header\d+\.xml$',n):data=data.replace(b'[Project Title]',b'MediSummarize AI')
   z.writestr(n,data)
  for n in after.namelist():
   if n not in before.namelist():z.writestr(n,after.read(n))
 # Content and preservation checks are separate from visual QA.
 check=Document(final);alltext='\n'.join(p.text for p in check.paragraphs)+'\n'+'\n'.join(c.text for t in check.tables for r in t.rows for c in r.cells)
 leftovers=re.findall(r'\[(?!\d+\])[^\]\n]{1,100}\]',alltext)
 if leftovers:raise ValueError((kind,'Unfilled template slots',leftovers))
 if len(doc.sections)!=len(Document(source).sections):raise ValueError('Section count changed')
 source_headings=[p.text for p in Document(source).paragraphs if p.style.name.startswith('Heading')]
 final_headings=[p.text for p in check.paragraphs if p.style.name.startswith('Heading')]
 if source_headings!=final_headings:raise ValueError((kind,'Heading structure changed'))
 report={'file':str(final),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sections':len(doc.sections),'headings_preserved':len(final_headings),'figures':len(captions['figures']),'tables':len(check.tables),'unfilled_slots':leftovers}
 (TMP/f'{kind}-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
def dictionary():
 data=json.loads((TMP/'schema.json').read_text())
 for entity,rows in data.items():
  SDS['5.1.2'] += [B(entity),T(['Column','Type / length','Nullable','Default','Key / relation'],rows)]
def main():
 make_figures();dictionary()
 common_history=[T(['Version','Author','Date','Change'],[['1.0','Project team',DATE,'Prepared implementation-aligned documentation for supervisor review.']])]
 for data in [SRS,SDS]:
  data['Document History']=common_history
  data['Document Sign-Off']=[T(['Version','Authority','Signature','Date'],[['1.0',SUP,'Pending supervisor review','Not signed']])]
 SRS['Distribution List']=[T(['Name','Role','Date sent'],[[SUP,'Supervisor','Not yet distributed'],['Project team','Authors','Local working copy']])]
 build('SRS',SRS);build('SDS',SDS);build('Final_Report',REPORT)
if __name__=='__main__':main()
