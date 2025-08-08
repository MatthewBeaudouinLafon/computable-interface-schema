import { get_pyodide } from "../main";
import { div, svg } from "../utilities/utilities";
import { CodeMirrorEditor, create_codemirror } from "./codemirror/codemirror";
import "./editor.css";

export type Editor = {
  codemirror: CodeMirrorEditor;
  frag: HTMLElement;
  code: string;
};

export function create_editor(initial_code: string) {
  // Sub views
  const codemirror = create_codemirror(initial_code);

  // View
  const frag = div(".editor", [
    codemirror.frag,
    svg("svg", ".editor-code-overlay"),
  ]);

  const view: Editor = {
    frag,
    code: initial_code,
    codemirror,
  };

  // Event listeners
  codemirror.editor_view.dom.addEventListener("change", () => {
    editor_update_code(view, codemirror.value);
  });

  // Initial setup
  editor_update_code(view, initial_code);

  return view;
}

export async function editor_update_code(editor: Editor, code: string) {
  editor.code = code;

  const pyodide = get_pyodide();

  const result = await pyodide.runPython(
    `from compiler import compile

compile(spec)`,
    {
      locals: pyodide.toPy({
        spec: editor.code,
      }),
    }
  );

  console.log(result);

  // ...draw diagram
  //   async function update(editor: {
  //   editor_view: EditorView;
  //   el: HTMLElement;
  //   value: () => string;
  // }) {
  //   const mermaid_el = editor.el.parentElement!.querySelector(
  //     ".mermaid"
  //   ) as HTMLElement;

  //   const result = await pyodide.runPython(
  //     `mermaid_graph(yaml.safe_load(spec))`,
  //     {
  //       locals: pyodide.toPy({
  //         spec: editor.value(),
  //       }),
  //     }
  //   );

  //   mermaid_el.innerHTML = result;
  //   mermaid_el.removeAttribute("data-processed");

  //   mermaid.run({
  //     nodes: [mermaid_el],
  //   });
  // }
}
