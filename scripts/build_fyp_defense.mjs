import fs from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
const root='D:/fyp',build=root+'/tmp/artifacts/slides';
await fs.mkdir(build,{recursive:true});
const p=Presentation.create({slideSize:{width:1280,height:720}});
const data=[
['MediSummarize AI','FYP I implementation and research status',['Secure clinical document summarization using retrieval augmented generation','CS-FYP-1019 · FAST NUCES Karachi · Fall 2026']],
['Problem and project objective','A traceable workflow for fragmented documents',['Bring laboratory reports, prescriptions and discharge notes into one review.','Preserve evidence behind generated claims and state unavailable information.','Research question: does retrieval improve coverage and faithfulness over full-text generation?']],
['FYP I delivery boundary','The prototype works in explicitly labeled mock mode',['Implemented: ownership, ingestion, extraction, lexical retrieval and summary review.','A compatible local-model adapter exists. The current provider is MOCK/TEST OUTPUT.','Real-model paired evaluation remains outstanding before the research criterion can close.']],
['Document and review workflow','The reviewer checks the source before accepting a claim',['Upload fictional PDF, image or text documents into one owned record.','Inspect extracted pages and OCR warnings, then retrieve section-relevant passages.','Generate fixed sections, follow citations, open the source page and export.']],
['Implemented architecture','Local services with replaceable model providers',['React and TypeScript call FastAPI with authenticated record ownership.','SQLite stores metadata. Protected files and NumPy indexes store sources and vectors.','Lexical hashing is the current embedding baseline. Semantic models and PostgreSQL remain unverified.']],
['Frontend review workspace','A focused path from source upload to evidence review',['Create, search and sort fictional records. Batch retry retains unsuccessful files.','Document and summary tabs show sources, extraction states and citations.','Text and JSON exports retain source excerpts, provider metadata and mock labels.']],
['Safety and source lifecycle','A valid source ID still requires human verification',['Authorize before retrieval. Validate source files and reject cross-account access.','Move uncited claims into unresolved information. Show research and mock labels.','Invalidate stored summaries whenever sources change, so stale snapshots cannot return.']],
['Verification evidence','Application checks pass; model-quality evidence is pending',['60 backend tests passed. Nine frontend tests passed. Production build succeeded.','The evaluation dry run produced 18 mock rows across nine manifest entries. Zero reportable rows.','Browser walkthrough remains unverified after tool timeouts and a Windows browser policy block.']],
['Evaluation and remaining FYP I work','Both conditions must use the same real model',['Retrieved context uses character chunks and top four hits per section query.','The baseline uses full extracted text with the same provider and output schema.','Freeze held-out cases and the model, run both conditions, then review claim support and missing facts.']],
['Submission package and FYP II plan','The next milestone is a real-model baseline',['Prepared in supplied templates: final report, SRS and SDS, with diagrams and traceability.','Before sign-off: finish the baseline, verify browser upload/export and obtain supervisor review.','FYP II: semantic retrieval, broader evaluation, optional adaptation, roles and hardened deployment.']]
];
function txt(s,value,x,y,w,h,size,color='#153d33',bold=false){let a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});a.text=value;a.text.style={fontFamily:'Arial',fontSize:size,bold,color};}
for(let i=0;i<data.length;i++){
 const [title,sub,body]=data[i],s=p.slides.add();s.background.fill=i===0?'#153d33':'#f7f8f1';
 if(i===0){txt(s,title,78,100,1124,100,70,'#ffffff',true);txt(s,sub,82,222,1115,65,31,'#c4ddc7');txt(s,body[0],82,350,1050,100,31,'#ffffff');txt(s,body[1],82,475,1100,45,22,'#c4ddc7');txt(s,'Muhammad Humayun Dar (23K-0795) · Muhammad Hamza Siddiqui (23K-0500)\nHassan Sheikh (22K-5157) · Supervisor: Dr. Muhammad Yaseen Khan',82,552,1100,70,20,'#ffffff');}
 else{txt(s,title,78,62,1124,80,44,'#153d33',true);txt(s,sub,80,154,1120,65,27,'#536b57');body.forEach((b,j)=>txt(s,b,80,273+j*118,1100,96,29,'#203f32'));}
 txt(s,String(i+1)+' / '+data.length+'     MediSummarize AI · FYP I · 09 November 2026',80,665,1110,26,15,i===0?'#c4ddc7':'#536b57');
 s.speakerNotes.text='Project CS-FYP-1019. Supervisor: Dr. Muhammad Yaseen Khan. No co-supervisor. Team: Muhammad Humayun Dar (23K-0795), Muhammad Hamza Siddiqui (23K-0500), Hassan Sheikh (22K-5157). Sources: supplied proposal, current source code, docs/project-status.md and companion SRS/SDS/report, verified 09 November 2026. Current generation is mock. No clinical performance or real-model improvement is claimed. Signatures, similarity check and approval remain pending.';
 await fs.writeFile(build+'/slide-'+(i+1)+'.png',new Uint8Array(await (await p.export({slide:s,format:'png',scale:1})).arrayBuffer()));
}
await (await PresentationFile.exportPptx(p)).save(build+'/candidate.pptx');
const skill="C:/Users/Hamza's PC/.codex/plugins/cache/openai-primary-runtime/presentations/26.1105.12137/skills/presentations";
const {finalizePresentation}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs').href);
await finalizePresentation({workspaceDir:root,candidatePath:build+'/candidate.pptx',finalPath:root+'/output/fyp-i/MediSummarize_AI_FYP-I_Defense_Review.pptx',pythonExecutable:"C:/Users/Hamza's PC/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe",integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,explicitTotalSlideCount:10,receiptPath:build+'/validation-final.json'});
await fs.copyFile(root+'/output/fyp-i/MediSummarize_AI_FYP-I_Defense_Review.pptx',root+'/output/fyp-i/MediSummarize_AI_FYP-I_Defense.pptx');
await fs.unlink(root+'/output/fyp-i/MediSummarize_AI_FYP-I_Defense_Review.pptx');
console.log('Defense PPTX finalized.');
