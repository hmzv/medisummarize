import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { RecordDetailPage } from "./RecordDetailPage";
import * as api from "../api/client";
vi.mock("../components/PrototypeShell", () => ({PrototypeShell: ({children}: {children: React.ReactNode}) => <>{children}</>}));
vi.mock("../components/ExperimentResults", () => ({ExperimentPreview: () => null}));
vi.mock("../api/client", async importOriginal => ({...await importOriginal<typeof api>(), getRecord:vi.fn(), listDocuments:vi.fn(), fetchSummary:vi.fn(), generateSummary:vi.fn(), uploadDocument:vi.fn(), extractDocument:vi.fn(), fetchExtractedText:vi.fn()}));
const doc = {id:"d1",record_id:"r1",original_filename:"note.txt",file_kind:"text",size_bytes:50,status:"indexed",page_count:1};
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });
function renderPage() { return render(<MemoryRouter initialEntries={["/records/r1"]}><Routes><Route path="/records/:recordId" element={<RecordDetailPage />} /></Routes></MemoryRouter>); }
beforeEach(() => {
 vi.mocked(api.getRecord).mockResolvedValue({id:"r1",display_label:"Case A",created_at:"2026-11-09T00:00:00Z"} as api.RecordResponse);
 vi.mocked(api.listDocuments).mockResolvedValue([doc as api.DocumentResponse]);
 vi.mocked(api.fetchSummary).mockRejectedValue(new api.ApiError(404,"No summary"));
});
it("opens source text using instant scrolling when reduced motion is requested", async () => {
 vi.stubGlobal("matchMedia", vi.fn(() => ({matches:true})));
 const scroll = vi.fn();
 const original = document.getElementById.bind(document);
 vi.spyOn(document,"getElementById").mockImplementation(id => {
   const node = original(id);
   if (node) Object.defineProperty(node,"scrollIntoView",{value:scroll, configurable:true});
   return node;
 });
 vi.mocked(api.fetchExtractedText).mockResolvedValue({document_id:"d1",status:"indexed",public_error:null,items:[{id:"p1",document_id:"d1",page_number:1,text:"Synthetic source evidence.",extraction_method:"utf8_text",ocr_confidence:null,warnings:[],created_at:"2026-11-10T00:00:00Z"}]} as api.ExtractedPageListResponse);
 renderPage(); await screen.findByRole("heading",{name:"Review the record"});
 fireEvent.click(screen.getByRole("tab",{name:"Summary & evidence"}));
 fireEvent.click(screen.getByRole("button",{name:/note\.txt.*Extracted.*1 page/}));
 expect(await screen.findByText("Synthetic source evidence.")).toBeInTheDocument();
 expect(scroll).toHaveBeenCalledWith({behavior:"auto",block:"center"});
});
it("enables generation and review for indexed documents", async () => {
 renderPage();
 expect(await screen.findByRole("heading",{name:"Review the record"})).toBeInTheDocument();
 expect(screen.getByRole("button",{name:"Generate summary"})).toBeEnabled();
 expect(screen.getByRole("button",{name:"Review text"})).toBeEnabled();
});
it("does not generate before any document text is ready", async () => {
 vi.mocked(api.listDocuments).mockResolvedValue([{...doc,status:"uploaded"} as api.DocumentResponse]);
 renderPage(); await screen.findByRole("heading",{name:"Review the record"});
 expect(screen.getByRole("button",{name:"Generate summary"})).toBeDisabled();
 expect(screen.getByText(/Extract text from at least one/)).toBeInTheDocument();
});
it("retains failed batch files and never reuploads a successful file on retry", async () => {
 vi.mocked(api.uploadDocument).mockResolvedValueOnce(doc as api.DocumentResponse).mockRejectedValueOnce(new api.ApiError(400,"Second file failed")).mockResolvedValueOnce(doc as api.DocumentResponse);
 renderPage(); await screen.findByRole("heading",{name:"Review the record"});
 const first=new File(["SYNTHETIC"],"first.txt",{type:"text/plain"}); const second=new File(["SYNTHETIC"],"second.txt",{type:"text/plain"});
 fireEvent.change(screen.getByLabelText("Choose synthetic files"),{target:{files:[first,second]}});
 fireEvent.click(screen.getByRole("button",{name:"Upload 2 files"}));
 await screen.findByText("Second file failed");
 fireEvent.click(screen.getByRole("button",{name:"Upload 1 file"}));
 await waitFor(() => expect(api.uploadDocument).toHaveBeenCalledTimes(3));
 expect(vi.mocked(api.uploadDocument).mock.calls.map(c => c[1].name)).toEqual(["first.txt","second.txt","second.txt"]);
});
