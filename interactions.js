(function initResearchSelection() {
  const button = document.getElementById("research-toggle");
  const heading = document.getElementById("research-heading");
  const status = document.getElementById("research-status");
  const container = document.getElementById("research-papers");
  const papers = Array.from(document.querySelectorAll("#research-papers .paper-row"));
  if (!button || !heading || !container || papers.length === 0) return;

  let showAll = new URLSearchParams(location.search).get("publications") === "all";
  function updateSelection(announce) {
    const order = showAll ? "allOrder" : "selectedOrder";
    papers.slice().sort((a, b) => Number(a.dataset[order]) - Number(b.dataset[order])).forEach(paper => {
      paper.hidden = !showAll && paper.dataset.highlight !== "true";
      container.appendChild(paper);
    });
    heading.textContent = showAll ? "Publications & Manuscripts" : "Selected Publications & Manuscripts";
    button.textContent = showAll ? "Selected Research Papers" : "All Research Papers";
    button.setAttribute("aria-expanded", String(showAll));
    button.setAttribute("aria-label", showAll ? "Show selected publications only" : "Show all publications and manuscripts");
    if (announce && status) {
      status.textContent = `Showing ${papers.filter(paper => !paper.hidden).length} ${showAll ? "total" : "selected"} publications.`;
    }
  }

  function revealHashTarget() {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    const target = document.getElementById(id);
    if (target && target.matches(".paper-row") && target.dataset.highlight !== "true") {
      showAll = true;
      updateSelection(false);
    }
    if (target && target.matches(".paper-row")) {
      requestAnimationFrame(() => target.scrollIntoView({ block: "start", behavior: "instant" }));
    }
  }

  button.addEventListener("click", () => { showAll = !showAll; updateSelection(true); });
  updateSelection(false);
  button.hidden = false;
  revealHashTarget();
  window.addEventListener("hashchange", revealHashTarget);
})();

(function initFigurePreview() {
  const dialog = document.getElementById("figure-dialog");
  const image = document.getElementById("figure-image");
  const caption = document.getElementById("figure-caption");
  if (!dialog || typeof dialog.showModal !== "function") return;
  let trigger = null;
  document.querySelectorAll("a[data-figure]").forEach(link => {
    link.addEventListener("click", event => {
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      trigger = link;
      image.src = link.href;
      image.alt = link.querySelector("img").alt;
      caption.textContent = link.dataset.caption;
      dialog.showModal();
    });
  });
  dialog.addEventListener("click", event => {
    const bounds = dialog.getBoundingClientRect();
    if (event.target === dialog && (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom)) dialog.close();
  });
  dialog.addEventListener("close", () => { if (trigger) trigger.focus({ preventScroll: true }); });
})();
