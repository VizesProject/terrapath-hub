const list = document.querySelector("#guideList");
const search = document.querySelector("#searchInput");

let guides = [];

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
    <h2>${escapeHtml(guide.title)}</h2>
    <p>${escapeHtml(guide.summary)}</p>
    <div class="guide-card__meta">
      <span>Class: ${escapeHtml((guide.classTags || []).join(", "))}</span>
      <span>Language: ${escapeHtml(guide.language)}</span>
      <span>Popularity: ${Number(guide.popularity || 0)}</span>
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
    const response = await fetch(path, { cache: "no-store" });
    if (response.ok) {
      return response.json();
    }
  }

  throw new Error("Catalog request failed.");
}

async function loadCatalog() {
  const catalog = await fetchCatalog();
  guides = catalog.guides || [];
  render();
}

search.addEventListener("input", render);
loadCatalog().catch((error) => {
  list.textContent = error.message;
});
