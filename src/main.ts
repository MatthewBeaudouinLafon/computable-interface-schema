import SWIPL from "swipl-wasm";
import { create_editor_alt, Editor } from "./editor/editor";
import { parse } from "./parser/parser";
import { State } from "./State";
import "./style.css";
import { create_el } from "./utilities/utilities";

const file_picker_button = create_el(
  "button",
  "file-picker-button",
  document.body,
);
file_picker_button.innerText = "Choose save folder";

const editors_container = create_el("div", "editors-container", document.body);
const SPEC_PATHS = ["video_editor.is"];

let spec_editors: Editor[], swipl: SWIPL.SWIPLModule, output: HTMLElement;

async function setup() {
  /* ---------------- Specification editor ---------------- */
  spec_editors = await Promise.all(
    SPEC_PATHS.map(async (spec) =>
      create_editor_alt(
        spec,
        await (await fetch(`./interface-schema/specifications/${spec}`)).text(),
      ),
    ),
  );

  spec_editors.forEach((editor) => editors_container.append(editor.parent));

  // SWIPL WASM setup
  swipl = await SWIPL({ arguments: ["-q"] });

  // Live programming
  let typingTimer: any | null;

  spec_editors.map((editor) =>
    editor.editor_view.dom.addEventListener("change", (_) => {
      if (typingTimer != null) clearTimeout(typingTimer);
      typingTimer = setTimeout(() => update(editor), 1000); // Should this be synchronous?
    }),
  );

  output = create_el('div', 'editor-output', document.body, { innerText: "Output"})

  spec_editors.map(editor => update(editor))
}

async function update(from: Editor) {
  const raw = from.editor_view.state.doc.toString();

  // Sync with file on disk
  if (State.file_system_handle != null) {
    const file_handle = await State.file_system_handle.getFileHandle(
      from.path,
      { create: true },
    );

    // Create a FileSystemWritableFileStream to write to.
    const writable = await file_handle.createWritable();

    // Write the contents of the file to the stream.
    await writable.write(raw);
    await writable.close();
  } else {
    // alert("Note: file not being saved. Please select a folder.");
    console.warn("Note: file not being saved. Please select a folder.")
  }

  const parsed = parse(raw);
  output.innerText = parsed;
}

async function main() {
  // Write out the file
  file_picker_button.addEventListener("click", async () => {
    State.file_system_handle = await window.showDirectoryPicker();
  });

  await setup();
}

async function loop() {
  requestAnimationFrame(loop);
}

main();
loop();
