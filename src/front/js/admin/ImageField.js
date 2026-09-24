import { useRef, useState } from "react";
import { adminApi } from "../api";
import { Photo } from "../component/Photo";

const MAX = 10 * 1024 * 1024;
const TYPES = ["image/jpeg", "image/png", "image/webp"];

export async function uploadImage(file, folder) {
  if (!TYPES.includes(file.type)) throw new Error("Please choose a JPG, PNG, or WebP photo.");
  if (file.size > MAX) throw new Error("That photo is larger than 10 MB. Please choose a smaller one.");
  const fd = new FormData();
  fd.append("file", file);
  if (folder) fd.append("folder", folder);
  const res = await adminApi.post("/admin/upload", fd);
  return res.webp_url;
}

// Upload with preview. When `alt` is provided, alt text is required before saving.
export function ImageField({ id, label, value, onChange, alt, onAltChange, altHint, folder, error, altError, required, note }) {
  const fileRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [uploadError, setUploadError] = useState("");

  const pick = async (e) => {
    const file = e.target.files && e.target.files[0];
    e.target.value = "";
    if (!file) return;
    setBusy(true);
    setUploadError("");
    try {
      onChange(await uploadImage(file, folder));
    } catch (err) {
      setUploadError(err.message || "Upload failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <fieldset className="field image-field">
      <legend>{label}{required && <span className="required-mark" aria-hidden="true">*</span>}</legend>
      <div className="image-field-row">
        <div className="image-preview">
          {value ? <Photo src={value} alt={alt || ""} ratio="4 / 3" sizes="16rem" /> : <div className="empty small">No photo yet</div>}
        </div>
        <div className="stack">
          <input ref={fileRef} id={id} type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" tabIndex={-1} aria-label={`Choose a file for: ${label}`} onChange={pick} />
          <div className="cluster">
            <button type="button" className="btn" onClick={() => fileRef.current.click()} disabled={busy}>
              {busy ? "Uploading…" : value ? "Replace photo" : "Upload photo"}
            </button>
            {value && <button type="button" className="btn btn-outline" onClick={() => onChange("")}>Remove</button>}
          </div>
          <p className="hint">JPG, PNG, or WebP, up to 10 MB. Large photos are resized automatically. Only use photos of people who gave photo/video consent.</p>
          {note && value && <p className="hint">{note}</p>}
          {(uploadError || error) && <p className="field-error" role="alert">{uploadError || error}</p>}
          {onAltChange && value && (
            <div className="field" style={{ marginBottom: 0 }}>
              <label htmlFor={`${id}-alt`}>Describe this photo (alt text)<span className="required-mark" aria-hidden="true">*</span></label>
              <span className="hint" id={`${id}-alt-hint`}>{altHint || "What would you tell someone who can't see it? e.g. \"Teens coding together at laptops\"."}</span>
              <input id={`${id}-alt`} type="text" value={alt || ""} maxLength={300} required aria-invalid={altError ? "true" : undefined}
                aria-describedby={`${id}-alt-hint${altError ? ` ${id}-alt-error` : ""}`} onChange={(e) => onAltChange(e.target.value)} />
              {altError && <p className="field-error" id={`${id}-alt-error`}>{altError}</p>}
            </div>
          )}
        </div>
      </div>
    </fieldset>
  );
}
