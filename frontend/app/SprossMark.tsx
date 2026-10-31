/**
 * Sprossa – Spross-Marke als Inline-SVG.
 * Ersetzt das 🌱-Emoji im Header: gleiche Form in jeder Schriftart/jedem System,
 * skaliert verlustfrei und ist per aria-hidden dekorativ (der Markenname steht daneben).
 */
export default function SprossMark({
  size = 22,
  color = "#FAF6EF",
  className = "",
}: {
  size?: number;
  color?: string;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 130"
      fill="none"
      aria-hidden="true"
      focusable="false"
      className={className}
    >
      <path
        d="M50 126 C44 96 46 66 52 46"
        stroke={color}
        strokeWidth={9}
        strokeLinecap="round"
      />
      <path d="M50 52 C34 44 20 28 14 10 C32 6 48 26 50 52 Z" fill={color} />
      <path d="M50 52 C66 44 80 28 86 10 C68 6 52 26 50 52 Z" fill={color} />
    </svg>
  );
}
