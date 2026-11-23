/**
 * Brand marks for the platforms we can actually connect to.
 *
 * These are hand-drawn geometric marks (not official logo files) so the studio does
 * not ship third-party artwork it has no licence for. Each is recognisable at small
 * sizes and inherits a fixed brand colour from the platform, not the theme.
 */

type Platform = "youtube" | "tiktok" | "instagram" | "x" | string;

const size = (value: number) => ({ width: value, height: value });

export function YouTubeMark({ px = 32 }: { px?: number }) {
  return (
    <svg viewBox="0 0 48 48" role="img" aria-label="YouTube" style={size(px)}>
      <rect x="2" y="10" width="44" height="28" rx="9" fill="#FF0033" />
      <path d="M20 18.5l10 5.5-10 5.5z" fill="#fff" />
    </svg>
  );
}

export function TikTokMark({ px = 32 }: { px?: number }) {
  return (
    <svg viewBox="0 0 48 48" role="img" aria-label="TikTok" style={size(px)}>
      <rect x="2" y="2" width="44" height="44" rx="11" fill="#0D0D12" />
      <g transform="translate(1.6,-1.2)" opacity="0.9">
        <path
          d="M28.5 12h3.2c.4 3 2.4 5.2 5.3 5.7v3.3c-2 0-3.8-.7-5.3-1.8v9.1c0 4.6-3.4 7.7-7.6 7.7-4 0-7.1-2.9-7.1-6.7 0-4 3.2-6.9 7.4-6.7v3.4c-.5-.1-1-.2-1.5-.1-1.9.2-3.2 1.6-3.1 3.4.1 1.7 1.6 2.9 3.4 2.8 1.9-.1 3.2-1.5 3.2-3.5z"
          fill="#25F4EE"
        />
      </g>
      <g transform="translate(-1.4,1.2)">
        <path
          d="M28.5 12h3.2c.4 3 2.4 5.2 5.3 5.7v3.3c-2 0-3.8-.7-5.3-1.8v9.1c0 4.6-3.4 7.7-7.6 7.7-4 0-7.1-2.9-7.1-6.7 0-4 3.2-6.9 7.4-6.7v3.4c-.5-.1-1-.2-1.5-.1-1.9.2-3.2 1.6-3.1 3.4.1 1.7 1.6 2.9 3.4 2.8 1.9-.1 3.2-1.5 3.2-3.5z"
          fill="#FE2C55"
        />
      </g>
      <path
        d="M28.5 12h3.2c.4 3 2.4 5.2 5.3 5.7v3.3c-2 0-3.8-.7-5.3-1.8v9.1c0 4.6-3.4 7.7-7.6 7.7-4 0-7.1-2.9-7.1-6.7 0-4 3.2-6.9 7.4-6.7v3.4c-.5-.1-1-.2-1.5-.1-1.9.2-3.2 1.6-3.1 3.4.1 1.7 1.6 2.9 3.4 2.8 1.9-.1 3.2-1.5 3.2-3.5z"
        fill="#fff"
      />
    </svg>
  );
}

export function InstagramMark({ px = 32 }: { px?: number }) {
  const id = "ig-gradient";
  return (
    <svg viewBox="0 0 48 48" role="img" aria-label="Instagram" style={size(px)}>
      <defs>
        <linearGradient id={id} x1="0" y1="1" x2="1" y2="0">
          <stop offset="0%" stopColor="#FFC273" />
          <stop offset="35%" stopColor="#F5603F" />
          <stop offset="65%" stopColor="#D42E82" />
          <stop offset="100%" stopColor="#6A44C8" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="44" height="44" rx="13" fill={`url(#${id})`} />
      <rect x="12" y="12" width="24" height="24" rx="8" fill="none" stroke="#fff" strokeWidth="3" />
      <circle cx="24" cy="24" r="6" fill="none" stroke="#fff" strokeWidth="3" />
      <circle cx="32.4" cy="15.6" r="1.9" fill="#fff" />
    </svg>
  );
}

export function XMark({ px = 32 }: { px?: number }) {
  return (
    <svg viewBox="0 0 48 48" role="img" aria-label="X" style={size(px)}>
      <rect x="2" y="2" width="44" height="44" rx="11" fill="#0D0D12" />
      <path d="M15 14h5.6l5 6.9 5.6-6.9H35l-8.1 10.1L35.4 34h-5.7l-5.3-7.3-6 7.3H14l8.5-10.6z" fill="#fff" />
    </svg>
  );
}

export function PlatformMark({ platform, px = 32 }: { platform: Platform; px?: number }) {
  const key = String(platform ?? "").toLowerCase();
  switch (key) {
    case "youtube":
      return <YouTubeMark px={px} />;
    case "tiktok":
      return <TikTokMark px={px} />;
    case "instagram":
      return <InstagramMark px={px} />;
    case "x":
      return <XMark px={px} />;
    default:
      return (
        <svg viewBox="0 0 48 48" role="img" aria-label={key || "platform"} style={size(px)}>
          <rect x="2" y="2" width="44" height="44" rx="11" fill="#2A2F45" />
          <text x="24" y="30" textAnchor="middle" fontSize="18" fill="#fff" fontFamily="sans-serif">
            {(key.slice(0, 1) || "?").toUpperCase()}
          </text>
        </svg>
      );
  }
}
