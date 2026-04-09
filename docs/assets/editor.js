const STORAGE_KEY = "terrapath-editor-draft-v3";

const LANGUAGE_OPTIONS = [
  { value: "en-US", label: "English (US)" },
  { value: "ru-RU", label: "Russian" }
];

const SUPPORTED_MOD_OPTIONS = [
  {
    value: "Terraria",
    label: "Terraria",
    description: "Vanilla progression and content",
    availableInEditor: true
  },
  {
    value: "CalamityMod",
    label: "Calamity Mod",
    description: "Guide metadata can mention it; curated item support comes later",
    availableInEditor: false
  },
  {
    value: "ThoriumMod",
    label: "Thorium Mod",
    description: "Guide metadata can mention it; curated item support comes later",
    availableInEditor: false
  }
];

const CLASS_TAG_OPTIONS = [
  { value: "melee", label: "Melee" },
  { value: "ranged", label: "Ranged" },
  { value: "magic", label: "Magic" },
  { value: "summoner", label: "Summoner" },
  { value: "rogue", label: "Rogue" },
  { value: "bard", label: "Bard" },
  { value: "other", label: "Other" }
];

const GUIDE_TAG_OPTIONS = [
  { value: "starter", label: "Starter" },
  { value: "prehardmode", label: "Pre-Hardmode" },
  { value: "hardmode", label: "Hardmode" },
  { value: "bossing", label: "Bossing" },
  { value: "progression", label: "Progression" },
  { value: "vanilla", label: "Vanilla" },
  { value: "calamity", label: "Calamity" },
  { value: "thorium", label: "Thorium" },
  { value: "draft", label: "Draft" }
];

const CATEGORY_LABELS = {
  weapon: "Weapons",
  armor: "Armor",
  accessory: "Accessories",
  ammo: "Ammo",
  tool: "Tools",
  mount: "Mounts",
  pet: "Pets",
  buff: "Buffs",
  material: "Materials",
  ore: "Ores",
  furniture: "Furniture",
  other: "Other"
};

const CATEGORY_OPTIONS = Object.keys(CATEGORY_LABELS);

const supportStatus = document.querySelector("#supportStatus");
const titleInput = document.querySelector("#titleInput");
const authorInput = document.querySelector("#authorInput");
const languageSelect = document.querySelector("#languageSelect");
const requiredModOptions = document.querySelector("#requiredModOptions");
const classTagOptions = document.querySelector("#classTagOptions");
const guideTagOptions = document.querySelector("#guideTagOptions");
const summaryInput = document.querySelector("#summaryInput");
const addStageButton = document.querySelector("#addStageButton");
const copyJsonButton = document.querySelector("#copyJsonButton");
const resetDraftButton = document.querySelector("#resetDraftButton");
const downloadButton = document.querySelector("#downloadButton");
const openIssueButton = document.querySelector("#openIssueButton");
const submissionStatus = document.querySelector("#submissionStatus");
const stageList = document.querySelector("#stageList");
const guidePreview = document.querySelector("#guidePreview");
const jsonPreview = document.querySelector("#jsonPreview");

let latestJson = "{}";
let supportIndex = {
  items: [],
  bosses: [],
  itemMap: new Map(),
  bossMap: new Map()
};

let state = loadDraft() || createDefaultState();

function createDefaultState() {
  return {
    createdAt: today(),
    title: "Vanilla Melee Starter Path",
    author: "TerraPath Team",
    language: "en-US",
    requiredMods: ["Terraria"],
    classTags: ["melee"],
    guideTags: ["starter", "progression", "vanilla", "draft"],
    summary: "A structured melee progression path that shows how TerraPath guides can be authored and previewed.",
    stages: [
      createStage({
        title: "First Night",
        description: "Collect movement accessories, set up an arena, and prepare a reliable early weapon.",
        goalsText: "Find a mobility accessory\nPrepare a simple wooden arena\nCraft or loot a stronger melee option",
        notesText: "This is still an example draft.",
        bossRefs: ["Terraria/EyeofCthulhu"],
        items: [
          {
            itemId: "Terraria/EnchantedBoomerang",
            category: "weapon",
            priority: 70,
            note: "A safe ranged melee option for early exploration."
          },
          {
            itemId: "Terraria/CloudinaBottle",
            category: "accessory",
            priority: 85,
            note: "Early movement is always worth prioritizing."
          }
        ]
      })
    ]
  };
}

function createStage(seed = {}) {
  return {
    title: seed.title || "New Stage",
    description: seed.description || "",
    goalsText: seed.goalsText || "",
    notesText: seed.notesText || "",
    bossRefs: Array.isArray(seed.bossRefs) ? [...seed.bossRefs] : [],
    items: Array.isArray(seed.items) && seed.items.length
      ? seed.items.map((item) => createItem(item))
      : [createItem()]
  };
}

function createItem(seed = {}) {
  return {
    itemId: seed.itemId || "",
    category: seed.category || "weapon",
    priority: Number.isFinite(seed.priority) ? seed.priority : 50,
    note: seed.note || ""
  };
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

function slugify(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "new-guide";
}

function splitLines(value) {
  return String(value || "")
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function splitCommaSeparated(value) {
  return Array.from(new Set(
    String(value || "")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean)
  ));
}

function uniqueValues(values) {
  return Array.from(new Set((values || []).filter(Boolean)));
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#039;");
}

function titleCaseCategory(category) {
  return CATEGORY_LABELS[category] || category;
}

function initials(label) {
  return String(label || "?")
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0] || "")
    .join("")
    .toUpperCase();
}

function saveDraft() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function loadDraft() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }
    return normalizeState(JSON.parse(raw));
  } catch {
    return null;
  }
}

function normalizeState(raw) {
  if (!raw || typeof raw !== "object") {
    return createDefaultState();
  }

  const requiredMods = Array.isArray(raw.requiredMods)
    ? raw.requiredMods
    : splitCommaSeparated(raw.requiredModsText || "Terraria");
  const classTags = Array.isArray(raw.classTags)
    ? raw.classTags
    : splitCommaSeparated(raw.classTagsText || "melee").map((tag) => tag.toLowerCase());
  const guideTags = Array.isArray(raw.guideTags)
    ? raw.guideTags
    : splitCommaSeparated(raw.guideTagsText || "draft").map((tag) => tag.toLowerCase());

  return {
    createdAt: typeof raw.createdAt === "string" ? raw.createdAt : today(),
    title: String(raw.title || ""),
    author: String(raw.author || ""),
    language: String(raw.language || "en-US"),
    requiredMods: uniqueValues(requiredMods),
    classTags: uniqueValues(classTags),
    guideTags: uniqueValues(guideTags),
    summary: String(raw.summary || ""),
    stages: Array.isArray(raw.stages) && raw.stages.length
      ? raw.stages.map((stage) => createStage(stage))
      : [createStage()]
  };
}

function buildChoiceMarkup(option, group, selectedValues) {
  const checked = selectedValues.includes(option.value) ? "checked" : "";
  const disabled = option.disabled ? "disabled" : "";
  const unavailable = option.availableInEditor === false ? "choice-chip--muted" : "";

  return `
    <label class="choice-chip ${unavailable}">
      <input
        type="checkbox"
        data-choice-group="${group}"
        value="${escapeHtml(option.value)}"
        ${checked}
        ${disabled}>
      <span class="choice-chip__label">${escapeHtml(option.label)}</span>
      <span class="choice-chip__description">${escapeHtml(option.description || "")}</span>
    </label>
  `;
}

function renderChoiceGroups() {
  requiredModOptions.innerHTML = SUPPORTED_MOD_OPTIONS.map((option) =>
    buildChoiceMarkup(option, "required-mods", state.requiredMods)).join("");
  classTagOptions.innerHTML = CLASS_TAG_OPTIONS.map((option) =>
    buildChoiceMarkup(option, "class-tags", state.classTags)).join("");
  guideTagOptions.innerHTML = GUIDE_TAG_OPTIONS.map((option) =>
    buildChoiceMarkup(option, "guide-tags", state.guideTags)).join("");
}

function renderLanguageOptions() {
  languageSelect.innerHTML = LANGUAGE_OPTIONS.map((option) => `
    <option value="${option.value}">${escapeHtml(option.label)}</option>
  `).join("");
}

function syncMetadataInputs() {
  titleInput.value = state.title;
  authorInput.value = state.author;
  languageSelect.value = state.language;
  summaryInput.value = state.summary;
  renderChoiceGroups();
}

function buildGuide() {
  const usedStageIds = new Map();

  const stages = state.stages.map((stage, index) => {
    const title = stage.title.trim() || `Stage ${index + 1}`;
    const baseId = slugify(title).slice(0, 40) || `stage-${index + 1}`;
    let stageId = baseId;
    const seenCount = usedStageIds.get(baseId) || 0;
    if (seenCount > 0) {
      stageId = `${baseId}-${seenCount + 1}`.slice(0, 40);
    }
    usedStageIds.set(baseId, seenCount + 1);

    const bossRefs = uniqueValues(stage.bossRefs.map((value) => value.trim()).filter(Boolean));
    const goals = splitLines(stage.goalsText);
    const notes = splitLines(stage.notesText);
    const items = stage.items
      .map((item) => ({
        itemId: item.itemId.trim(),
        category: item.category,
        priority: Number.isFinite(item.priority) ? item.priority : 50,
        note: item.note.trim()
      }))
      .filter((item) => item.itemId)
      .map((item) => {
        const output = {
          itemId: item.itemId,
          category: item.category
        };

        if (item.priority !== 50) {
          output.priority = item.priority;
        }
        if (item.note) {
          output.note = item.note;
        }

        return output;
      });

    const output = {
      id: stageId,
      title,
      items
    };

    if (stage.description.trim()) {
      output.description = stage.description.trim();
    }
    if (bossRefs.length) {
      output.bossRefs = bossRefs;
    }
    if (goals.length) {
      output.goals = goals;
    }
    if (notes.length) {
      output.notes = notes;
    }

    return output;
  });

  const guide = {
    schemaVersion: 1,
    id: slugify(`${state.requiredMods[0] || "guide"}-${state.classTags[0] || "path"}-${state.title}`),
    title: state.title.trim() || "Untitled Guide",
    author: state.author.trim() || "Unknown Author",
    language: state.language || "en-US",
    summary: state.summary.trim() || "Draft guide.",
    requiredMods: state.requiredMods.length ? state.requiredMods : ["Terraria"],
    classTags: state.classTags.length ? state.classTags : ["other"],
    createdAt: state.createdAt,
    updatedAt: today(),
    stages
  };

  if (state.guideTags.length) {
    guide.guideTags = [...state.guideTags];
  }

  return guide;
}

function resolveEntry(contentId, map) {
  return map.get(contentId) || null;
}

function resolveEntryName(contentId, map) {
  const entry = resolveEntry(contentId, map);
  if (entry?.displayName) {
    return entry.displayName;
  }
  return String(contentId || "").split("/").pop() || contentId;
}

function iconMarkup(entry, label) {
  if (entry?.icon) {
    return `<img class="content-icon" src="${escapeHtml(entry.icon)}" alt="${escapeHtml(label)}" loading="lazy">`;
  }

  return `<span class="content-token">${escapeHtml(initials(label))}</span>`;
}

function buildContentBadge(contentId, map) {
  const entry = resolveEntry(contentId, map);
  const label = resolveEntryName(contentId, map);
  return `
    <div class="content-chip">
      <span class="content-chip__media">${iconMarkup(entry, label)}</span>
      <span>${escapeHtml(label)}</span>
    </div>
  `;
}

function renderStagePreview(stage) {
  const groupedItems = new Map();
  for (const item of stage.items) {
    const key = item.category || "other";
    const existing = groupedItems.get(key) || [];
    existing.push(item);
    groupedItems.set(key, existing);
  }

  const groups = Array.from(groupedItems.entries())
    .sort(([left], [right]) => titleCaseCategory(left).localeCompare(titleCaseCategory(right)))
    .map(([category, items]) => `
      <section class="category-block">
        <h4>${escapeHtml(titleCaseCategory(category))}</h4>
        <div class="content-grid">
          ${items.map((item) => {
            const entry = resolveEntry(item.itemId, supportIndex.itemMap);
            const label = resolveEntryName(item.itemId, supportIndex.itemMap);
            return `
              <article class="content-card">
                <div class="content-card__head">
                  <span class="content-card__media">${iconMarkup(entry, label)}</span>
                  <div>
                    <strong>${escapeHtml(label)}</strong>
                    <div class="content-card__meta">${escapeHtml(item.itemId)}</div>
                  </div>
                </div>
                ${item.note ? `<p class="content-card__note">${escapeHtml(item.note)}</p>` : ""}
              </article>
            `;
          }).join("")}
        </div>
      </section>
    `)
    .join("");

  return `
    <article class="stage-preview">
      <div class="stage-preview__header">
        <h3>${escapeHtml(stage.title)}</h3>
        <span class="meta-pill">${stage.items.length} item picks</span>
      </div>
      ${stage.description ? `<p>${escapeHtml(stage.description)}</p>` : ""}
      ${stage.bossRefs?.length ? `
        <section class="preview-block">
          <h4>Bosses</h4>
          <div class="chip-row">
            ${stage.bossRefs.map((bossRef) => buildContentBadge(bossRef, supportIndex.bossMap)).join("")}
          </div>
        </section>
      ` : ""}
      ${stage.goals?.length ? `
        <section class="preview-block">
          <h4>Goals</h4>
          <ul class="line-list">
            ${stage.goals.map((goal) => `<li>${escapeHtml(goal)}</li>`).join("")}
          </ul>
        </section>
      ` : ""}
      ${groups || `<p class="empty-state">No item picks added for this stage yet.</p>`}
      ${stage.notes?.length ? `
        <section class="preview-block">
          <h4>Notes</h4>
          <ul class="line-list">
            ${stage.notes.map((note) => `<li>${escapeHtml(note)}</li>`).join("")}
          </ul>
        </section>
      ` : ""}
    </article>
  `;
}

function renderGuidePreview(guide) {
  const metaPills = [
    `Class: ${guide.classTags.join(", ")}`,
    `Language: ${guide.language}`,
    `Mods: ${guide.requiredMods.join(", ")}`,
    `${guide.stages.length} stages`
  ];

  guidePreview.innerHTML = `
    <header class="guide-preview__header">
      <h2>${escapeHtml(guide.title)}</h2>
      <p>${escapeHtml(guide.summary)}</p>
      <div class="chip-row">
        ${metaPills.map((pill) => `<span class="meta-pill">${escapeHtml(pill)}</span>`).join("")}
      </div>
    </header>
    <div class="guide-preview__stages">
      ${guide.stages.map((stage) => renderStagePreview(stage)).join("")}
    </div>
  `;
}

function updateOutput() {
  const guide = buildGuide();
  latestJson = `${JSON.stringify(guide, null, 2)}\n`;
  jsonPreview.textContent = latestJson;
  renderGuidePreview(guide);
  downloadButton.disabled = false;
  saveDraft();
}

function downloadJson() {
  const blob = new Blob([latestJson], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "guide.json";
  link.click();
  URL.revokeObjectURL(url);
}

async function copyJson() {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(latestJson);
      submissionStatus.textContent = "guide.json copied. Open a GitHub issue and paste the JSON into the submission form.";
      return;
    }
  } catch {
    // Fall through to selection fallback.
  }

  const selection = window.getSelection();
  const range = document.createRange();
  range.selectNodeContents(jsonPreview);
  selection.removeAllRanges();
  selection.addRange(range);
  submissionStatus.textContent = "Clipboard access was blocked. The JSON preview was selected for manual copy.";
}

function detectRepositoryUrl() {
  const { hostname, pathname } = window.location;

  if (hostname.endsWith(".github.io")) {
    const owner = hostname.slice(0, hostname.indexOf(".github.io"));
    const repo = pathname.split("/").filter(Boolean)[0];
    if (owner && repo) {
      return `https://github.com/${owner}/${repo}`;
    }
  }

  if (hostname === "github.com") {
    const [owner, repo] = pathname.split("/").filter(Boolean);
    if (owner && repo) {
      return `https://github.com/${owner}/${repo}`;
    }
  }

  return null;
}

function openIssuePage() {
  const repositoryUrl = detectRepositoryUrl();
  if (!repositoryUrl) {
    submissionStatus.textContent = "Repository URL was not detected here. Open your TerraPath GitHub repository and create a new guide submission issue manually.";
    return;
  }

  window.open(`${repositoryUrl}/issues/new`, "_blank", "noopener");
  submissionStatus.textContent = "GitHub issues opened in a new tab. Choose the guide submission form and paste the copied JSON.";
}

function groupEntriesByMod(entries) {
  const grouped = new Map();
  for (const entry of entries) {
    const modName = String(entry.id || "").split("/")[0] || "Other";
    const group = grouped.get(modName) || [];
    group.push(entry);
    grouped.set(modName, group);
  }
  return grouped;
}

function buildSelectOptions(entries, selectedValue, placeholderLabel) {
  const entryMap = new Map(entries.map((entry) => [entry.id, entry]));
  let markup = `<option value="">${escapeHtml(placeholderLabel)}</option>`;

  if (selectedValue && !entryMap.has(selectedValue)) {
    markup += `<option value="${escapeHtml(selectedValue)}" selected>Unavailable: ${escapeHtml(selectedValue)}</option>`;
  }

  for (const [modName, modEntries] of groupEntriesByMod(entries)) {
    const options = modEntries
      .slice()
      .sort((left, right) => left.displayName.localeCompare(right.displayName))
      .map((entry) => `
        <option value="${escapeHtml(entry.id)}" ${entry.id === selectedValue ? "selected" : ""}>
          ${escapeHtml(entry.displayName)}
        </option>
      `).join("");

    markup += `<optgroup label="${escapeHtml(modName)}">${options}</optgroup>`;
  }

  return markup;
}

function renderBossRows(stage, stageIndex) {
  if (!stage.bossRefs.length) {
    return `<p class="empty-state">No boss references yet.</p>`;
  }

  return stage.bossRefs.map((bossRef, bossIndex) => {
    const entry = resolveEntry(bossRef, supportIndex.bossMap);
    const label = resolveEntryName(bossRef, supportIndex.bossMap);

    return `
      <div class="inline-row inline-row--boss">
        <span class="inline-row__media">${iconMarkup(entry, label)}</span>
        <select
          class="inline-row__fill"
          data-role="boss-id"
          data-stage-index="${stageIndex}"
          data-boss-index="${bossIndex}">
          ${buildSelectOptions(supportIndex.bosses, bossRef, "Choose a boss")}
        </select>
        <button
          class="button button--quiet button--tiny"
          type="button"
          data-action="remove-boss"
          data-stage-index="${stageIndex}"
          data-boss-index="${bossIndex}">
          Remove
        </button>
      </div>
    `;
  }).join("");
}

function renderItemRows(stage, stageIndex) {
  if (!stage.items.length) {
    return `<p class="empty-state">No item picks yet.</p>`;
  }

  return stage.items.map((item, itemIndex) => {
    const entry = resolveEntry(item.itemId, supportIndex.itemMap);
    const label = resolveEntryName(item.itemId, supportIndex.itemMap);

    return `
      <div class="inline-row inline-row--item">
        <span class="inline-row__media">${iconMarkup(entry, label)}</span>
        <select
          class="inline-row__fill"
          data-role="item-id"
          data-stage-index="${stageIndex}"
          data-item-index="${itemIndex}">
          ${buildSelectOptions(supportIndex.items, item.itemId, "Choose an item")}
        </select>
        <select
          data-role="item-category"
          data-stage-index="${stageIndex}"
          data-item-index="${itemIndex}">
          ${CATEGORY_OPTIONS.map((category) => `
            <option value="${category}" ${category === item.category ? "selected" : ""}>${titleCaseCategory(category)}</option>
          `).join("")}
        </select>
        <input
          data-role="item-priority"
          data-stage-index="${stageIndex}"
          data-item-index="${itemIndex}"
          type="number"
          min="0"
          max="100"
          value="${Number(item.priority)}"
          placeholder="50">
        <input
          class="inline-row__fill"
          data-role="item-note"
          data-stage-index="${stageIndex}"
          data-item-index="${itemIndex}"
          value="${escapeHtml(item.note)}"
          placeholder="Optional explanation">
        <button
          class="button button--quiet button--tiny"
          type="button"
          data-action="remove-item"
          data-stage-index="${stageIndex}"
          data-item-index="${itemIndex}">
          Remove
        </button>
      </div>
    `;
  }).join("");
}

function renderStages() {
  stageList.innerHTML = state.stages.map((stage, stageIndex) => `
    <article class="stage-card">
      <div class="stage-card__header">
        <div>
          <p class="eyebrow">Stage ${stageIndex + 1}</p>
          <h3>${escapeHtml(stage.title || `Stage ${stageIndex + 1}`)}</h3>
        </div>
        <div class="stage-card__actions">
          <button class="button button--quiet button--tiny" type="button" data-action="move-stage-up" data-stage-index="${stageIndex}" ${stageIndex === 0 ? "disabled" : ""}>Up</button>
          <button class="button button--quiet button--tiny" type="button" data-action="move-stage-down" data-stage-index="${stageIndex}" ${stageIndex === state.stages.length - 1 ? "disabled" : ""}>Down</button>
          <button class="button button--quiet button--tiny" type="button" data-action="remove-stage" data-stage-index="${stageIndex}" ${state.stages.length === 1 ? "disabled" : ""}>Delete</button>
        </div>
      </div>
      <div class="field-grid field-grid--stage">
        <label class="field">
          <span>Stage title</span>
          <input data-role="stage-title" data-stage-index="${stageIndex}" value="${escapeHtml(stage.title)}" placeholder="Getting Started">
        </label>
        <label class="field field--wide">
          <span>Description</span>
          <textarea data-role="stage-description" data-stage-index="${stageIndex}" rows="4" placeholder="Explain this progression step.">${escapeHtml(stage.description)}</textarea>
        </label>
        <label class="field field--wide">
          <span>Goals, one per line</span>
          <textarea data-role="stage-goals" data-stage-index="${stageIndex}" rows="4" placeholder="Build an arena&#10;Craft mobility items">${escapeHtml(stage.goalsText)}</textarea>
        </label>
        <label class="field field--wide">
          <span>Notes, one per line</span>
          <textarea data-role="stage-notes" data-stage-index="${stageIndex}" rows="3" placeholder="Optional reminders and tips">${escapeHtml(stage.notesText)}</textarea>
        </label>
      </div>
      <section class="subsection">
        <div class="subsection__header">
          <div>
            <h4>Boss references</h4>
            <p class="muted">Choose boss milestones from the curated support index.</p>
          </div>
          <button class="button button--quiet button--tiny" type="button" data-action="add-boss" data-stage-index="${stageIndex}">Add boss</button>
        </div>
        <div class="row-list">
          ${renderBossRows(stage, stageIndex)}
        </div>
      </section>
      <section class="subsection">
        <div class="subsection__header">
          <div>
            <h4>Item picks</h4>
            <p class="muted">Choose curated entries and place them into guide categories.</p>
          </div>
          <button class="button button--quiet button--tiny" type="button" data-action="add-item" data-stage-index="${stageIndex}">Add item</button>
        </div>
        <div class="row-list">
          ${renderItemRows(stage, stageIndex)}
        </div>
      </section>
    </article>
  `).join("");
}

async function tryFetchJson(paths) {
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

  throw new Error("Unable to load support index.");
}

async function loadSupportIndex() {
  try {
    const [itemsData, oresData, bossesData] = await Promise.all([
      tryFetchJson(["supported/Terraria/items.json", "../supported/Terraria/items.json"]),
      tryFetchJson(["supported/Terraria/ores.json", "../supported/Terraria/ores.json"]),
      tryFetchJson(["supported/Terraria/bosses.json", "../supported/Terraria/bosses.json"])
    ]);

    const itemEntries = [
      ...(itemsData.items || []),
      ...((oresData.ores || []).map((ore) => ({ ...ore, category: "ore" })))
    ];
    const bossEntries = bossesData.bosses || [];

    supportIndex = {
      items: itemEntries,
      bosses: bossEntries,
      itemMap: new Map(itemEntries.map((entry) => [entry.id, entry])),
      bossMap: new Map(bossEntries.map((entry) => [entry.id, entry]))
    };

    supportStatus.textContent = `Curated editor support loaded: ${itemEntries.length} Terraria item and ore entries, ${bossEntries.length} Terraria boss entries. Metadata can already mention planned mods such as Calamity and Thorium, while their curated content pickers are still upcoming.`;
  } catch (error) {
    supportStatus.textContent = "Curated support data could not be loaded. The editor still shows saved draft data, but content selectors may be empty.";
    console.error(error);
  }

  renderStages();
  updateOutput();
}

function swapStages(fromIndex, toIndex) {
  const next = [...state.stages];
  const [moved] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moved);
  state.stages = next;
}

function toggleArrayValue(array, value) {
  return array.includes(value)
    ? array.filter((entry) => entry !== value)
    : [...array, value];
}

function handleMetadataChoiceChange(event) {
  const input = event.target;
  if (!(input instanceof HTMLInputElement)) {
    return;
  }

  const group = input.dataset.choiceGroup;
  if (!group) {
    return;
  }

  if (group === "required-mods") {
    state.requiredMods = toggleArrayValue(state.requiredMods, input.value);
    if (!state.requiredMods.length) {
      state.requiredMods = ["Terraria"];
      renderChoiceGroups();
    }
  }

  if (group === "class-tags") {
    state.classTags = toggleArrayValue(state.classTags, input.value);
    if (!state.classTags.length) {
      state.classTags = ["other"];
      renderChoiceGroups();
    }
  }

  if (group === "guide-tags") {
    state.guideTags = toggleArrayValue(state.guideTags, input.value);
  }

  updateOutput();
}

function handleStageAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) {
    return;
  }

  const action = button.dataset.action;
  const stageIndex = Number(button.dataset.stageIndex);
  const itemIndex = Number(button.dataset.itemIndex);
  const bossIndex = Number(button.dataset.bossIndex);
  const stage = state.stages[stageIndex];

  switch (action) {
    case "move-stage-up":
      if (stageIndex > 0) {
        swapStages(stageIndex, stageIndex - 1);
      }
      break;
    case "move-stage-down":
      if (stageIndex < state.stages.length - 1) {
        swapStages(stageIndex, stageIndex + 1);
      }
      break;
    case "remove-stage":
      if (state.stages.length > 1) {
        state.stages.splice(stageIndex, 1);
      }
      break;
    case "add-boss":
      stage.bossRefs.push("");
      break;
    case "remove-boss":
      stage.bossRefs.splice(bossIndex, 1);
      break;
    case "add-item":
      stage.items.push(createItem());
      break;
    case "remove-item":
      stage.items.splice(itemIndex, 1);
      break;
    default:
      return;
  }

  renderStages();
  updateOutput();
}

function updateStageHeading(target, title) {
  const card = target.closest(".stage-card");
  const heading = card?.querySelector("h3");
  if (heading) {
    heading.textContent = title;
  }
}

function handleStageInput(event) {
  const target = event.target;
  const role = target.dataset.role;
  if (!role) {
    return;
  }

  const stageIndex = Number(target.dataset.stageIndex);
  const itemIndex = Number(target.dataset.itemIndex);
  const bossIndex = Number(target.dataset.bossIndex);
  const stage = state.stages[stageIndex];

  switch (role) {
    case "stage-title":
      stage.title = target.value;
      updateStageHeading(target, target.value.trim() || `Stage ${stageIndex + 1}`);
      break;
    case "stage-description":
      stage.description = target.value;
      break;
    case "stage-goals":
      stage.goalsText = target.value;
      break;
    case "stage-notes":
      stage.notesText = target.value;
      break;
    case "boss-id":
      stage.bossRefs[bossIndex] = target.value;
      renderStages();
      break;
    case "item-id": {
      stage.items[itemIndex].itemId = target.value;
      const entry = resolveEntry(target.value, supportIndex.itemMap);
      if (entry?.category) {
        stage.items[itemIndex].category = entry.category;
      }
      renderStages();
      break;
    }
    case "item-category":
      stage.items[itemIndex].category = target.value;
      break;
    case "item-priority":
      stage.items[itemIndex].priority = Math.max(0, Math.min(100, Number(target.value) || 0));
      break;
    case "item-note":
      stage.items[itemIndex].note = target.value;
      break;
    default:
      return;
  }

  updateOutput();
}

function bindMetadataInputs() {
  titleInput.addEventListener("input", () => {
    state.title = titleInput.value;
    updateOutput();
  });

  authorInput.addEventListener("input", () => {
    state.author = authorInput.value;
    updateOutput();
  });

  languageSelect.addEventListener("change", () => {
    state.language = languageSelect.value;
    updateOutput();
  });

  summaryInput.addEventListener("input", () => {
    state.summary = summaryInput.value;
    updateOutput();
  });

  requiredModOptions.addEventListener("change", handleMetadataChoiceChange);
  classTagOptions.addEventListener("change", handleMetadataChoiceChange);
  guideTagOptions.addEventListener("change", handleMetadataChoiceChange);
}

function resetDraft() {
  if (!confirm("Reset the current TerraPath draft?")) {
    return;
  }

  localStorage.removeItem(STORAGE_KEY);
  state = createDefaultState();
  syncMetadataInputs();
  renderStages();
  updateOutput();
}

function init() {
  renderLanguageOptions();
  syncMetadataInputs();
  renderStages();
  bindMetadataInputs();
  stageList.addEventListener("click", handleStageAction);
  stageList.addEventListener("input", handleStageInput);
  stageList.addEventListener("change", handleStageInput);
  addStageButton.addEventListener("click", () => {
    state.stages.push(createStage({ title: `Stage ${state.stages.length + 1}` }));
    renderStages();
    updateOutput();
  });
  copyJsonButton.addEventListener("click", copyJson);
  openIssueButton.addEventListener("click", openIssuePage);
  resetDraftButton.addEventListener("click", resetDraft);
  downloadButton.addEventListener("click", downloadJson);
  updateOutput();
  loadSupportIndex();
}

init();
