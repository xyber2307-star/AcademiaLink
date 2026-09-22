import { useEffect, useRef, useState } from "react";
import { CheckCircle2, Loader2, School, X } from "lucide-react";
import { institutionSearchService, InstitutionSearchResult } from "../../services/institutionSearchService";
import type { MyProfile } from "../../services/userService";

interface Props {
  /** Free-text fallback value (used when nothing from the registry has been selected). */
  freeTextValue: string;
  onFreeTextChange: (value: string) => void;
  /** Currently-selected canonical institution, if any (institution_id + display fields). */
  selected: {
    institution_id?: string;
    institution?: string;
    institutionState?: string;
    institutionDistrict?: string;
    institutionCode?: string;
    institutionVerificationStatus?: MyProfile["institutionVerificationStatus"];
  };
  onSelect: (result: InstitutionSearchResult) => void;
  onClearSelection: () => void;
}

/**
 * Institution search + selection widget backing the college verification flow.
 * The frontend never decides "verified" itself - it only displays whatever the backend's
 * registry search returns and lets the student pick one of those exact candidates.
 * See docs/INSTITUTION_VERIFICATION.md.
 */
export function InstitutionSearchInput({ freeTextValue, onFreeTextChange, selected, onSelect, onClearSelection }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<InstitutionSearchResult[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "empty" | "error" | "source_unavailable">("idle");
  const [open, setOpen] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const isVerified = selected.institution_id && selected.institutionVerificationStatus === "VERIFIED";

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (query.trim().length < 2) {
      setResults([]);
      setStatus("idle");
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setStatus("loading");
      try {
        const resp = await institutionSearchService.search(query.trim());
        if (!resp.sourceAvailable) {
          setStatus("source_unavailable");
          setResults([]);
          return;
        }
        setResults(resp.results);
        setStatus(resp.results.length === 0 ? "empty" : "idle");
      } catch {
        setStatus("error");
        setResults([]);
      }
    }, 350);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  if (isVerified) {
    return (
      <div>
        <label className="block text-xs font-semibold text-slate-700">Institution</label>
        <div className="mt-1 flex items-start justify-between gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2.5">
          <div className="flex items-start gap-2">
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
            <div>
              <p className="text-sm font-medium text-slate-900">{selected.institution}</p>
              <p className="text-xs text-slate-500">
                {[selected.institutionDistrict, selected.institutionState].filter(Boolean).join(", ")}
                {selected.institutionCode ? ` · AICTE ID: ${selected.institutionCode}` : ""}
              </p>
              <p className="mt-0.5 text-[11px] text-emerald-700">Institution registry verified · Source: AICTE</p>
              <p className="text-[11px] text-slate-400">Program-level approval not checked.</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              onClearSelection();
              setQuery("");
            }}
            className="shrink-0 rounded-lg p-1 text-slate-400 hover:bg-white hover:text-slate-600"
            title="Change institution"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      <label className="block text-xs font-semibold text-slate-700">Institution</label>
      <div className="relative mt-1">
        <School className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          value={query || freeTextValue}
          onChange={(e) => {
            setQuery(e.target.value);
            onFreeTextChange(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          placeholder="Search your institution..."
          className="w-full rounded-xl border border-slate-200 px-3 py-2 pl-9 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
        />
        {status === "loading" && (
          <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-slate-400" />
        )}
      </div>

      {freeTextValue && !query && (
        <p className="mt-1 text-[11px] text-amber-600">
          Unable to verify this institution against the available authoritative registry. Search above to find and
          select your institution, or continue with this text (shown as "Not Verified").
        </p>
      )}

      {open && query.trim().length >= 2 && (
        <div className="absolute z-10 mt-1 w-full overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg">
          {status === "loading" && <div className="px-3 py-3 text-xs text-slate-500">Searching institution registry…</div>}

          {status === "source_unavailable" && (
            <div className="px-3 py-3 text-xs text-amber-700">
              Verification temporarily unavailable. The authoritative institution source could not be reached.
              You can still save your institution as free text (shown as "Not Verified") and try searching again later.
            </div>
          )}

          {status === "error" && (
            <div className="px-3 py-3 text-xs text-rose-600">
              Something went wrong searching the institution registry.{" "}
              <button type="button" className="underline" onClick={() => setQuery((q) => q + " ")}>
                Retry
              </button>
            </div>
          )}

          {status === "empty" && (
            <div className="px-3 py-3 text-xs text-slate-500">
              No matching institution found in the available authoritative registry. This does not necessarily mean
              your institution doesn't exist - try a shorter or differently-spelled search, or continue with free text.
            </div>
          )}

          {results.length > 0 && (
            <ul className="max-h-64 overflow-y-auto">
              {results.map((r) => (
                <li key={r.institutionId}>
                  <button
                    type="button"
                    onClick={() => {
                      onSelect(r);
                      setOpen(false);
                      setQuery("");
                    }}
                    className="flex w-full flex-col items-start gap-0.5 px-3 py-2 text-left hover:bg-blue-50"
                  >
                    <span className="text-sm font-medium text-slate-900">{r.name}</span>
                    <span className="text-xs text-slate-500">
                      {[r.district, r.state].filter(Boolean).join(", ")} · AICTE ID: {r.aicteId}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
