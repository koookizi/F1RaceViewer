import React, { useEffect, useState } from "react";
import type { WeatherApiResponse, WeatherSample } from "../types";

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
    return <div className="skeleton h-24 w-auto"></div>;
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
  const windDirPercentage =
    w.wind_dir != null ? calculatePercentage([0, 360], w.wind_dir) : null;

  return (
    <div className="card card-border bg-base-100 w-full">
      <div className="card-body">
        <div className="flex gap-4 overflow-x-auto overflow-y-hidden whitespace-nowrap mx-auto">
          <div className="flex items-center gap-4 -mb-9">
            {/* Gauge Component */}
            <div className="relative size-30">
              <svg
                className="size-full rotate-180"
                viewBox="0 0 36 36"
                xmlns="http://www.w3.org/2000/svg"
              >
                {/* Background Circle (Gauge) */}
                <circle
                  cx="18"
                  cy="18"
                  r="16"
                  fill="none"
                  className="stroke-current text-orange-100 dark:text-neutral-700"
                  strokeWidth="3"
                  stroke-dasharray="50 100"
                  strokeLinecap="round"
                ></circle>

                {/* Gauge Progress */}
                <circle
                  cx="18"
                  cy="18"
                  r="16"
                  fill="none"
                  style={
                    {
                      color: airTempColour,
                    } as React.CSSProperties
                  }
                  className="stroke-current"
                  strokeWidth="1"
                  stroke-dasharray={`${(airTempPercentage ?? 0) / 2} 100`}
                  strokeLinecap="round"
                ></circle>
              </svg>

              {/* Value Text */}
              <div
                className="absolute top-9 start-1/2 transform -translate-x-1/2 text-center"
                style={
                  {
                    color: airTempColour,
                  } as React.CSSProperties
                }
              >
                <span className="text-2xl font-bold ">
                  {w.air_temp?.toFixed(1)}°C
                </span>
                <span className="text-xs  block">AIR</span>
              </div>
            </div>
            {/* End Gauge Component */}
            {/* Gauge Component */}
            <div className="relative size-30">
              <svg
                className="size-full rotate-180"
                viewBox="0 0 36 36"
                xmlns="http://www.w3.org/2000/svg"
              >
                {/* Background Circle (Gauge) */}
                <circle
                  cx="18"
                  cy="18"
                  r="16"
                  fill="none"
                  className="stroke-current text-orange-100 dark:text-neutral-700"
                  strokeWidth="3"
                  stroke-dasharray="50 100"
                  strokeLinecap="round"
                ></circle>

                {/* Gauge Progress */}
                <circle
                  cx="18"
                  cy="18"
                  r="16"
                  fill="none"
                  style={
                    {
                      color: trackTempColour,
                    } as React.CSSProperties
                  }
                  className="stroke-current"
                  strokeWidth="1"
                  stroke-dasharray={`${(trackTempPercentage ?? 0) / 2} 100`}
                  strokeLinecap="round"
                ></circle>
              </svg>

              {/* Value Text */}
              <div
                className="absolute top-9 start-1/2 transform -translate-x-1/2 text-center"
                style={
                  {
                    color: trackTempColour,
                  } as React.CSSProperties
                }
              >
                <span className="text-2xl font-bold ">
                  {w.track_temp?.toFixed(1)}°C
                </span>
                <span className="text-xs  block">TRACK</span>
              </div>
            </div>
            {/* End Gauge Component */}
            {/* Gauge Component */}
            <div className="relative size-30">
              <svg
                className="size-full rotate-180"
                viewBox="0 0 36 36"
                xmlns="http://www.w3.org/2000/svg"
              >
                {/* Background Circle (Gauge) */}
                <circle
                  cx="18"
                  cy="18"
                  r="16"
                  fill="none"
                  className="stroke-current text-orange-100 dark:text-neutral-700"
                  strokeWidth="3"
                  stroke-dasharray="50 100"
                  strokeLinecap="round"
                ></circle>

                {/* Gauge Progress */}
                <circle
                  cx="18"
                  cy="18"
                  r="16"
                  fill="none"
                  style={
                    {
                      color: humidityColour,
                    } as React.CSSProperties
                  }
                  className="stroke-current"
                  strokeWidth="1"
                  stroke-dasharray={`${(humidityPercentage ?? 0) / 2} 100`}
                  strokeLinecap="round"
                ></circle>
              </svg>

              {/* Value Text */}
              <div
                className="absolute top-9 start-1/2 transform -translate-x-1/2 text-center"
                style={
                  {
                    color: humidityColour,
                  } as React.CSSProperties
                }
              >
                <span className="text-2xl font-bold ">
                  {w.humidity?.toFixed(1)}%
                </span>
                <span className="text-xs  block">HUMIDITY</span>
              </div>
            </div>
            {/* End Gauge Component */}
            {/* Gauge Component */}
            <div className="relative size-30">
              <svg
                className="size-full rotate-180"
                viewBox="0 0 36 36"
                xmlns="http://www.w3.org/2000/svg"
              >
                {/* Background Circle (Gauge) */}
                <circle
                  cx="18"
                  cy="18"
                  r="16"
                  fill="none"
                  className="stroke-current text-orange-100 dark:text-neutral-700"
                  strokeWidth="3"
                  stroke-dasharray="50 100"
                  strokeLinecap="round"
                ></circle>

                {/* Gauge Progress */}
                <circle
                  cx="18"
                  cy="18"
                  r="16"
                  fill="none"
                  style={
                    {
                      color: pressureColour,
                    } as React.CSSProperties
                  }
                  className="stroke-current"
                  strokeWidth="1"
                  stroke-dasharray={`${(pressurePercentage ?? 0) / 2} 100`}
                  strokeLinecap="round"
                ></circle>
              </svg>

              {/* Value Text */}
              <div
                className="absolute top-9 start-1/2 transform -translate-x-1/2 text-center"
                style={
                  {
                    color: pressureColour,
                  } as React.CSSProperties
                }
              >
                <span className="text-2xl font-bold ">
                  {w.pressure?.toFixed(1)}mb
                </span>
                <span className="text-xs  block">PRESSURE</span>
              </div>
            </div>
            {/* End Gauge Component */}
            {/* Gauge Component */}
            <div className="relative size-30">
              <svg
                className="size-full rotate-180"
                viewBox="0 0 36 36"
                xmlns="http://www.w3.org/2000/svg"
              >
                {/* Background Circle (Gauge) */}
                <circle
                  cx="18"
                  cy="18"
                  r="16"
                  fill="none"
                  className="stroke-current text-orange-100 dark:text-neutral-700"
                  strokeWidth="3"
                  stroke-dasharray="50 100"
                  strokeLinecap="round"
                ></circle>

                {/* Gauge Progress */}
                <circle
                  cx="18"
                  cy="18"
                  r="16"
                  fill="none"
                  style={
                    {
                      color: windSpeedColour,
                    } as React.CSSProperties
                  }
                  className="stroke-current"
                  strokeWidth="1"
                  stroke-dasharray={`${(windSpeedPercentage ?? 0) / 2} 100`}
                  strokeLinecap="round"
                ></circle>
              </svg>

              {/* Value Text */}
              <div
                className="absolute top-9 start-1/2 transform -translate-x-1/2 text-center"
                style={
                  {
                    color: windSpeedColour,
                  } as React.CSSProperties
                }
              >
                <span className="text-2xl font-bold ">
                  {w.wind_speed?.toFixed(1)}m/s
                </span>
                <span className="text-xs  block">WIND SPEED</span>
              </div>
            </div>
            {/* End Gauge Component */}
            {/* Gauge Component */}
            <div className="relative size-30">
              {/* Value Text */}
              <div
                className="absolute top-9 start-1/2 transform -translate-x-1/2 text-center"
                style={
                  {
                    color: airTempColour,
                  } as React.CSSProperties
                }
              >
                <span className="text-2xl font-bold ">
                  {w.wind_dir?.toFixed(1)}°
                </span>
                <span className="text-xs  block">WIND DIR</span>
              </div>
            </div>
            {/* End Gauge Component */}
          </div>
        </div>
      </div>
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
