import mermaid from "mermaid";
import { loadPyodide, version as pyodideVersion } from "pyodide";
import { create_editor, Editor } from "./editor/editor";
import "./style.css";

const path_a = "calendar.yaml";
const path_b = "video-editor.yaml";
const pyodide = await loadPyodide({
  indexURL: `https://cdn.jsdelivr.net/pyodide/v${pyodideVersion}/full/`,
});

async function main() {
  const editor_a = create_editor(
    path_a,
    await (await fetch(`./interface-schema/specifications/${path_a}`)).text()
  );

  const editor_b = create_editor(
    path_b,
    await (await fetch(`./interface-schema/specifications/${path_b}`)).text()
  );

  document.body.append(editor_a.parent);
  document.body.append(editor_b.parent);

  // Setup pyodide
  await pyodide.loadPackage("pyyaml");
  await pyodide.loadPackage("networkx");
  await pyodide.loadPackage("scipy");
  const base_meta_algo = await (await fetch(`./metalgo.py`)).text();
  pyodide.runPython(base_meta_algo);

  // Live programming
  let typingTimer: any | null;
  [editor_a, editor_b].forEach((editor) => {
    editor.editor_view.dom.addEventListener("change", (_) => {
      if (typingTimer != null) clearTimeout(typingTimer);
      typingTimer = setTimeout(() => update(editor_a), 1000);
    });
  });

  const analogy = pyodide.runPython(
    `analogy, cost = compute_analogy(make_graph(yaml.safe_load(spec_a)), make_graph(yaml.safe_load(spec_b)));
serialize_analogy(analogy)`,
    {
      locals: pyodide.toPy({
        spec_a: editor_a.editor_view.state.doc.toString(),
        spec_b: editor_b.editor_view.state.doc.toString(),
      }),
    }
  );

  console.log(analogy);

  [editor_a, editor_b].forEach(update);
}

async function update(editor: Editor) {
  const mermaid_el = editor.parent.querySelector(".mermaid") as HTMLElement;

  const py_graph = pyodide.runPython(`mermaid_graph(yaml.safe_load(spec))`, {
    locals: pyodide.toPy({ spec: editor.editor_view.state.doc.toString() }),
  });

  mermaid_el.innerHTML = py_graph;
  mermaid_el.removeAttribute("data-processed");

  mermaid.run({
    nodes: [mermaid_el],
  });
}

async function loop() {
  requestAnimationFrame(loop);
}

main();
loop();
