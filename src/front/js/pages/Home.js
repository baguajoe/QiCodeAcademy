import { useTranslation } from "react-i18next";
import { useSeo } from "../seo";

export default function Home() {
  const { t } = useTranslation();
  useSeo({ imageSlot: "hero-home" });
  return (
    <section className="section">
      <div className="container">
        <h1>Qi Code Academy</h1>
        <p className="lead">{t("common.tagline")}</p>
      </div>
    </section>
  );
}
