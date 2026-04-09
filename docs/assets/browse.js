const list = document.querySelector("#guideList");
const search = document.querySelector("#searchInput");
const languageFilter = document.querySelector("#languageFilter");
const classFilter = document.querySelector("#classFilter");
const modFilter = document.querySelector("#modFilter");
const sortFilter = document.querySelector("#sortFilter");
const guideCountSummary = document.querySelector("#guideCountSummary");

let guides = [];

function pageParams() {
  return new URLSearchParams(window.location.search);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function guideToSearchText(guide) {
  return [
    guide.title,
    guide.author,
    guide.language,
    guide.summary,
    ...(guide.requiredMods || []),
    ...(guide.classTags || []),
    ...(guide.guideTags || [])
  ].join(" ").toLowerCase();
}

function uniqueSorted(values) {
  return Array.from(new Set(values.filter(Boolean))).sort((left, right) => left.localeCompare(right));
}

function populateFilter(select, values, emptyLabel) {
  const current = select.value;
  select.innerHTML = [`<option value="">${emptyLabel}</option>`]
    .concat(values.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`))
    .join("");
  if (values.includes(current)) {
    select.value = current;
  }
}

function renderGuide(guide) {
  const card = document.createElement("article");
  card.className = "guide-card";
  card.innerHTML = `
    <div class="guide-card__head">
      <div>
        <h2><a class="guide-card__link" href="guide.html?id=${encodeURIComponent(guide.id)}">${escapeHtml(guide.title)}</a></h2>
        <p>${escapeHtml(guide.summary)}</p>
      </div>
      <a class="button button--quiet button--tiny" href="guide.html?id=${encodeURIComponent(guide.id)}">Open guide</a>
    </div>
    <div class="guide-card__meta">
      <span>Class: ${escapeHtml((guide.classTags || []).join(", "))}</span>
      <span>Language: ${escapeHtml(guide.language)}</span>
      <span>Popularity: ${Number(guide.popularity || 0)}</span>
      <span>Stages: ${Number(guide.stageCount || 0)}</span>
      <span>Mods: ${escapeHtml((guide.requiredMods || []).join(", "))}</span>
    </div>
  `;
  return card;
}

function compareGuides(left, right) {
  switch (sortFilter.value) {
    case "title":
      return left.title.localeCompare(right.title);
    case "updated":
      return String(right.updatedAt || "").localeCompare(String(left.updatedAt || ""));
    case "popularity":
    default:
      return Number(right.popularity || 0) - Number(left.popularity || 0) || left.title.localeCompare(right.title);
  }
}

function render() {
  const query = search.value.trim().toLowerCase();
  const filtered = guides
    .filter((guide) => !query || guideToSearchText(guide).includes(query))
    .filter((guide) => !languageFilter.value || guide.language === languageFilter.value)
    .filter((guide) => !classFilter.value || (guide.classTags || []).includes(classFilter.value))
    .filter((guide) => !modFilter.value || (guide.requiredMods || []).includes(modFilter.value))
    .sort(compareGuides);

  guideCountSummary.textContent = `${filtered.length} of ${guides.length} guides shown`;
  list.replaceChildren(...filtered.map(renderGuide));
  if (!filtered.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "No guides found for the selected filters.";
    list.append(empty);
  }
}

async function fetchCatalog() {
  const paths = ["catalog/index.json", "../catalog/index.json"];

  for (const path of paths) {
    try {
      const response = await fetch(path, { cache: "no-store" });
      if (response.ok) {
        return response.json();
      }
    } catch {
      // Ignore and continue to fallback path.
    }
  }

  throw new Error("Catalog request failed.");
}

function applySelectedSearchFromPage() {
  const selected = pageParams().get("selected");
  const selectedGuide = guides.find((guide) => guide.id === selected);
  if (selectedGuide) {
    search.value = selectedGuide.title;
  }
}

function populateFilters() {
  populateFilter(languageFilter, uniqueSorted(guides.map((guide) => guide.language)), "All languages");
  populateFilter(classFilter, uniqueSorted(guides.flatMap((guide) => guide.classTags || [])), "All classes");
  populateFilter(modFilter, uniqueSorted(guides.flatMap((guide) => guide.requiredMods || [])), "All mods");
}

async function loadCatalog() {
  const catalog = await fetchCatalog();
  guides = catalog.guides || [];
  populateFilters();
  applySelectedSearchFromPage();
  render();
}

search.addEventListener("input", render);
languageFilter.addEventListener("change", render);
classFilter.addEventListener("change", render);
modFilter.addEventListener("change", render);
sortFilter.addEventListener("change", render);

loadCatalog().catch((error) => {
  list.textContent = error.message;
});
