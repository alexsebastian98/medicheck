import { useLocation, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { InteractionResult } from "../components/InteractionResult";
import type { CheckInteractionsResponse } from "../types/api";

interface LocationState {
  data?: CheckInteractionsResponse;
}

export function Results() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState;

  if (!state?.data) {
    return (
      <main className="layout">
        <p>Missing analysis data.</p>
        <button className="action" type="button" onClick={() => navigate("/")}>
          {t("back")}
        </button>
      </main>
    );
  }

  return (
    <main className="layout">
      <div className="results-top-row">
        <button className="back-link" type="button" onClick={() => navigate("/")}>
          {t("back")}
        </button>
      </div>
      <InteractionResult data={state.data} />
    </main>
  );
}
