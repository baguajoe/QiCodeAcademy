import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useSeo } from "../seo";

export default function NotFound() {
  const { t } = useTranslation();
  useSeo({ title: t("notFound.title"), noindex: true });
  return (
    <section className="section">
      <div className="container container-narrow center">
        <p className="eyebrow">404</p>
        <h1>{t("notFound.title")}</h1>
        <p className="lead">{t("notFound.body")}</p>
        <div className="cluster" style={{ justifyContent: "center" }}>
          <Link className="btn" to="/">{t("notFound.home")}</Link>
          <Link className="btn btn-outline" to="/contact">{t("nav.contact")}</Link>
        </div>
      </div>
    </section>
  );
}
