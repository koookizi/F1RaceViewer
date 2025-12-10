export type TrackPoint = [number, number];

export type DriverSample = {
  t: number;   // seconds since race start
  lap: number;
  x: number;
  y: number;
};

export type DriverSeries = {
  code: string;
  color: string;
  samples: DriverSample[];
};

export type PlaybackData = {
  track: { points: TrackPoint[] };
  drivers: DriverSeries[];
  raceDuration: number;
  totalLaps: number;
};
