import { useStore } from "../store/appContext";
import { resolveSlot, uploadedSources } from "../siteImages";

function CameraIcon() {
  return (
    <svg className="ph-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">
      <path d="M4 7h3l1.5-2h7L17 7h3a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1z" />
      <circle cx="12" cy="13" r="3.6" />
    </svg>
  );
}

// Styled stand-in describing the photo that belongs in this spot.
export function Placeholder({ division = "community", subject, size }) {
  return (
    <div className={`placeholder ph-${division}`} role="img" aria-label={`Photo placeholder: ${subject}`}>
      <CameraIcon />
      <span className="ph-caption" aria-hidden="true">
        <span className="ph-label">Photo placeholder</span>
        <br />
        {subject}
        {size ? ` — ${size}` : ""}
      </span>
    </div>
  );
}

// Renders an uploaded URL, a build-time local image object, or a placeholder.
export function Photo({ src, alt = "", sizes = "100vw", priority = false, placeholder, ratio, className = "", fit = "cover", position }) {
  const style = ratio ? { "--ratio": ratio } : undefined;
  const cls = `photo ${ratio ? "photo-frame" : ""} ${className}`.trim();
  const imgProps = {
    alt,
    loading: priority ? "eager" : "lazy",
    decoding: "async",
    style: { objectFit: fit, ...(position ? { objectPosition: position } : {}) },
    ...(priority ? { fetchpriority: "high" } : {}),
  };

  if (src && typeof src === "object") {
    return (
      <div className={cls} style={style}>
        <img src={src.src} srcSet={src.srcSet} sizes={sizes} width={src.width} height={src.height} {...imgProps} />
      </div>
    );
  }
  if (typeof src === "string" && src) {
    const s = uploadedSources(src);
    return (
      <div className={cls} style={style}>
        <picture>
          {s.webpSet && <source type="image/webp" srcSet={s.webpSet} sizes={sizes} />}
          <img src={s.src} srcSet={s.jpgSet || undefined} sizes={sizes} width={s.width} height={s.height} {...imgProps} />
        </picture>
      </div>
    );
  }
  return (
    <div className={cls} style={style}>
      <Placeholder {...(placeholder || { subject: "Photo", division: "community" })} />
    </div>
  );
}

// A named site photo slot (see siteImages.js / IMAGE_GUIDE.md).
export function SiteImage({ slot, sizes, priority, ratio, className, alt }) {
  const { store } = useStore();
  const r = resolveSlot(slot, store.siteImages);
  return (
    <Photo
      src={r.kind === "placeholder" ? null : r.src}
      alt={alt || r.alt}
      sizes={sizes}
      priority={priority}
      ratio={ratio === undefined ? r.meta.ratio : ratio}
      className={className}
      position={r.meta.position}
      placeholder={{ division: r.meta.division, subject: r.meta.subject, size: r.meta.size }}
    />
  );
}

export function isSlotPlaceholder(slot, siteImages) {
  return resolveSlot(slot, siteImages).kind === "placeholder";
}

// In-page photo that renders ONLY when a real photo exists (uploaded or default file) —
// never an empty placeholder box.
export function OptionalSiteImage({ slot, className = "", sizes, ratio, caption }) {
  const { store } = useStore();
  const r = resolveSlot(slot, store.siteImages);
  if (r.kind === "placeholder") return null;
  return (
    <figure className={`inline-photo ${className}`}>
      <Photo src={r.src} alt={r.alt} sizes={sizes} ratio={ratio === undefined ? r.meta.ratio : ratio} />
      {caption && <figcaption>{caption}</figcaption>}
    </figure>
  );
}
