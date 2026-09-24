import { Suspense, lazy, useEffect, useRef } from "react";
import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useStore } from "./store/appContext";
import { Header } from "./component/Header";
import { Footer } from "./component/Footer";
import { Loading } from "./component/common";

// Every page is its own lazily-loaded chunk.
const Home = lazy(() => import(/* webpackChunkName: "home" */ "./pages/Home"));
const About = lazy(() => import(/* webpackChunkName: "about" */ "./pages/About"));
const Founder = lazy(() => import(/* webpackChunkName: "founder" */ "./pages/Founder"));
const programs = () => import(/* webpackChunkName: "programs" */ "./pages/Programs");
const YouthPrograms = lazy(() => programs().then((m) => ({ default: m.YouthPrograms })));
const SeniorPrograms = lazy(() => programs().then((m) => ({ default: m.SeniorPrograms })));
const IntergenerationalPrograms = lazy(() => programs().then((m) => ({ default: m.IntergenerationalPrograms })));
const Research = lazy(() => import(/* webpackChunkName: "research" */ "./pages/Research"));
const events = () => import(/* webpackChunkName: "events" */ "./pages/Events");
const Events = lazy(events);
const EventDetail = lazy(() => events().then((m) => ({ default: m.EventDetail })));
const news = () => import(/* webpackChunkName: "news" */ "./pages/News");
const News = lazy(news);
const NewsPost = lazy(() => news().then((m) => ({ default: m.NewsPost })));
const Gallery = lazy(() => import(/* webpackChunkName: "gallery" */ "./pages/Gallery"));
const NotFound = lazy(() => import(/* webpackChunkName: "notfound" */ "./pages/NotFound"));

function useRouteFocus() {
  const location = useLocation();
  const first = useRef(true);
  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    if (location.hash) {
      const el = document.getElementById(location.hash.slice(1));
      if (el) {
        el.scrollIntoView();
        return;
      }
    }
    window.scrollTo(0, 0);
    // Move focus to the new page's heading so screen readers announce it.
    const t = setTimeout(() => {
      const target = document.querySelector("main h1") || document.getElementById("main-content");
      if (target) {
        if (!target.hasAttribute("tabindex")) target.setAttribute("tabindex", "-1");
        target.focus({ preventScroll: true });
      }
    }, 60);
    return () => clearTimeout(t);
  }, [location.pathname, location.hash]);
}

function PublicLayout() {
  const { t } = useTranslation();
  const { actions } = useStore();
  useRouteFocus();
  useEffect(() => {
    actions.loadSiteContent();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <>
      <a className="skip-link" href="#main-content">{t("a11y.skip")}</a>
      <Header />
      <main id="main-content" tabIndex={-1}>
        <Suspense fallback={<div className="container"><Loading /></div>}>
          <Outlet />
        </Suspense>
      </main>
      <Footer />
    </>
  );
}

export default function Layout() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<PublicLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
          <Route path="/about/founder" element={<Founder />} />
          <Route path="/programs" element={<Navigate to="/#divisions" replace />} />
          <Route path="/programs/youth" element={<YouthPrograms />} />
          <Route path="/programs/seniors" element={<SeniorPrograms />} />
          <Route path="/programs/intergenerational" element={<IntergenerationalPrograms />} />
          <Route path="/research" element={<Research />} />
          <Route path="/events" element={<Events />} />
          <Route path="/events/:slug" element={<EventDetail />} />
          <Route path="/news" element={<News />} />
          <Route path="/news/:slug" element={<NewsPost />} />
          <Route path="/gallery" element={<Gallery />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
