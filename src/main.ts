import SWIPL from "swipl-wasm";
import { loop_scene } from "./diagram/scene";
import { create_editor, Editor } from "./editor/editor";
import { State } from "./State";
import "./style.css";
import { create_el } from "./utilities/utilities";

const file_picker_button = create_el("button", "file-picker-button", document.body);
file_picker_button.innerText = "Choose save folder";

const editors_container = create_el("div", "editors-container", document.body);

const SPEC_PATHS = ["chrome_tabs.pl", "ios_tabs.pl"];

async function setup() {
  /* -------------------- Header editor ------------------- */
  State.header_editor = create_editor("Header", await (await fetch("./interface-schema/header.pl")).text());

  /* ---------------- Specification editor ---------------- */
  State.spec_editors = await Promise.all(
    SPEC_PATHS.map(async (spec) =>
      create_editor(spec, await (await fetch(`./interface-schema/specifications/${spec}`)).text()),
    ),
  );

  State.spec_editors.forEach((editor) => editors_container.append(editor.parent));

  /* --------------- Design patterns editor --------------- */
  State.design_patterns_editor = create_editor(
    "Design Patterns",
    // TODO: combine patterns in the folder
    await (await fetch("./interface-schema/design-patterns/history.pl")).text(),
  );

  /* -------------------- Rules editor -------------------- */
  State.rules_editor = create_editor("Rules", await (await fetch("./interface-schema/rules.pl")).text());

  /* -------------------- Query editor -------------------- */
  State.query_editor = create_editor("Query", `X subsets Y.`);
  State.query_editor.parent.classList.add("query-editor");

  // Output(s)
  State.query_output = create_el("div", "editor-output", State.query_editor.parent);

  // SWIPL WASM setup
  State.swipl = await SWIPL({ arguments: ["-q"] });

  // Diagram view
  // State.scene = create_scene(State.spec_editor.parent);

  // Live programming
  let typingTimer: any | null;

  State.spec_editors.map((editor) =>
    editor.editor_view.dom.addEventListener("change", (_) => {
      if (typingTimer != null) clearTimeout(typingTimer);
      typingTimer = setTimeout(() => update(editor), 1000); // Should this be synchronous?
    }),
  );
}

async function update(from: Editor) {
  if (State.file_system_handle != null) {
    const file_handle = await State.file_system_handle.getFileHandle(from.path, { create: true });

    // Create a FileSystemWritableFileStream to write to.
    const writable = await file_handle.createWritable();

    // Write the contents of the file to the stream.
    const raw = from.editor_view.state.doc.toString();
    await writable.write(raw);
    await writable.close();
  } else {
    alert("Note: file not being saved. Please select a folder.");
  }

  // await execute_prolog();
}

async function main() {
  // Write out the file
  file_picker_button.addEventListener("click", async () => {
    State.file_system_handle = await window.showDirectoryPicker();
  });

  await setup();

  // Initial execute
  // await update();
}

async function loop() {
  if (State.scene != null) loop_scene(State.scene);

  requestAnimationFrame(loop);
}

main();
loop();
