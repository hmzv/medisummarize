import { render, screen } from "@testing-library/react";
import { DisclaimerBanner } from "../components/DisclaimerBanner";

describe("DisclaimerBanner", () => {
  it("shows the required prototype disclaimer", () => {
    render(<DisclaimerBanner />);
    expect(
      screen.getByText(/Not for diagnosis, prescribing, treatment recommendations/i),
    ).toBeInTheDocument();
  });
});
