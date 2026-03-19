import { BrowserRouter, Route, Routes } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useState } from "react";
import type { SupportedLanguage } from "./types/api";
import { Home } from "./pages/Home";
import { Results } from "./pages/Results";
import { LanguageSwitcher } from "./components/LanguageSwitcher";

function App() {
  const { i18n, t } = useTranslation();
  const [lang, setLang] = useState<SupportedLanguage>("en");

  function handleLangChange(nextLang: SupportedLanguage) {
    setLang(nextLang);
    i18n.changeLanguage(nextLang);
  }

  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <div className="app-shell">
        <header className="top-bar">
          <div className="app-brand">{t("appTitle")}</div>
          <LanguageSwitcher lang={lang} onChange={handleLangChange} />
        </header>
        <Routes>
          <Route path="/" element={<Home lang={lang} />} />
          <Route path="/results" element={<Results />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
