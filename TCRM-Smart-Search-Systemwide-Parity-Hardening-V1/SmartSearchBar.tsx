import { useMemo, useState } from "react";
import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import VoiceSearchButton from "./VoiceSearchButton";
import { normalizeSearchText } from "@shared/searchNormalization";

export type SmartSearchSuggestion =
  | string
  | {
      id: string | number;
      label: string;
      secondary?: string | null;
    };

type SmartSearchBarProps = {
  value: string;
  onValueChange: (value: string) => void;
  placeholder?: string;
  language?: "ar-EG" | "en-US";
  suggestions?: SmartSearchSuggestion[];
  containerClassName?: string;
  inputClassName?: string;
  compact?: boolean;
  disabled?: boolean;
  showVoice?: boolean;
  showClear?: boolean;
  ariaLabel?: string;
  autoFocus?: boolean;
  onFocus?: () => void;
  onBlur?: () => void;
};

export default function SmartSearchBar({
  value,
  onValueChange,
  placeholder,
  language = "en-US",
  suggestions = [],
  containerClassName,
  inputClassName,
  compact = false,
  disabled = false,
  showVoice = true,
  showClear = true,
  ariaLabel,
  autoFocus = false,
  onFocus,
  onBlur,
}: SmartSearchBarProps) {
  const [focused, setFocused] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const isRTL = language.startsWith("ar");
  const suggestionsReady = normalizeSearchText(value).length >= 2;

  const normalizedSuggestions = useMemo(() => {
    const seen = new Set<string>();
    const out: Array<{ id: string | number; label: string; secondary?: string | null }> = [];
    for (const item of suggestions) {
      const suggestion =
        typeof item === "string"
          ? { id: item, label: item, secondary: null }
          : {
              id: item.id,
              label: String(item.label ?? "").trim(),
              secondary: item.secondary ?? null,
            };
      if (!suggestion.label) continue;
      const key = normalizeSearchText(suggestion.label);
      if (!key || seen.has(key)) continue;
      seen.add(key);
      out.push(suggestion);
      if (out.length >= 6) break;
    }
    return out;
  }, [suggestions]);

  const visibleSuggestions = suggestionsReady ? normalizedSuggestions : [];
  const labels = isRTL
    ? {
        start: "بحث بالصوت",
        listening: "جاري الاستماع... اضغط للإيقاف",
        unsupported: "البحث الصوتي غير مدعوم في هذا المتصفح",
        error: "تعذر التقاط الصوت. حاول مرة أخرى.",
        clear: "مسح البحث",
      }
    : {
        start: "Search by voice",
        listening: "Listening... click to stop",
        unsupported: "Voice search is not supported in this browser",
        error: "Could not capture speech. Please try again.",
        clear: "Clear search",
      };

  const selectSuggestion = (label: string) => {
    onValueChange(label);
    setFocused(false);
    setActiveIndex(-1);
  };

  return (
    <div className={cn("relative w-full", containerClassName)} dir={isRTL ? "rtl" : "ltr"}>
      <Search
        aria-hidden="true"
        className={cn(
          "pointer-events-none absolute top-1/2 z-10 -translate-y-1/2 text-muted-foreground",
          compact ? "h-3.5 w-3.5" : "h-4 w-4",
          isRTL ? "right-3" : "left-3",
        )}
      />
      {/* SMART_SEARCH_SYSTEMWIDE_V1: reusable normalized search + suggestions + voice + clear */}
      <Input
        type="text"
        value={value}
        onChange={event => {
          onValueChange(event.target.value);
          setActiveIndex(-1);
        }}
        onFocus={() => {
          setFocused(true);
          onFocus?.();
        }}
        onBlur={() => {
          window.setTimeout(() => setFocused(false), 120);
          onBlur?.();
        }}
        onKeyDown={event => {
          if (!visibleSuggestions.length) return;
          if (event.key === "ArrowDown") {
            event.preventDefault();
            setActiveIndex(index => Math.min(index + 1, visibleSuggestions.length - 1));
          } else if (event.key === "ArrowUp") {
            event.preventDefault();
            setActiveIndex(index => Math.max(index - 1, 0));
          } else if (event.key === "Enter" && activeIndex >= 0) {
            event.preventDefault();
            selectSuggestion(visibleSuggestions[activeIndex].label);
          } else if (event.key === "Escape") {
            setFocused(false);
            setActiveIndex(-1);
          }
        }}
        placeholder={placeholder}
        aria-label={ariaLabel || placeholder}
        autoFocus={autoFocus}
        disabled={disabled}
        autoComplete="off"
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={focused && visibleSuggestions.length > 0}
        className={cn(
          compact ? "h-8 text-xs" : "h-10",
          isRTL
            ? showVoice || (showClear && value) ? "pr-9 pl-16" : "pr-9"
            : showVoice || (showClear && value) ? "pl-9 pr-16" : "pl-9",
          inputClassName,
        )}
      />
      <div
        className={cn(
          "absolute top-1/2 z-20 flex -translate-y-1/2 items-center gap-0.5",
          isRTL ? "left-1" : "right-1",
        )}
      >
        {showClear && value ? (
          <button
            type="button"
            onMouseDown={event => event.preventDefault()}
            onClick={() => {
              onValueChange("");
              setActiveIndex(-1);
            }}
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
            aria-label={labels.clear}
          >
            <X className={compact ? "h-3 w-3" : "h-3.5 w-3.5"} />
          </button>
        ) : null}
        {showVoice ? (
          <VoiceSearchButton
            language={language}
            onTranscript={text => {
              onValueChange(text);
              setActiveIndex(-1);
            }}
            labels={labels}
          />
        ) : null}
      </div>

      {focused && visibleSuggestions.length > 0 ? (
        <div
          role="listbox"
          className="absolute start-0 end-0 top-full z-50 mt-1 overflow-hidden rounded-xl border bg-popover text-popover-foreground shadow-xl"
        >
          {visibleSuggestions.map((suggestion, index) => (
            <button
              key={`${suggestion.id}:${suggestion.label}`}
              type="button"
              role="option"
              aria-selected={activeIndex === index}
              onMouseDown={event => {
                event.preventDefault();
                selectSuggestion(suggestion.label);
              }}
              className={cn(
                "block w-full px-3 py-2 text-start text-sm hover:bg-muted",
                activeIndex === index && "bg-muted",
              )}
            >
              <span className="block truncate font-medium">{suggestion.label}</span>
              {suggestion.secondary ? (
                <span className="block truncate text-[11px] text-muted-foreground">
                  {suggestion.secondary}
                </span>
              ) : null}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
