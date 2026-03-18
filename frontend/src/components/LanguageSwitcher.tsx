import type { SupportedLanguage } from "../types/api";

interface LanguageSwitcherProps {
  lang: SupportedLanguage;
  onChange: (lang: SupportedLanguage) => void;
}

export function LanguageSwitcher({ lang, onChange }: LanguageSwitcherProps) {
  return (
    <div className="language-switcher" role="group" aria-label="Language switcher">
      <button
        type="button"
        className={lang === "en" ? "active" : ""}
        onClick={() => onChange("en")}
      >
        EN
      </button>
      <button
        type="button"
        className={lang === "de" ? "active" : ""}
        onClick={() => onChange("de")}
      >
        DE
      </button>
    </div>
  );
}
