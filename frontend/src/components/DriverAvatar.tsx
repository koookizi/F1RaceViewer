import { useState } from "react";

type DriverAvatarProps = {
  name: string;
  headshotUrl: string | null;
};

export function DriverAvatar({ name, headshotUrl }: DriverAvatarProps) {
  const [imgError, setImgError] = useState(false);

  const showImg = !!headshotUrl && !imgError;

  return (
    <div className="avatar">
      <div className="mask mask-squircle h-12 w-12 flex items-center justify-center bg-base-300">
        {showImg ? (
          <img
            src={headshotUrl || undefined}
            alt={`Photo of ${name}`}
            onError={() => setImgError(true)}
          />
        ) : (
          <i
            className="bi bi-person-fill text-2xl text-neutral-400"
            aria-hidden="true"
          />
        )}
      </div>
    </div>
  );
}
