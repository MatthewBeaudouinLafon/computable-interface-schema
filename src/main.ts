import mermaid from "mermaid";
import { loadPyodide, version as pyodideVersion } from "pyodide";
import { create_editor } from "./editor/editor";
import "./style.css";
import { tabs } from "./utilities/ui-utilities";

const paths = ["calendar.yaml", "video-editor.yaml"];

const pyodide = await loadPyodide({
  indexURL: `https://cdn.jsdelivr.net/pyodide/v${pyodideVersion}/full/`,
});

export function get_pyodide() {
  return pyodide;
}

async function main() {
  // Load meta algo dependencies
  await pyodide.loadPackage("networkx");
  await pyodide.loadPackage("pyyaml");

  const python_files = await Promise.all(
    ["compiler.py", "parser.py"].map(async (name) => [
      name,
      await (await fetch(`./python-lib/${name}`)).text(),
    ])
  );

  python_files.forEach(([name, contents]) => {
    pyodide.FS.writeFile(`${name}`, contents);
  });

  // Mermaid styling
  mermaid.initialize({
    theme: "neutral",
    flowchart: {
      padding: 0,
      nodeSpacing: 0,
    },
  });

  // Load specs
  const specs = await Promise.all(
    paths.map(
      async (p) =>
        await (await fetch(`./interface-schema/specifications/${p}`)).text()
    )
  );

  const editors = specs.map((spec) => create_editor(spec));

  const frag = tabs(
    ".editor-tabs",
    editors.map((editor, i) => [paths[i], editor.frag])
  );

  const app = document.getElementById("app")!;
  app.append(frag);
}

async function loop() {
  requestAnimationFrame(loop);
}

main();
loop();
