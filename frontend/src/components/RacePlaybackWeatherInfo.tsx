import type { WeatherApiResponse, WeatherSample } from "../types";
import { TelemetryPill } from "../components/TelemetryPill";

type RacePlaybackProps = {
  weatherData: WeatherApiResponse | null;
  currentTime: number;
  playbackStartTime: number;
};

export function WeatherInfo({
  weatherData,
  currentTime,
  playbackStartTime,
}: RacePlaybackProps) {
  if (!weatherData) {
    return null;
  }

  const weatherTimeline = normalizeWeatherSamples(weatherData.weather);
  const alignedTime = getAlignedWeatherTime(
    weatherTimeline,
    currentTime,
    playbackStartTime
  );
  const w = getWeatherAtTime(weatherTimeline, alignedTime);
  if (!w) return <div>No weather</div>;
  const airTempPercentage =
    w.air_temp != null
      ? calculatePercentage(weatherData.rangeAirTemp, w.air_temp)
      : null;
  const airTempColour =
    airTempPercentage != null
      ? getGradientColorNormal(airTempPercentage)
      : null;

  const humidityPercentage =
    w.humidity != null
      ? calculatePercentage(weatherData.rangeHumidity, w.humidity)
      : null;
  const humidityColour =
    humidityPercentage != null
      ? getGradientColorNormal(humidityPercentage)
      : null;
  const pressurePercentage =
    w.pressure != null
      ? calculatePercentage(weatherData.rangePressure, w.pressure)
      : null;
  const pressureColour =
    pressurePercentage != null
      ? getGradientColorNormal(pressurePercentage)
      : null;
  const trackTempPercentage =
    w.track_temp != null
      ? calculatePercentage(weatherData.rangeTrackTemp, w.track_temp)
      : null;
  const trackTempColour =
    trackTempPercentage != null
      ? getGradientColorNormal(trackTempPercentage)
      : null;
  const windSpeedPercentage =
    w.wind_speed != null
      ? calculatePercentage(weatherData.rangeWindSpeed, w.wind_speed)
      : null;
  const windSpeedColour =
    windSpeedPercentage != null
      ? getGradientColorNormal(windSpeedPercentage)
      : null;

  return (
    <div className="flex gap-4 overflow-x-auto overflow-y-hidden whitespace-nowrap mx-auto items-center justify-center">
      <TelemetryPill
        items={[
          {
            percent: airTempPercentage ?? 0,
            valueText: w.air_temp != null ? w.air_temp.toFixed(1) : "",
            label: "AIR",
            subLabel: "°C",
            color: airTempColour ?? "#fff",
          },
          {
            percent: trackTempPercentage ?? 0,
            valueText: w.track_temp != null ? w.track_temp.toFixed(1) : "",
            label: "TRC",
            subLabel: "°C",
            color: trackTempColour ?? "#fff",
          },
          {
            percent: humidityPercentage ?? 0,
            valueText: w.humidity != null ? w.humidity.toFixed(1) : "",
            label: "HMD",
            subLabel: "%",
            color: humidityColour ?? "#fff",
          },
          {
            percent: pressurePercentage ?? 0,
            valueText: w.pressure != null ? w.pressure.toFixed(1) : "",
            label: "PRS",
            subLabel: "mb",
            color: pressureColour ?? "#fff",
          },
          {
            percent: windSpeedPercentage ?? 0,
            valueText: w.wind_speed != null ? w.wind_speed.toFixed(1) : "",
            label: "WND",
            subLabel: "m/s",
            color: windSpeedColour ?? "#fff",
          },
        ]}
      />
    </div>
  );
}

function normalizeWeatherSamples(samples: WeatherSample[]): WeatherSample[] {
  return [...samples]
    .filter((sample) => Number.isFinite(sample.time_sec))
    .sort((a, b) => a.time_sec - b.time_sec)
    .filter(
      (sample, index, sorted) =>
        index === 0 || sample.time_sec !== sorted[index - 1].time_sec
    );
}

function getAlignedWeatherTime(
  samples: WeatherSample[],
  currentTime: number,
  playbackStartTime: number
): number {
  if (!samples.length) return currentTime;

  const firstSampleTime = samples[0].time_sec;
  const lastSampleTime = samples[samples.length - 1].time_sec;

  if (currentTime >= firstSampleTime && currentTime <= lastSampleTime) {
    return currentTime;
  }

  const normalizedPlaybackTime = currentTime - playbackStartTime;
  if (
    normalizedPlaybackTime >= firstSampleTime &&
    normalizedPlaybackTime <= lastSampleTime
  ) {
    return normalizedPlaybackTime;
  }

  // Fall back to the clock that lands closest to the weather series.
  const rawDistance = Math.min(
    Math.abs(currentTime - firstSampleTime),
    Math.abs(currentTime - lastSampleTime)
  );
  const normalizedDistance = Math.min(
    Math.abs(normalizedPlaybackTime - firstSampleTime),
    Math.abs(normalizedPlaybackTime - lastSampleTime)
  );

  return normalizedDistance < rawDistance
    ? normalizedPlaybackTime
    : currentTime;
}

function getWeatherAtTime(
  samples: WeatherSample[],
  currentTime: number
): WeatherSample | null {
  if (!samples.length) return null;

  // return first entry if current time is less than first data entry, and vice versa
  if (currentTime <= samples[0].time_sec) return samples[0];
  if (currentTime >= samples[samples.length - 1].time_sec) {
    return samples[samples.length - 1];
  }

  let left = 0;
  let right = samples.length - 1;

  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    if (samples[mid].time_sec <= currentTime) {
      left = mid + 1;
    } else {
      right = mid - 1;
    }
  }

  const idx = Math.max(0, right);
  const a = samples[idx];
  const b = samples[idx + 1];

  const t0 = a.time_sec;
  const t1 = b.time_sec;
  const dt = t1 - t0 || 1; // avoid divide-by-zero
  const ratio = (currentTime - t0) / dt;

  // linear interpolation - basically gets the smooth value between 2 things given the ratio.
  const lerp = (x: number | null, y: number | null): number | null => {
    if (x == null || y == null) return null;
    return x + (y - x) * ratio;
  };

  return {
    time_sec: currentTime,
    air_temp: lerp(a.air_temp, b.air_temp),
    track_temp: lerp(a.track_temp, b.track_temp),
    humidity: lerp(a.humidity, b.humidity),
    pressure: lerp(a.pressure, b.pressure),
    rainfall: lerp(a.rainfall, b.rainfall),
    wind_dir: lerp(a.wind_dir, b.wind_dir),
    wind_speed: lerp(a.wind_speed, b.wind_speed),
  };
}

function getGradientColorNormal(pct: number): string {
  // interpolate between colors
  const r = Math.floor((pct / 100) * 255); // 0 → 255
  const g = Math.floor((1 - Math.abs(pct - 50) / 50) * 255); // 255 at 50%
  const b = Math.floor((1 - pct / 100) * 255); // 255 → 0

  return `rgb(${r}, ${g}, ${b})`;
}

function calculatePercentage(range: [number, number], value: number): number {
  const minRange = range[0];
  const maxRange = range[1];

  const percent = ((value - minRange) / (maxRange - minRange)) * 100;
  return Math.round(Math.min(100, Math.max(0, percent)));
}
