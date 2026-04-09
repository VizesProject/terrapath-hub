const form = document.querySelector("#guideForm");
const preview = document.querySelector("#jsonPreview");
const downloadButton = document.querySelector("#downloadButton");

let latestJson = "{}";

function slugify(value) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "new-guide";
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

function buildGuide(formData) {
  const title = String(formData.get("title") || "");
  const requiredMod = String(formData.get("requiredMod") || "Terraria");
  const classTag = String(formData.get("classTag") || "melee").toLowerCase();
  const stageTitle = String(formData.get("stageTitle") || "Getting Started");

  return {
    schemaVersion: 1,
    id: slugify(`${requiredMod}-${classTag}-${title}`),
    title,
    author: String(formData.get("author") || ""),
    language: String(formData.get("language") || "en-US"),
    summary: String(formData.get("summary") || ""),
    requiredMods: [requiredMod],
    classTags: [classTag],
    guideTags: ["draft"],
    createdAt: today(),
    updatedAt: today(),
    stages: [
      {
        id: slugify(stageTitle).slice(0, 40),
        title: stageTitle,
        description: String(formData.get("stageDescription") || ""),
        bossRefs: [],
        goals: [],
        items: [],
        notes: []
      }
    ]
  };
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

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const guide = buildGuide(new FormData(form));
  latestJson = JSON.stringify(guide, null, 2);
  preview.textContent = latestJson;
  downloadButton.disabled = false;
});

downloadButton.addEventListener("click", downloadJson);
