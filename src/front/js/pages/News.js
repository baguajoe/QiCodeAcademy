import { Link, useParams, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { useApi } from "../hooks/useApi";
import { useSeo } from "../seo";
import { Empty, ErrorNote, Loading, PageBanner } from "../component/common";
import { NewsCard } from "../component/Cards";
import { Photo } from "../component/Photo";
import NotFound from "./NotFound";
import { formatLongDate, parseUtc } from "../format";

const CATEGORIES = ["youth", "seniors", "research", "community"];

export default function News() {
  const { t } = useTranslation();
  const [params, setParams] = useSearchParams();
  const category = params.get("category") || "";
  const page = Number(params.get("page") || 1);
  const { data, error, loading, reload } = useApi(
    () => api.get("/news", { params: { category, page, per_page: 9 } }), [category, page]);
  useSeo({ title: t("news.title"), description: t("news.lead") });

  const go = (next) => {
    const p = new URLSearchParams();
    if (next.category) p.set("category", next.category);
    if (next.page > 1) p.set("page", next.page);
    setParams(p);
  };

  return (
    <div className="theme-community">
      <PageBanner title={t("news.title")} lead={t("news.lead")} />
      <section className="section">
        <div className="container">
          <div className="filters" role="group" aria-labelledby="news-cat-label">
            <span className="label" id="news-cat-label" style={{ fontWeight: 700 }}>{t("news.category")}</span>
            <div className="cluster">
              {["", ...CATEGORIES].map((c) => (
                <button key={c || "all"} type="button" className={`btn btn-sm ${category === c ? "" : "btn-outline"}`}
                  aria-pressed={category === c} onClick={() => go({ category: c, page: 1 })}>
                  {c ? t(`news.categories.${c}`) : t("news.all")}
                </button>
              ))}
            </div>
          </div>
          {loading && <Loading />}
          {error && <ErrorNote error={error} onRetry={reload} />}
          {data && (data.items.length ? (
            <div className="grid grid-3">{data.items.map((p) => <NewsCard key={p.id} post={p} headingLevel={2} />)}</div>
          ) : <Empty>{t("news.noPosts")}</Empty>)}
          {data && data.pages > 1 && (
            <nav className="pagination" aria-label={t("news.pagination")}>
              <button type="button" className="btn btn-outline" disabled={page <= 1} onClick={() => go({ category, page: page - 1 })}>
                ← {t("news.previous")}
              </button>
              <span>{t("news.page", { page, pages: data.pages })}</span>
              <button type="button" className="btn btn-outline" disabled={page >= data.pages} onClick={() => go({ category, page: page + 1 })}>
                {t("news.next")} →
              </button>
            </nav>
          )}
        </div>
      </section>
    </div>
  );
}

export function NewsPost() {
  const { t } = useTranslation();
  const { slug } = useParams();
  const { data: post, error, loading, reload } = useApi(() => api.get(`/news/${slug}`), [slug]);
  useSeo(post ? {
    title: post.title,
    description: post.excerpt,
    image: post.cover_image_url || undefined,
    type: "article",
    jsonLd: [{
      "@context": "https://schema.org",
      "@type": "NewsArticle",
      headline: post.title,
      datePublished: post.published_at,
      dateModified: post.updated_at,
      publisher: { "@type": "NGO", name: "Qi Code Academy", url: window.location.origin },
      ...(post.cover_image_url ? { image: [post.cover_image_url.startsWith("http") ? post.cover_image_url : window.location.origin + post.cover_image_url] } : {}),
    }],
  } : { title: t("news.title") });

  if (loading) return <div className="container section"><Loading /></div>;
  if (error && error.status === 404) return <NotFound />;
  if (error) return <div className="container section"><ErrorNote error={error} onRetry={reload} /></div>;
  const theme = { seniors: "senior", youth: "youth", research: "research" }[post.category] || "community";

  return (
    <article className={`theme-${theme}`}>
      <section className="banner banner-plain">
        <div className="container banner-content">
          <nav className="breadcrumb" aria-label={t("common.breadcrumb")}><Link to="/news">← {t("news.back")}</Link></nav>
          <span className="badge badge-solid" style={{ alignSelf: "flex-start", marginBottom: "0.75rem" }}>{t(`news.categories.${post.category}`)}</span>
          <h1>{post.title}</h1>
          <p className="muted"><time dateTime={post.published_at}>{t("news.published", { date: formatLongDate(parseUtc(post.published_at)) })}</time></p>
        </div>
      </section>
      <section className="section">
        <div className="container">
          <div className="prose" style={{ margin: "0 auto" }}>
            {post.cover_image_url && <Photo src={post.cover_image_url} alt={post.cover_image_alt || ""} ratio="16 / 9" sizes="(min-width: 48rem) 44rem, 100vw" priority />}
            {/* Body HTML is sanitized server-side with bleach (see API.md). */}
            <div className="news-body" dangerouslySetInnerHTML={{ __html: post.body }} />
          </div>
        </div>
      </section>
    </article>
  );
}
