export type TrackPoint = [number, number];

export type DriverSample = {
  t: number; // seconds since race start
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

export type WeatherSample = {
  time_sec: number;
  air_temp: number | null;
  track_temp: number | null;
  humidity: number | null;
  wind_dir: number | null;
  wind_speed: number | null;
  pressure: number | null;
  rainfall: number | null;
};

export type WeatherApiResponse = {
  weather: WeatherSample[];
  rangeAirTemp: [number, number];
  rangeHumidity: [number, number];
  rangePressure: [number, number];
  rangeTrackTemp: [number, number];
  rangeWindSpeed: [number, number];
};

export interface LapData {
  Time: number | null;
  LapStartTime: number | null;
  LapTime: number | null;

  LapNumber: number | null;
  Stint: number | null;

  PitOutTime: number | null;
  PitInTime: number | null;

  Sector1Time: number | null;
  Sector2Time: number | null;
  Sector3Time: number | null;

  Sector1SessionTime: number | null;
  Sector2SessionTime: number | null;
  Sector3SessionTime: number | null;

  SpeedI1: number | null;
  SpeedI2: number | null;
  SpeedFL: number | null;
  SpeedST: number | null;

  IsPersonalBest: boolean | number | null;

  Compound: string | null;
  TyreLife: number | null;
  FreshTyre: boolean | null;

  Position: number | null;
}

export interface DriverData {
  driver_code: string;
  driver_fullName: string;
  teamColour: string;
  data: LapData[];
}

export interface SessionLeaderboardResponse {
  drivers: DriverData[];
}
