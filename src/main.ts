import SWIPL from "swipl-wasm";
import { setup_bloom } from "./bloom";
import { create_default_editor } from "./editor/editor";
import { execute_prolog } from "./prolog";
import { State } from "./State";
import "./style.css";
import { create_el } from "./utilities";

async function setup() {
  // Spec editor
  const { editor: spec_editor, parent: spec_parent } = create_default_editor(
    "Specification",
    await (await fetch("./spec.txt")).text()
  );
  spec_parent.classList.add("spec-editor");
  State.spec_editor = spec_editor;

  // Query editor
  const { editor: query_editor, parent: query_parent } = create_default_editor(
    "Query",
    `objects(X).`
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
