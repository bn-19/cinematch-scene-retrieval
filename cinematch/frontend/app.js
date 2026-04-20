const queryInput = document.getElementById("query-input");
const searchBtn = document.getElementById("search-btn");
const resultsDiv = document.getElementById("results");
const statusDiv = document.getElementById("status");

// ── Lightbox ─────────────────────────────────────────────
const lightbox = document.createElement("div");
lightbox.id = "lightbox";
lightbox.innerHTML = `
  <div class="lb-backdrop"></div>
  <div class="lb-content">
    <button class="lb-close">✕</button>
    <img class="lb-img" src="" alt="" />
    <div class="lb-info">
      <div class="lb-title"></div>
      <div class="lb-meta"></div>
      <div class="lb-desc"></div>
      <div class="lb-tags"></div>
      <div class="lb-score"></div>
    </div>
  </div>
`;
document.body.appendChild(lightbox);

function openLightbox(scene) {
    const info = getFilmInfo(scene);
    lightbox.querySelector(".lb-img").src = "/images/" + encodeURIComponent(scene.filename);
    lightbox.querySelector(".lb-title").textContent = info.title;
    lightbox.querySelector(".lb-meta").textContent = info.meta;
    lightbox.querySelector(".lb-desc").textContent = info.isFilm ? scene.description : "";
    lightbox.querySelector(".lb-score").textContent = (scene.similarity * 100).toFixed(1) + "% match";

    const tagsEl = lightbox.querySelector(".lb-tags");
    tagsEl.innerHTML = "";
    scene.tone_tags.split(", ").forEach(function (tag) {
        const span = document.createElement("span");
        span.className = "tone-tag";
        span.textContent = tag;
        tagsEl.appendChild(span);
    });

    lightbox.classList.add("open");
    document.body.style.overflow = "hidden";
}

function closeLightbox() {
    lightbox.classList.remove("open");
    document.body.style.overflow = "";
    lightbox.querySelector(".lb-img").src = "";
}

lightbox.querySelector(".lb-close").addEventListener("click", closeLightbox);
lightbox.querySelector(".lb-backdrop").addEventListener("click", closeLightbox);
document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeLightbox();
});

// ── Card ─────────────────────────────────────────────────
function getFilmInfo(scene) {
    if (scene.film_title && scene.director) {
        return {
            isFilm: true,
            title: scene.film_title + " (" + scene.year + ")",
            meta: "Dir. " + scene.director + (scene.timestamp ? "  ·  " + scene.timestamp : ""),
        };
    }
    return {
        isFilm: false,
        title: "Reference Image",
        meta: scene.description,
    };
}

function createSceneCard(scene) {
    const card = document.createElement("div");
    card.className = "scene-card";
    card.title = "Click to view fullscreen";

    const imgWrap = document.createElement("div");
    imgWrap.className = "card-img-wrap";

    const img = document.createElement("img");
    img.src = "/images/" + encodeURIComponent(scene.filename);
    img.alt = scene.source;
    img.loading = "lazy";

    const expandHint = document.createElement("div");
    expandHint.className = "expand-hint";
    expandHint.textContent = "⤢";

    imgWrap.appendChild(img);
    imgWrap.appendChild(expandHint);
    card.appendChild(imgWrap);

    card.addEventListener("click", function () { openLightbox(scene); });

    const body = document.createElement("div");
    body.className = "card-body";

    const info = getFilmInfo(scene);

    const titleEl = document.createElement("div");
    titleEl.className = "source" + (info.isFilm ? " film-title" : " ref-label");
    titleEl.textContent = info.title;
    body.appendChild(titleEl);

    const metaEl = document.createElement("div");
    metaEl.className = "description";
    metaEl.textContent = info.meta;
    body.appendChild(metaEl);

    const footer = document.createElement("div");
    footer.className = "card-footer";

    const sim = document.createElement("div");
    sim.className = "similarity";
    sim.textContent = (scene.similarity * 100).toFixed(1) + "% match";
    footer.appendChild(sim);

    const tagsDiv = document.createElement("div");
    tagsDiv.className = "tone-tags";
    scene.tone_tags.split(", ").slice(0, 2).forEach(function (tag) {
        const span = document.createElement("span");
        span.className = "tone-tag";
        span.textContent = tag;
        tagsDiv.appendChild(span);
    });
    footer.appendChild(tagsDiv);

    body.appendChild(footer);
    card.appendChild(body);
    return card;
}

async function search() {
    const query = queryInput.value.trim();
    if (!query) return;

    searchBtn.disabled = true;
    statusDiv.textContent = "Searching...";
    resultsDiv.textContent = "";

    try {
        const resp = await fetch("/api/search?q=" + encodeURIComponent(query));
        if (!resp.ok) throw new Error("Server error: " + resp.status);
        const data = await resp.json();

        if (data.results.length === 0) {
            const noResults = document.createElement("div");
            noResults.className = "no-results";
            noResults.textContent = "No matching scenes found. Try a different description.";
            resultsDiv.appendChild(noResults);
            statusDiv.textContent = "";
            return;
        }

        statusDiv.textContent = "Top " + data.results.length + " matches for \"" + data.query + "\"";

        data.results.forEach(function (scene) {
            resultsDiv.appendChild(createSceneCard(scene));
        });
    } catch (err) {
        statusDiv.textContent = "Error: " + err.message;
    } finally {
        searchBtn.disabled = false;
    }
}

searchBtn.addEventListener("click", search);
queryInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") search();
});
