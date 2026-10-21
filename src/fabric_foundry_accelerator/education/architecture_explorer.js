"use strict";
document.addEventListener("DOMContentLoaded", () => {
  for (const root of document.querySelectorAll("[data-explorer]")) {
    const {view, components} = JSON.parse(root.querySelector("[data-architecture]").textContent);
    const inspector = root.querySelector(".arch-inspector");
    const cue = root.querySelector(".arch-cue");
    const traceSelect = root.querySelector("[data-trace]");
    const layer = root.querySelector("[data-layer]");
    const level = root.querySelector("[data-level]");
    let selected = null;
    let hop = -1;
    const byId = new Map(view.nodes.map(node => [node.id, node]));
    const activeTrace = () => view.traces.find(trace => trace.id === traceSelect.value);
    function paragraph(title, text) {
      const heading = document.createElement("h4");
      heading.textContent = title;
      const body = document.createElement("p");
      body.textContent = text;
      inspector.append(heading, body);
    }
    function inspect(id) {
      selected = id;
      const node = byId.get(id);
      const component = components[node.component];
      inspector.replaceChildren();
      paragraph(node.label, `${node.state} · ${component?.status ?? node.kind}`);
      paragraph("What it is and why it matters", component?.description[level.value] ?? node.summary);
      if (node.summary && component) paragraph("Role in this workflow", node.summary);
      if (component) {
        paragraph("Owns", component.owns.join("; "));
        paragraph("Does not own", component.does_not_own.join("; ") || "No additional exclusions documented.");
        paragraph("Offline equivalent", component.offline_equivalent);
      }
      if (node.repo_path) paragraph("Implementation", node.repo_path);
      paragraph("Connections — drill into a neighbor", "Follow an incoming or outgoing boundary below.");
      for (const edge of view.edges.filter(edge => edge.source === id || edge.target === id)) {
        const target = edge.source === id ? edge.target : edge.source;
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = `${edge.source === id ? "To" : "From"} ${byId.get(target).label}: ${edge.label || edge.kind} (${edge.kind}${edge.planned ? ", planned" : ""})`;
        button.addEventListener("click", () => {hop = -1; inspect(target); update();});
        const row = document.createElement("p");
        row.append(button);
        inspector.append(row);
      }
      const sources = [...new Set([...node.sources, ...(component?.sources ?? [])])];
      if (sources.length) paragraph("Sources", sources.join(", "));
      paragraph("Evidence boundary", "This is an architecture explanation, not a new tool invocation. Validate identity, exact target, approval and persisted output separately.");
      for (const box of root.querySelectorAll("[data-node]")) {
        box.setAttribute("aria-pressed", String(box.dataset.node === id));
      }
    }
    function update() {
      const trace = activeTrace();
      const current = trace?.steps[hop];
      const order = view.steps.map(step => step.id);
      const visible = node => !layer.value || !node.step || order.indexOf(node.step) <= order.indexOf(layer.value);
      const shown = new Set(view.nodes.filter(visible).map(node => node.id));
      for (const box of root.querySelectorAll("[data-node]")) {
        box.style.display = shown.has(box.dataset.node) ? "" : "none";
        box.classList.toggle("arch-dim", Boolean(current) && box.dataset.node !== current.node);
      }
      for (const edge of view.edges) {
        const path = root.querySelector(`[data-edge="${edge.id}"]`);
        path.parentElement.style.display = shown.has(edge.source) && shown.has(edge.target) && visible(edge) ? "" : "none";
        path.classList.toggle("arch-active", current?.edge === edge.id);
      }
      for (const zone of view.zones) {
        root.querySelector(`[data-zone="${zone.id}"]`).style.display = visible(zone) ? "" : "none";
      }
      cue.textContent = current
        ? `${trace.label} / ${trace.title} / hop ${hop + 1} of ${trace.steps.length}. ${trace.summary} ${current.say} ${current.note}`
        : view.steps.find(step => step.id === layer.value)?.cue ?? trace?.summary ?? view.cue;
      root.querySelector("[data-start]").disabled = !trace;
      root.querySelector("[data-back]").disabled = hop <= 0;
      root.querySelector("[data-next]").disabled = !trace || hop < 0 || hop >= trace.steps.length - 1;
    }
    function go(next) {
      const trace = activeTrace();
      if (!trace || next < 0 || next >= trace.steps.length) return;
      layer.value = "";
      hop = next;
      inspect(trace.steps[hop].node);
      update();
      const node = root.querySelector(`[data-node="${trace.steps[hop].node}"]`);
      node.scrollIntoView({block:"nearest",inline:"center"});
    }
    for (const box of root.querySelectorAll("[data-node]")) {
      const activate = () => {hop = -1; inspect(box.dataset.node); update();};
      box.addEventListener("click", activate);
      box.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") {event.preventDefault(); activate();}
      });
    }
    for (const button of root.querySelectorAll("[data-inspect]")) {
      button.addEventListener("click", () => {hop = -1; inspect(button.dataset.inspect); update();});
    }
    for (const button of root.querySelectorAll("[data-hop]")) {
      button.addEventListener("click", () => {traceSelect.value = button.dataset.path; go(Number(button.dataset.hop));});
    }
    root.querySelector("[data-start]").addEventListener("click", () => go(0));
    root.querySelector("[data-back]").addEventListener("click", () => go(hop - 1));
    root.querySelector("[data-next]").addEventListener("click", () => go(hop + 1));
    root.querySelector("[data-reset]").addEventListener("click", () => {
      hop = -1; selected = null; layer.value = "";
      inspector.textContent = "Select a component to explore it.";
      for (const box of root.querySelectorAll("[data-node]")) box.setAttribute("aria-pressed","false");
      update();
    });
    traceSelect.addEventListener("change", () => {hop = -1; update();});
    layer.addEventListener("change", () => {hop = -1; update();});
    level.addEventListener("change", () => {if (selected) inspect(selected);});
    update();
  }
});
