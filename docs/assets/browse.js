const list = document.querySelector("#guideList");
const search = document.querySelector("#searchInput");

let guides = [];

function pageParams() {
  return new URLSearchParams(window.location.search);
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

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
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

function render() {
  const query = search.value.trim().toLowerCase();
  const filtered = guides.filter((guide) => guideToSearchText(guide).includes(query));
  list.replaceChildren(...filtered.map(renderGuide));
  if (!filtered.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "No guides found.";
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

async function loadCatalog() {
  const catalog = await fetchCatalog();
  guides = catalog.guides || [];

  const selected = pageParams().get("selected");
  const selectedGuide = guides.find((guide) => guide.id === selected);
  if (selectedGuide) {
    search.value = selectedGuide.title;
  }

  render();
}

search.addEventListener("input", render);
loadCatalog().catch((error) => {
  list.textContent = error.message;
});
