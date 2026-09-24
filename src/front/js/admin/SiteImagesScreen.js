import { useEffect, useState } from "react";
import { adminApi } from "../api";
import { ErrorNote, Loading } from "../component/common";
import { Photo } from "../component/Photo";
import { SLOTS, localImage } from "../siteImages";
import { useStore } from "../store/appContext";
import { ImageField } from "./ImageField";
import { useTitle } from "./AdminApp";

function SlotCard({ slot, meta, row, onSaved }) {
  const [url, setUrl] = useState(row ? row.image_url : "");
  const [alt, setAlt] = useState(row ? row.alt_text : "");
  const [state, setState] = useState({ saving: false, msg: "", error: "" });
  const dirty = url !== (row ? row.image_url : "") || alt !== (row ? row.alt_text : "");
  const local = localImage(slot);

  const save = async (nextUrl = url, nextAlt = alt) => {
    if (nextUrl && !nextAlt.trim()) return setState({ saving: false, msg: "", error: "Please describe the photo (alt text) before saving." });
    setState({ saving: true, msg: "", error: "" });
    try {
      const body = { image_url: nextUrl || "", alt_text: nextUrl ? nextAlt.trim() : "" };
      if (row) await adminApi.patch(`/admin/site-images/${row.id}`, body);
      else await adminApi.post("/admin/site-images", { slot_key: slot, ...body });
      setState({ saving: false, msg: nextUrl ? "Saved — the website now shows this photo." : "Reset to the default photo.", error: "" });
      onSaved();
    } catch (err) {
      setState({ saving: false, msg: "", error: err.message || "Couldn't save." });
    }
  };

  return (
    <li className="panel slot-card">
      <h2>{meta.page}</h2>
      <p className="muted small">Slot <code>{slot}</code> · Recommended size {meta.size}</p>
      <p><strong>Suggested photo:</strong> {meta.subject.replace(/^[^:]+:\s*/, "")}</p>
      <p className="small">
        Showing now: {row && row.image_url ? "your uploaded photo" : local ? `the default file (${slot}.jpg)` : "a placeholder"}
      </p>
      {!url && (
        <div className="slot-current">
          <Photo src={local} alt="" ratio={meta.ratio} sizes="20rem"
            placeholder={{ division: meta.division, subject: meta.subject, size: meta.size }} />
        </div>
      )}
      <ImageField id={`slot-${slot}`} label={url ? "Uploaded photo" : "Upload a new photo"} value={url} onChange={setUrl}
        alt={alt} onAltChange={setAlt} folder="site" error={state.error && !state.error.includes("alt") ? state.error : ""}
        altError={state.error.includes("alt") ? state.error : ""} />
      {state.msg && <p className="alert alert-success" role="status">{state.msg}</p>}
      <div className="cluster">
        <button type="button" className="btn" disabled={!dirty || state.saving} onClick={() => save()}>{state.saving ? "Saving…" : "Save photo"}</button>
        {row && row.image_url && (
          <button type="button" className="btn btn-outline" onClick={() => { setUrl(""); setAlt(""); save("", ""); }}>Use default instead</button>
        )}
      </div>
    </li>
  );
}

export function SiteImagesScreen() {
  useTitle("Site photos");
  const { actions } = useStore();
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(null);
  const load = () => adminApi.get("/admin/site-images", { params: { per_page: 500 } })
    .then((d) => setRows(Object.fromEntries(d.items.map((r) => [r.slot_key, r])))).catch(setError);
  useEffect(() => { load(); }, []);

  if (error) return <ErrorNote error={error} onRetry={load} />;
  if (!rows) return <Loading />;
  return (
    <>
      <h1>Site photos</h1>
      <p className="admin-help">
        Replace any photo on the website. An uploaded photo takes priority over the default file. Only use photos of
        people who have given photo/video consent, and always describe the photo for people using screen readers.
        See IMAGE_GUIDE.md for the full list of photo spots.
      </p>
      <ul className="slot-grid">
        {Object.entries(SLOTS).map(([slot, meta]) => (
          <SlotCard key={`${slot}-${rows[slot] ? rows[slot].updated_at : "new"}`} slot={slot} meta={meta} row={rows[slot]}
            onSaved={() => { load(); actions.refreshSiteContent(); }} />
        ))}
      </ul>
    </>
  );
}
