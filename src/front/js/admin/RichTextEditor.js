// Small, dependency-free rich-text editor for news posts. The server sanitizes
// the HTML with bleach on save, so only safe tags are ever stored.
import { useEffect, useRef, useState } from "react";
import { uploadImage } from "./ImageField";

const TOOLS = [
  { cmd: "bold", label: "Bold", text: "B", style: { fontWeight: 800 } },
  { cmd: "italic", label: "Italic", text: "I", style: { fontStyle: "italic" } },
  { cmd: "formatBlock", arg: "h2", label: "Heading", text: "H2" },
  { cmd: "formatBlock", arg: "h3", label: "Subheading", text: "H3" },
  { cmd: "formatBlock", arg: "p", label: "Normal paragraph", text: "¶" },
  { cmd: "insertUnorderedList", label: "Bulleted list", text: "• List" },
  { cmd: "insertOrderedList", label: "Numbered list", text: "1. List" },
  { cmd: "formatBlock", arg: "blockquote", label: "Quote", text: "“ Quote" },
];

export function RichTextEditor({ id, label, value, onChange, error }) {
  const ref = useRef(null);
  const [htmlMode, setHtmlMode] = useState(false);
  const [msg, setMsg] = useState("");
  const fileRef = useRef(null);

  // Only push external value into the DOM when it differs (keeps the caret stable).
  useEffect(() => {
    if (!htmlMode && ref.current && ref.current.innerHTML !== (value || "")) ref.current.innerHTML = value || "";
  }, [value, htmlMode]);

  const exec = (cmd, arg) => {
    ref.current.focus();
    document.execCommand(cmd, false, arg);
    onChange(ref.current.innerHTML);
  };

  const addLink = () => {
    const url = window.prompt("Link address (starting with https://):", "https://");
    if (!url || !/^(https?:\/\/|mailto:|\/)/.test(url)) return;
    exec("createLink", url);
  };

  const addImage = async (e) => {
    const file = e.target.files && e.target.files[0];
    e.target.value = "";
    if (!file) return;
    let alt = "";
    while (!alt) {
      alt = (window.prompt("Describe this photo for people using screen readers (required):", "") || "").trim();
      if (alt === "" && !window.confirm("Alt text is required. Try again?")) return;
    }
    setMsg("Uploading photo…");
    try {
      const url = await uploadImage(file, "news");
      ref.current.focus();
      const safeAlt = alt.replace(/"/g, "&quot;").replace(/</g, "&lt;");
      document.execCommand("insertHTML", false, `<img src="${url}" alt="${safeAlt}" loading="lazy">`);
      onChange(ref.current.innerHTML);
      setMsg("");
    } catch (err) {
      setMsg(err.message || "Upload failed.");
    }
  };

  return (
    <div className="field rte">
      <span className="label" id={`${id}-label`}>{label}</span>
      <div className="rte-toolbar" role="toolbar" aria-label="Formatting" aria-controls={id}>
        {TOOLS.map((t) => (
          <button key={t.label} type="button" className="btn btn-sm btn-outline" aria-label={t.label} title={t.label}
            onMouseDown={(e) => e.preventDefault()} onClick={() => exec(t.cmd, t.arg)} disabled={htmlMode} style={t.style}>
            {t.text}
          </button>
        ))}
        <button type="button" className="btn btn-sm btn-outline" onMouseDown={(e) => e.preventDefault()} onClick={addLink} disabled={htmlMode}>Link</button>
        <button type="button" className="btn btn-sm btn-outline" onMouseDown={(e) => e.preventDefault()} onClick={() => exec("unlink")} disabled={htmlMode}>Unlink</button>
        <button type="button" className="btn btn-sm btn-outline" onClick={() => fileRef.current.click()} disabled={htmlMode}>Insert photo</button>
        <button type="button" className="btn btn-sm btn-outline" onMouseDown={(e) => e.preventDefault()} onClick={() => exec("removeFormat")} disabled={htmlMode}>Clear formatting</button>
        <button type="button" className="btn btn-sm" aria-pressed={htmlMode} onClick={() => setHtmlMode((m) => !m)}>{htmlMode ? "Back to editor" : "Edit HTML"}</button>
        <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" tabIndex={-1} aria-hidden="true" onChange={addImage} />
      </div>
      {msg && <p className="hint" role="status">{msg}</p>}
      {htmlMode ? (
        <textarea id={id} aria-labelledby={`${id}-label`} className="rte-html" value={value || ""} rows={16} onChange={(e) => onChange(e.target.value)} />
      ) : (
        <div id={id} ref={ref} className="rte-area prose" contentEditable suppressContentEditableWarning role="textbox"
          aria-multiline="true" aria-labelledby={`${id}-label`} aria-invalid={error ? "true" : undefined}
          onInput={(e) => onChange(e.currentTarget.innerHTML)} onBlur={(e) => onChange(e.currentTarget.innerHTML)} />
      )}
      {error && <p className="field-error">{error}</p>}
    </div>
  );
}
