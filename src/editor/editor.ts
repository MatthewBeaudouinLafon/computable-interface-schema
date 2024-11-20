import { closeBrackets, closeBracketsKeymap, completionKeymap } from "@codemirror/autocomplete";
import { defaultKeymap, history, historyKeymap } from "@codemirror/commands";
import {
  bracketMatching,
  defaultHighlightStyle,
  foldKeymap,
  indentOnInput,
  StreamLanguage,
  syntaxHighlighting,
} from "@codemirror/language";
import { erlang } from "@codemirror/legacy-modes/mode/erlang";
import { lintKeymap } from "@codemirror/lint";
import { highlightSelectionMatches, searchKeymap } from "@codemirror/search";
import { EditorState } from "@codemirror/state";
import {
  crosshairCursor,
  Decoration,
  DecorationSet,
  dropCursor,
  highlightSpecialChars,
  keymap,
  MatchDecorator,
  // lineNumbers,
  rectangularSelection,
  ViewPlugin,
  ViewUpdate,
} from "@codemirror/view";
import { EditorView } from "codemirror";
import { create_el } from "../utilities/utilities";
import "./editor.css";

// export function prepare_spec_dropdown(items: string[]) {
//   const dropdownEl = document.createElement("select");
//   dropdownEl.classList.add("editor-dropdown");

//   dropdownEl.onchange = async function (event) {
//     if (!event.target) {
//       return;
//     }

//     // TODO: sanitize spec_name?
//     const target = event.target as HTMLSelectElement;
//     const spec_name = target.value;
//     const new_spec = await (await fetch(`./interface-schema/specifications/${spec_name}.pl`)).text();

//     console.log(new_spec.startsWith("<!DOCTYPE html>"));
//     if (new_spec.startsWith("<!DOCTYPE html>")) {
//       // For some reason fetch returns the html file when it doens't find the prolog file...
//       // In which case, show an empty file.
//       State.spec_editor.editor_view.dispatch({
//         changes: {
//           from: 0,
//           to: State.spec_editor.editor_view.state.doc.length,
//         },
//       });
//     } else {
//       // Else we pick an actual file and put it in the editor.

//       // TODO: probably keep state of edited files in memory. Maybe do:
//       // State.spec_states = { file_name: CodeMirrorState }
//       State.spec_editor.editor_view.dispatch({
//         changes: {
//           from: 0,
//           to: State.spec_editor.editor_view.state.doc.length,
//           insert: new_spec,
//         },
//       });
//     }
//   };

//   items.forEach((item) => {
//     const option = create_el("option", "editor-dropdown-option", dropdownEl);
//     option.setAttribute("value", item);
//     option.textContent = item;
//   });

//   return dropdownEl;
// }

// Interface schema syntax highlighting
const CustomOperatorMatcher = new MatchDecorator({
  regexp: /structures|subsets/g,
  decoration: (match) => {
    return Decoration.mark({ class: "cm-custom-highlight" });
  },
  maxLength: 1,
});

const customHighlight = ViewPlugin.fromClass(
  class {
    customHighlight: DecorationSet;
    constructor(view: EditorView) {
      this.customHighlight = CustomOperatorMatcher.createDeco(view);
    }
    update(update: ViewUpdate) {
      this.customHighlight = CustomOperatorMatcher.updateDeco(update, this.customHighlight);
    }
  },
  {
    decorations: (instance) => instance.customHighlight,
    provide: (plugin) =>
      EditorView.atomicRanges.of((view) => {
        return view.plugin(plugin)?.customHighlight || Decoration.none;
      }),
  },
);

export type Editor = {
  parent: HTMLElement;
  editor_view: EditorView;
  path: string;
};

export function create_editor(path: string = "", default_text: string): Editor {
  const parent = create_el("div", "editor-container");

  if (path != "") {
    const heading = create_el("div", "editor-heading", parent);
    heading.innerText = `${path}`;
  }

  // https://github.com/codemirror/basic-setup/blob/main/src/codemirror.ts
  const basic_setup = (() => [
    EditorView.updateListener.of((v) => {
      if (v.docChanged) {
        const event = new CustomEvent("change", { detail: v });
        v.view.dom.dispatchEvent(event);
      }
    }),
    // lineNumbers(),
    // highlightActiveLineGutter(),
    highlightSpecialChars(),
    history(),
    // foldGutter(),
    // drawSelection(),
    dropCursor(),
    EditorState.allowMultipleSelections.of(true),
    indentOnInput(),
    syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
    bracketMatching(),
    closeBrackets(),
    // autocompletion(),
    rectangularSelection(),
    crosshairCursor(),
    // highlightActiveLine(),
    highlightSelectionMatches(),
    customHighlight,
    keymap.of([
      ...closeBracketsKeymap,
      ...defaultKeymap,
      ...searchKeymap,
      ...historyKeymap,
      ...foldKeymap,
      ...completionKeymap,
      ...lintKeymap,
    ]),
  ])();

  const editor_view = new EditorView({
    state: EditorState.create({
      extensions: [...basic_setup, StreamLanguage.define(erlang), EditorView.lineWrapping],
    }),
    parent: parent,
  });

  editor_view.dispatch({ changes: [{ from: 0, insert: default_text }] });

  return {
    editor_view,
    parent,
    path,
  };
}
