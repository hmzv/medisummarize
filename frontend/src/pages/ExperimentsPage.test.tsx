import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ExperimentsPage } from "./ExperimentsPage";
import * as api from "../api/experiments";

vi.mock("../components/PrototypeShell", () => ({PrototypeShell: ({children}: {children: React.ReactNode}) => <>{children}</>}));
vi.mock("../api/experiments", () => ({listExperiments: vi.fn(), importExperiments: vi.fn()}));
const run: api.ExperimentRun = {id:"r1",model:"Tesseract",dataset:"RxHandBD v3 ML",split:"validation",samples:446,metrics:{cer:.78,wer:1.1,exact_match:.01,digit_samples:15,digit_sequence_match:0},elapsed_seconds:198,created_at:"2026-11-10T00:00:00Z",limitations:["Word crops only"],verification:"user_supplied",provenance:{}};

it("shows measured validation scores separately from unrun models and final test", async () => {
  vi.mocked(api.listExperiments).mockResolvedValue({items:[run],notice:"Imported"});
  render(<MemoryRouter><ExperimentsPage /></MemoryRouter>);
  expect(await screen.findByText("78.0%")).toBeInTheDocument();
  expect(screen.getAllByText("Not run")).toHaveLength(2);
  fireEvent.change(screen.getByLabelText("Evaluation split"), {target:{value:"test"}});
  expect(screen.queryByText("78.0%")).not.toBeInTheDocument();
  expect(screen.getByText(/No results match/)).toBeInTheDocument();
});

it("rejects malformed JSON before calling the import endpoint", async () => {
  vi.mocked(api.listExperiments).mockResolvedValue({items:[],notice:"Imported"});
  render(<MemoryRouter><ExperimentsPage /></MemoryRouter>);
  await screen.findByText("Ready for your first measured run");
  const file = new File(["invalid"], "bad.json", {type:"application/json"});
  Object.defineProperty(file,"text",{value:async()=>"invalid"});
  fireEvent.change(screen.getByLabelText("Import experiment JSON"),{target:{files:[file]}});
  expect(await screen.findByRole("alert")).toHaveTextContent("not valid JSON");
  expect(api.importExperiments).not.toHaveBeenCalled();
});
