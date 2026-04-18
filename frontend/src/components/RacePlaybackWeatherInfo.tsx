import { useEffect, useState } from "react";
import type { WeatherApiResponse, WeatherSample } from "../types";
import { TelemetryPill } from "../components/TelemetryPill";

type RacePlaybackProps = {
  weatherData: WeatherApiResponse | null;
  currentTime: number;
};

export function WeatherInfo({ weatherData, currentTime }: RacePlaybackProps) {
  const [rangeAirTemp, setRangeAirTemp] = useState<[number, number]>([0, 0]);
  const [rangeHumidity, setRangeHumidity] = useState<[number, number]>([0, 0]);
  const [rangePressure, setRangePressure] = useState<[number, number]>([0, 0]);
  const [rangeTrackTemp, setRangeTrackTemp] = useState<[number, number]>([
    0, 0,
  ]);
  const [rangeWindSpeed, setRangeWindSpeed] = useState<[number, number]>([
    0, 0,
  ]);

  useEffect(() => {
    if (weatherData) {
      setRangeAirTemp(weatherData.rangeAirTemp);
      setRangeHumidity(weatherData.rangeHumidity);
      setRangePressure(weatherData.rangePressure);
      setRangeTrackTemp(weatherData.rangeTrackTemp);
      setRangeWindSpeed(weatherData.rangeWindSpeed);
    }
  }, [weatherData]);

  if (!weatherData) {
    return;
  }

  const w = getWeatherAtTime(weatherData.weather, currentTime);
  if (!w) return <div>No weather</div>;
  const airTempPercentage =
    w.air_temp != null ? calculatePercentage(rangeAirTemp, w.air_temp) : null;
  const airTempColour =
    rangeAirTemp && airTempPercentage != null
      ? getGradientColorNormal(airTempPercentage)
      : null;

  const humidityPercentage =
    w.humidity != null ? calculatePercentage(rangeHumidity, w.humidity) : null;
  const humidityColour =
    rangeHumidity && humidityPercentage != null
      ? getGradientColorNormal(humidityPercentage)
      : null;
  const pressurePercentage =
    w.pressure != null ? calculatePercentage(rangePressure, w.pressure) : null;
  const pressureColour =
    rangePressure && pressurePercentage != null
      ? getGradientColorNormal(pressurePercentage)
      : null;
  const trackTempPercentage =
    w.track_temp != null
      ? calculatePercentage(rangeTrackTemp, w.track_temp)
      : null;
  const trackTempColour =
    rangeTrackTemp && trackTempPercentage != null
      ? getGradientColorNormal(trackTempPercentage)
      : null;
  const windSpeedPercentage =
    w.wind_speed != null
      ? calculatePercentage(rangeWindSpeed, w.wind_speed)
      : null;
  const windSpeedColour =
    rangeWindSpeed && windSpeedPercentage != null
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

  // this part below basically uses interpolation to use data between of the correct weather data row closest to the current time
  // find the two rows around current_time
  let idx = 0;
  for (let i = 0; i < samples.length - 1; i++) {
    const a = samples[i];
    const b = samples[i + 1];
    if (currentTime >= a.time_sec && currentTime <= b.time_sec) {
      idx = i; // the index of the weather sample before/equal the current time
      break;
    }
  }

  const a = samples[idx];
  const b = samples[idx + 1];
  // ^ so one row before current time, one after

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
