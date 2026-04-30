const queryInput = document.getElementById("query-input");
const searchBtn = document.getElementById("search-btn");
const resultsDiv = document.getElementById("results");
const statusText = document.getElementById("status-text");
const newSearchBtn = document.getElementById("new-search-btn");
const presentToggle = document.getElementById("present-toggle");

let lastSearchQuery = "";
let searchSequence = 0;
let searchStatusTimer = null;

newSearchBtn.addEventListener("click", function () {
    window.clearTimeout(searchStatusTimer);
    resultsDiv.textContent = "";
    statusText.textContent = "";
    newSearchBtn.style.display = "none";
    queryInput.value = "";
    queryInput.focus();
});

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
      <div class="lb-frame"></div>
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
    lightbox.querySelector(".lb-frame").textContent = getFrameLabel(scene, true);

    const tagsEl = lightbox.querySelector(".lb-tags");
    tagsEl.innerHTML = "";
    getToneTags(scene).forEach(function (tag) {
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

// ── Search feedback ─────────────────────────────────────
function saveFeedback(rating) {
    const feedback = {
        query: lastSearchQuery,
        rating: rating,
        created_at: new Date().toISOString(),
    };
    let savedFeedback = [];
    try {
        savedFeedback = JSON.parse(localStorage.getItem("cinematch_feedback") || "[]");
    } catch (err) {
        savedFeedback = [];
    }
    savedFeedback.push(feedback);
    localStorage.setItem("cinematch_feedback", JSON.stringify(savedFeedback.slice(-25)));
}

function createFeedbackBar() {
    const bar = document.createElement("div");
    bar.className = "feedback-bar";
    bar.setAttribute("aria-label", "Rate these results");

    const kicker = document.createElement("div");
    kicker.className = "feedback-kicker";
    kicker.textContent = "Quick rating";
    bar.appendChild(kicker);

    const titleEl = document.createElement("div");
    titleEl.className = "feedback-bar-title";
    titleEl.textContent = "Are you satisfied with these results?";
    bar.appendChild(titleEl);

    const scale = document.createElement("div");
    scale.className = "feedback-scale";
    scale.setAttribute("aria-label", "Rate results from 1 to 5 stars");

    const starMeta = [
        { rating: 1, label: "1 star, not satisfied" },
        { rating: 2, label: "2 stars" },
        { rating: 3, label: "3 stars" },
        { rating: 4, label: "4 stars" },
        { rating: 5, label: "5 stars, very satisfied" },
    ];
    const starBtns = starMeta.map(function (meta) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "star-btn";
        btn.dataset.rating = String(meta.rating);
        btn.setAttribute("aria-label", meta.label);
        btn.textContent = "★";
        scale.appendChild(btn);
        return btn;
    });
    bar.appendChild(scale);

    const labelsEl = document.createElement("div");
    labelsEl.className = "feedback-labels";
    const labelLeft = document.createElement("span");
    labelLeft.textContent = "Not satisfied";
    const labelRight = document.createElement("span");
    labelRight.textContent = "Very satisfied";
    labelsEl.appendChild(labelLeft);
    labelsEl.appendChild(labelRight);
    bar.appendChild(labelsEl);

    const thanks = document.createElement("div");
    thanks.className = "feedback-thanks";
    thanks.setAttribute("aria-live", "polite");
    bar.appendChild(thanks);

    function setRating(rating) {
        starBtns.forEach(function (s) {
            s.classList.toggle("selected", Number(s.dataset.rating) <= rating);
        });
    }

    starBtns.forEach(function (star) {
        star.addEventListener("mouseenter", function () { setRating(Number(star.dataset.rating)); });
        star.addEventListener("focus", function () { setRating(Number(star.dataset.rating)); });
        star.addEventListener("click", function () {
            const rating = Number(star.dataset.rating);
            setRating(rating);
            saveFeedback(rating);
            thanks.textContent = "Thanks. Your rating helps tune the scene matching experience.";
            starBtns.forEach(function (s) { s.disabled = true; });
        });
    });

    scale.addEventListener("mouseleave", function () {
        if (!thanks.textContent) setRating(0);
    });

    return bar;
}

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

function getToneTags(scene) {
    if (Array.isArray(scene.tone_tags)) return scene.tone_tags;
    if (typeof scene.tone_tags === "string" && scene.tone_tags) {
        return scene.tone_tags.split(", ").filter(Boolean);
    }
    return [];
}

function getFrameLabel(scene, includeFile) {
    const parts = [];
    if (scene.timestamp) parts.push("Time " + scene.timestamp);
    if (scene.id) parts.push("Frame ID " + scene.id);
    if (includeFile && scene.filename) parts.push("File " + scene.filename);
    return parts.join("  ·  ");
}

function isPresentationMode() {
    return document.body.classList.contains("presentation-mode");
}

function setPresentationMode(enabled, persist) {
    document.body.classList.toggle("presentation-mode", enabled);
    presentToggle.setAttribute("aria-pressed", enabled ? "true" : "false");
    presentToggle.textContent = enabled ? "Exit Present" : "Present";
    if (persist) {
        localStorage.setItem("cinematch_presentation_mode", enabled ? "1" : "0");
        const url = new URL(window.location.href);
        if (enabled) {
            url.searchParams.set("present", "1");
        } else {
            url.searchParams.delete("present");
        }
        window.history.replaceState({}, "", url);
    }
}

function loadPresentationPreference() {
    const params = new URLSearchParams(window.location.search);
    if (params.get("present") === "1") {
        setPresentationMode(true, false);
        return;
    }
    setPresentationMode(localStorage.getItem("cinematch_presentation_mode") === "1", false);
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

    const frameEl = document.createElement("div");
    frameEl.className = "frame-meta";
    frameEl.textContent = getFrameLabel(scene, false);
    body.appendChild(frameEl);

    const footer = document.createElement("div");
    footer.className = "card-footer";

    const sim = document.createElement("div");
    sim.className = "similarity";
    sim.textContent = (scene.similarity * 100).toFixed(1) + "% match";
    footer.appendChild(sim);

    const tagsDiv = document.createElement("div");
    tagsDiv.className = "tone-tags";
    getToneTags(scene).slice(0, 2).forEach(function (tag) {
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
    if (!query) {
        statusText.textContent = "Choose a demo query or describe a scene to search.";
        queryInput.focus();
        return;
    }
    const currentSearch = searchSequence + 1;
    searchSequence = currentSearch;

    searchBtn.disabled = true;
    newSearchBtn.style.display = "none";
    statusText.textContent = "Encoding query with CLIP. Waking Spaces can take 30-60 seconds.";
    resultsDiv.textContent = "";
    window.clearTimeout(searchStatusTimer);
    searchStatusTimer = window.setTimeout(function () {
        if (searchSequence === currentSearch) {
            statusText.textContent = "Still working. The model may be loading after a cold start.";
        }
    }, 8000);

    try {
        const resp = await fetch("/api/search?q=" + encodeURIComponent(query));
        if (!resp.ok) throw new Error("Server error: " + resp.status);
        const data = await resp.json();

        if (data.results.length === 0) {
            const noResults = document.createElement("div");
            noResults.className = "no-results";
            noResults.textContent = "No matching scenes found. Try a different description.";
            resultsDiv.appendChild(noResults);
            statusText.textContent = "";
            return;
        }

        statusText.textContent = "Top " + data.results.length + " matches for \"" + data.query + "\"";
        newSearchBtn.style.display = "inline-flex";
        lastSearchQuery = data.query;

        data.results.forEach(function (scene) {
            resultsDiv.appendChild(createSceneCard(scene));
        });
        resultsDiv.appendChild(createFeedbackBar());
    } catch (err) {
        statusText.textContent = "Error: " + err.message;
    } finally {
        window.clearTimeout(searchStatusTimer);
        searchBtn.disabled = false;
    }
}

searchBtn.addEventListener("click", search);
queryInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") search();
});

document.querySelectorAll("[data-query]").forEach(function (button) {
    button.addEventListener("click", function () {
        queryInput.value = button.dataset.query;
        search();
    });
});

presentToggle.addEventListener("click", function () {
    setPresentationMode(!isPresentationMode(), true);
});

loadPresentationPreference();
