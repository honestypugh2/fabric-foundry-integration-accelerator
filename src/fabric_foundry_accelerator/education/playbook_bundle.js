"use strict";
(() => {
  const frames = [...document.querySelectorAll("iframe[data-page]")];
  const pages = new Map(frames.map(frame => [frame.dataset.page, frame]));
  const aliases = new Map([
    ["docs/field-playbooks/customer.html", "customer"],
    ["docs/field-playbooks/se-developer.html", "se-developer"],
    ["demos/fabric-copilot-level-up/index.html", "fabric-engineering"],
    ["demos/foundry-fabric-agents-workshop/index.html", "foundry-agents"],
  ]);
  const repository = "https://github.com/honestypugh2/fabric-foundry-integration-accelerator/blob/main/";
  const search = document.getElementById("search");
  const results = document.getElementById("results");
  const status = document.getElementById("search-status");
  const index = new Map();
  const prepared = new WeakSet();
  function showPage(focus = false) {
    const [requested, anchor] = location.hash.slice(1).split("/");
    const key = pages.has(requested) ? requested : document.body.dataset.audience;
    for (const [id, frame] of pages) {
      frame.parentElement.hidden = id !== key;
    }
    for (const link of document.querySelectorAll("nav [data-page]")) {
      link.setAttribute("aria-current", link.dataset.page === key ? "page" : "false");
    }
    const frame = pages.get(key);
    if (focus) frame.parentElement.querySelector("h2").focus();
    if (anchor) frame.contentDocument?.getElementById(anchor)?.scrollIntoView();
  }
  function searchContents() {
    results.replaceChildren();
    const query = search.value.trim().toLocaleLowerCase();
    if (!query) {
      status.textContent = "";
      return;
    }
    const matches = [...index.values()].flat().filter(entry => entry.text.toLocaleLowerCase().includes(query));
    status.textContent = `${matches.length} matching sections. ${Math.min(matches.length, 30)} shown.`;
    for (const entry of matches.slice(0, 30)) {
      const item = document.createElement("li");
      const link = document.createElement("a");
      link.href = `#${entry.page}/${entry.anchor}`;
      link.textContent = `${pages.get(entry.page).title} / ${entry.title}`;
      const excerpt = document.createElement("p");
      const start = Math.max(0, entry.text.toLocaleLowerCase().indexOf(query) - 60);
      excerpt.textContent = `${start ? "..." : ""}${entry.text.slice(start, start + 220)}...`;
      item.append(link, excerpt);
      results.append(item);
    }
  }
  function prepare(frame) {
    const content = frame.contentDocument;
    if (!content?.body || content.URL === "about:blank" || prepared.has(content)) return;
    prepared.add(content);
    for (const link of content.querySelectorAll("a[href]")) {
      const href = link.getAttribute("href");
      const relative = href.startsWith(repository) ? href.slice(repository.length) : null;
      const [path, anchor] = relative?.split("#") ?? [];
      const target = aliases.get(path);
      if (target) {
        link.addEventListener("click", event => {
          event.preventDefault();
          location.hash = `${target}${anchor ? `/${anchor}` : ""}`;
          showPage(true);
        });
      } else if (href.startsWith("https://") || href.startsWith("http://")) {
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.append(document.createTextNode(" (online reference, new tab)"));
      }
    }
    index.set(frame.dataset.page, [...content.querySelectorAll("section[id],h2[id]")].map(section => ({
      page: frame.dataset.page,
      anchor: section.id,
      title: section.querySelector("h2,h3")?.textContent ?? section.id,
      text: section.textContent.replace(/\s+/g, " ").trim(),
    })));
    searchContents();
    showPage();
  }
  for (const frame of frames) {
    frame.addEventListener("load", () => prepare(frame), {once: true});
    if (frame.contentDocument?.readyState === "complete") prepare(frame);
  }
  search.addEventListener("input", searchContents);
  window.addEventListener("hashchange", () => showPage(true));
  showPage();
})();
