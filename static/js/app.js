"use strict";

document.querySelectorAll(".progress-bar").forEach((bar) => {
  const percentage = Number.parseFloat(bar.style.width) || 0;
  bar.parentElement.setAttribute("role", "progressbar");
  bar.parentElement.setAttribute("aria-label", "Learning progress");
  bar.parentElement.setAttribute("aria-valuemin", "0");
  bar.parentElement.setAttribute("aria-valuemax", "100");
  bar.parentElement.setAttribute("aria-valuenow", String(percentage));
});

const titleInput = document.querySelector("#id_title");
const slugInput = document.querySelector("#id_slug");
if (titleInput && slugInput) {
  let manualSlug = Boolean(slugInput.value);
  slugInput.addEventListener("input", () => { manualSlug = true; });
  titleInput.addEventListener("input", () => {
    if (!manualSlug) slugInput.value = titleInput.value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  });
}

const timer = document.querySelector("[data-deadline]");
if (timer) {
  const deadline = Date.parse(timer.dataset.deadline);
  const tick = () => {
    const seconds = Math.max(0, Math.floor((deadline - Date.now()) / 1000));
    timer.textContent = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")} remaining`;
    if (seconds === 0) {
      clearInterval(interval);
      document.querySelector("#quiz-form").submit();
    }
  };
  const interval = setInterval(tick, 1000);
  tick();
}
