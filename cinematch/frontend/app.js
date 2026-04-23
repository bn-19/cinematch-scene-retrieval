const queryInput = document.getElementById("query-input");
const searchBtn = document.getElementById("search-btn");
const resultsDiv = document.getElementById("results");
const statusDiv = document.getElementById("status");

let lastSearchQuery = "";
let searchSequence = 0;

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
    if (e.key === "Escape") {
        closeLightbox();
        closeFeedbackModal();
    }
});

// ── Search feedback ─────────────────────────────────────
const feedbackModal = document.createElement("div");
feedbackModal.id = "feedback-modal";
feedbackModal.setAttribute("aria-hidden", "true");
feedbackModal.innerHTML = `
  <div class="feedback-backdrop"></div>
  <div class="feedback-content" role="dialog" aria-modal="true" aria-labelledby="feedback-title">
    <button class="feedback-close" aria-label="Close feedback">✕</button>
    <div class="feedback-kicker">Quick rating</div>
    <div id="feedback-title" class="feedback-title">Are you satisfied with these results?</div>
    <div class="feedback-scale" aria-label="Rate results from 1 to 5 stars">
      <button type="button" class="star-btn" data-rating="1" aria-label="1 star, not satisfied">★</button>
      <button type="button" class="star-btn" data-rating="2" aria-label="2 stars">★</button>
      <button type="button" class="star-btn" data-rating="3" aria-label="3 stars">★</button>
      <button type="button" class="star-btn" data-rating="4" aria-label="4 stars">★</button>
      <button type="button" class="star-btn" data-rating="5" aria-label="5 stars, very satisfied">★</button>
    </div>
    <div class="feedback-labels">
      <span>Not satisfied</span>
      <span>Very satisfied</span>
    </div>
    <div class="feedback-thanks" aria-live="polite"></div>
  </div>
`;
document.body.appendChild(feedbackModal);

const feedbackStars = feedbackModal.querySelectorAll(".star-btn");
const feedbackThanks = feedbackModal.querySelector(".feedback-thanks");

function setFeedbackRating(rating) {
    feedbackStars.forEach(function (star) {
        const starRating = Number(star.dataset.rating);
        star.classList.toggle("selected", starRating <= rating);
    });
}

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

function openFeedbackModal() {
    feedbackThanks.textContent = "";
    setFeedbackRating(0);
    feedbackModal.classList.add("open");
    feedbackModal.setAttribute("aria-hidden", "false");
}

function closeFeedbackModal() {
    feedbackModal.classList.remove("open");
    feedbackModal.setAttribute("aria-hidden", "true");
}

feedbackModal.querySelector(".feedback-close").addEventListener("click", closeFeedbackModal);
feedbackModal.querySelector(".feedback-backdrop").addEventListener("click", closeFeedbackModal);

feedbackStars.forEach(function (star) {
    star.addEventListener("mouseenter", function () {
        setFeedbackRating(Number(star.dataset.rating));
    });
    star.addEventListener("focus", function () {
        setFeedbackRating(Number(star.dataset.rating));
    });
    star.addEventListener("click", function () {
        const rating = Number(star.dataset.rating);
        setFeedbackRating(rating);
        saveFeedback(rating);
        feedbackThanks.textContent = "Thanks. Your rating helps tune the scene matching experience.";
        window.setTimeout(closeFeedbackModal, 900);
    });
});

feedbackModal.querySelector(".feedback-scale").addEventListener("mouseleave", function () {
    if (!feedbackThanks.textContent) setFeedbackRating(0);
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
    const currentSearch = searchSequence + 1;
    searchSequence = currentSearch;

    searchBtn.disabled = true;
    closeFeedbackModal();
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
        lastSearchQuery = data.query;

        data.results.forEach(function (scene) {
            resultsDiv.appendChild(createSceneCard(scene));
        });
        window.setTimeout(function () {
            if (searchSequence === currentSearch) openFeedbackModal();
        }, 450);
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
