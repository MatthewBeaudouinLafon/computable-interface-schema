import SWIPL from "swipl-wasm";
import { setup_bloom } from "./bloom";
import { create_default_editor } from "./editor/editor";
import { execute_prolog } from "./prolog";
import { State } from "./State";
import "./style.css";
import { create_el } from "./utilities";

async function setup() {
  // Header editor
  // TODO: hide when in some kind of user facing mode.
  const { editor: header_editor, parent: header_parent } = create_default_editor(
    "Header",
    await (await fetch("./interface-schema/header.pl")).text()
  );
  header_parent.classList.add("spec-editor");
  State.header_editor = header_editor;

  // Spec editor
  const { editor: spec_editor, parent: spec_parent } = create_default_editor(
    "Specification",
    // TODO: make dropdown for different default specs.
    await (await fetch("./interface-schema/specifications/web-browser.pl")).text(),
    true
  );
  spec_parent.classList.add("spec-editor");
  State.spec_editor = spec_editor;

  // design patterns editor
  // TODO: hide when in some kind of user facing mode.
  const { editor: design_patterns_editor, parent: design_patterns_parent } = create_default_editor(
    "Design Patterns",
    // TODO: combine patterns in the folder
    await (await fetch("./interface-schema/design-patterns/history.pl")).text()
  );
  design_patterns_parent.classList.add("spec-editor");
  State.design_patterns_editor = design_patterns_editor;

  // rules editor
  // TODO: hide when in some kind of user facing mode.
  const { editor: rules_editor, parent: rules_parent } = create_default_editor(
    "Rules",
    await (await fetch("./interface-schema/rules.pl")).text()
  );
  rules_parent.classList.add("spec-editor");
  State.rules_editor = rules_editor;

  // Query editor
  const { editor: query_editor, parent: query_parent } = create_default_editor(
    "Query",
    `objects(X).`,
    true
  );
  query_parent.classList.add("query-editor");
  State.query_editor = query_editor;

  // Output(s)
  State.spec_output = create_el("div", "editor-output", spec_parent);
  State.query_output = create_el("div", "editor-output", query_parent);

  // Diagram output
  State.diagram_output = create_el("div", "diagram-output", document.body);

  // SWIPL WASM setup
  State.swipl = await SWIPL({ arguments: ["-q"] });

  // Live programming
  let typingTimer: any | null;

  spec_editor.dom.addEventListener("change", (_) => {
    if (typingTimer != null) clearTimeout(typingTimer);
    typingTimer = setTimeout(() => execute_prolog(), 1000); // Should this be synchronous?
  });

  query_editor.dom.addEventListener("change", (_) => {
    if (typingTimer != null) clearTimeout(typingTimer);
    typingTimer = setTimeout(() => execute_prolog(), 1000);
  });
}

async function main() {
  await setup();

  // Initial execute
  await execute_prolog();

  // Setup bloom
  await setup_bloom();
}

main();
