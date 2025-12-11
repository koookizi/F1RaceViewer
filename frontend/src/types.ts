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
