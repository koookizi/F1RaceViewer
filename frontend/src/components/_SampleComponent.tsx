import type { RaceControlApiResponse } from "../types";

type SampleComponentProps = {
  raceControlData: RaceControlApiResponse[] | null;
  currentTime: number;
};

export function SampleComponent({
  raceControlData,
  currentTime,
}: SampleComponentProps) {
  if (!raceControlData) {
    return <div className="skeleton h-24 w-auto"></div>;
  }

  return (
    <div className="card card-border bg-base-100 w-full">
      <div className="card-body p-3 max-h-80 overflow-y-auto">Test</div>
    </div>
  );
}
