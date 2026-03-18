import { BrowserRouter, Route, Routes } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useState } from "react";
import type { SupportedLanguage } from "./types/api";
import { Home } from "./pages/Home";
import { Results } from "./pages/Results";
import { LanguageSwitcher } from "./components/LanguageSwitcher";

function App() {
  const { i18n } = useTranslation();
  const [lang, setLang] = useState<SupportedLanguage>("en");

  function handleLangChange(nextLang: SupportedLanguage) {
    setLang(nextLang);
    i18n.changeLanguage(nextLang);
  }

  return (
    <BrowserRouter>
      <div className="app-shell">
        <header className="top-bar">
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
