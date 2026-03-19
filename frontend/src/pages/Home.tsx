import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { DrugInputBox } from "../components/DrugInputBox";
import { checkInteractions } from "../api/interactionApi";
import type { CheckInteractionsResponse, SupportedLanguage } from "../types/api";
import { useState } from "react";

interface HomeProps {
  lang: SupportedLanguage;
}

export function Home({ lang }: HomeProps) {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(payload: {
    drugs: string[];
    allergies: string[];
    conditions: string[];
  }) {
    try {
      setLoading(true);
      setError("");

      const response: CheckInteractionsResponse = await checkInteractions({
        ...payload,
        lang,
      });

      navigate("/results", {
        state: {
          data: response,
        },
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      console.error("API Error:", message, err);
      setError(`API request failed: ${message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="layout">
      <section className="hero">
        <h1 className="hero-title">{t("appTitle")}</h1>
        <p className="hero-subtitle">{t("subtitle")}</p>
      </section>
      <DrugInputBox onSubmit={handleSubmit} isLoading={loading} />
      {error && <p className="error">{error}</p>}
      <footer className="app-footer">{t("footer")}</footer>
    </main>
  );
}
