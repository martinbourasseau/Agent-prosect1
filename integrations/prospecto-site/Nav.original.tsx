"use client";

import { useEffect, useLayoutEffect, useRef, useState } from "react";
import PMark from "./PMark";
import { Arrow } from "./Icons";

const links = [
  { id: "accueil", label: "Accueil" },
  { id: "prospecto", label: "Prospecto" },
  { id: "solutions", label: "Solutions IA" },
  { id: "synatrap", label: "SYNATRAP" },
  { id: "a-propos", label: "À propos" },
  { id: "contact", label: "Contact" },
];

const useIso = typeof window === "undefined" ? useEffect : useLayoutEffect;

export default function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState<string>("accueil");
  const listRef = useRef<HTMLUListElement>(null);
  const [pill, setPill] = useState<{ x: number; w: number } | null>(null);

  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 40);
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);

  // Section consultée : celle qui occupe le milieu de l'écran.
  useEffect(() => {
    const sections = links
      .map((l) => document.getElementById(l.id))
      .filter((el): el is HTMLElement => !!el);
    // Les sections sans lien direct (fonctionnement, capacités, questions) rattachées à leur parent.
    const extra: Record<string, string> = { fonctionnement: "prospecto", capacites: "prospecto", questions: "a-propos" };
    Object.keys(extra).forEach((id) => {
      const el = document.getElementById(id);
      if (el) sections.push(el);
    });
    if (!sections.length) return;
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) setActive(extra[e.target.id] ?? e.target.id);
        }
      },
      { rootMargin: "-45% 0px -50% 0px" },
    );
    sections.forEach((s) => io.observe(s));
    return () => io.disconnect();
  }, []);

  useIso(() => {
    const list = listRef.current;
    const el = list?.querySelector<HTMLElement>(`[data-id="${active}"]`);
    if (!list || !el) return setPill(null);
    const li = el.parentElement as HTMLElement;
    setPill({ x: li.offsetLeft, w: li.offsetWidth });
  }, [active]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    document.documentElement.classList.add("menu-open");
    return () => {
      window.removeEventListener("keydown", onKey);
      document.documentElement.classList.remove("menu-open");
    };
  }, [open]);

  return (
    <header className="nav-shell">
      <div className="wrap">
        <nav aria-label="Navigation principale" className="nav glass" data-scrolled={scrolled || open} data-glow>
          <a href="/#accueil" className="flex min-h-[44px] items-center gap-2.5" aria-label="Prospecto, retour à l'accueil">
            <PMark className="h-8 w-auto" />
            <span className="wordmark text-[0.78rem] text-[var(--light)]" style={{ letterSpacing: "0.34em" }}>
              Prospecto
            </span>
          </a>

          <ul ref={listRef} className="relative hidden items-center gap-0.5 xl:flex">
            {pill && (
              <li
                aria-hidden="true"
                className="nav-pill"
                style={{ transform: `translateX(${pill.x}px)`, width: pill.w }}
              />
            )}
            {links.map((l) => (
              <li key={l.id} className="relative">
                <a
                  className="nav-link"
                  data-id={l.id}
                  href={`/#${l.id}`}
                  aria-current={active === l.id ? "true" : undefined}
                >
                  {l.label}
                </a>
              </li>
            ))}
          </ul>

          <div className="flex items-center gap-2">
            <a href="/#contact" className="btn btn-primary hidden !min-h-[44px] !px-5 text-[0.9rem] sm:inline-flex" data-glow data-magnetic>
              Parlons de votre projet
            </a>
            <button
              type="button"
              className="menu-toggle glass xl:hidden"
              aria-expanded={open}
              aria-controls="menu-mobile"
              onClick={() => setOpen((v) => !v)}
            >
              <span className="sr-only">{open ? "Fermer le menu" : "Ouvrir le menu"}</span>
              <span className="menu-bars" data-open={open} aria-hidden="true">
                <i />
                <i />
              </span>
            </button>
          </div>
        </nav>
      </div>

      <div id="menu-mobile" className="menu-sheet xl:hidden" data-open={open} aria-hidden={!open} inert={!open}>
        <div className="menu-sheet-inner wrap">
          <ul className="flex flex-col">
            {links.map((l, i) => (
              <li key={l.id} style={{ ["--i" as string]: i }}>
                <a
                  className="menu-link"
                  href={`/#${l.id}`}
                  aria-current={active === l.id ? "true" : undefined}
                  onClick={() => setOpen(false)}
                >
                  <span>{l.label}</span>
                  <Arrow />
                </a>
              </li>
            ))}
          </ul>
          <div className="menu-foot" style={{ ["--i" as string]: links.length }}>
            <a href="/#contact" onClick={() => setOpen(false)} className="btn btn-primary w-full">
              Parlons de votre projet
            </a>
            <a href="https://synatrap.com" className="btn btn-glass glass w-full">
              Découvrir SYNATRAP
            </a>
          </div>
        </div>
      </div>
    </header>
  );
}
