/* WORK-LAB Observer — accessibility.js
   Keyboard navigation helpers, live region announcements, focus handling.
   WCAG 2.2 AA: logical tab order, visible focus ring, no auto-scroll/flash. */

const WlA11y = (function () {
  "use strict";

  let liveRegion = null;

  function ensureLiveRegion() {
    if (liveRegion) return liveRegion;
    liveRegion = document.createElement("div");
    liveRegion.setAttribute("role", "status");
    liveRegion.setAttribute("aria-live", "polite");
    liveRegion.className = "sr-only";
    document.body.appendChild(liveRegion);
    return liveRegion;
  }

  /* Announce a status change to assistive tech (mode switch, refresh outcome). */
  function announce(message) {
    const region = ensureLiveRegion();
    region.textContent = "";
    // force a reflow so repeated identical messages re-announce
    void region.offsetHeight;
    region.textContent = message;
  }

  /* Wire up in-page anchor nav: smooth-scroll to section, move focus for a11y. */
  function bindSectionNav(container, activeId) {
    const links = container.querySelectorAll("a.wl-nav-item");
    links.forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        const id = link.getAttribute("href").slice(1);
        const target = document.getElementById(id);
        if (target) {
          target.scrollIntoView({ behavior: "smooth", block: "start" });
          target.setAttribute("tabindex", "-1");
          target.focus({ preventScroll: true });
          setActiveNav(links, id);
        }
      });
    });
    return links;
  }

  function setActiveNav(links, id) {
    links.forEach((l) => {
      const on = l.getAttribute("href").slice(1) === id;
      l.classList.toggle("active", on);
      l.setAttribute("aria-current", on ? "true" : null);
    });
  }

  return { ensureLiveRegion, announce, bindSectionNav, setActiveNav };
})();

if (typeof module !== "undefined" && module.exports) {
  module.exports = { WlA11y };
}
