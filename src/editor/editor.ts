import {
  closeBrackets,
  closeBracketsKeymap,
  completionKeymap,
} from "@codemirror/autocomplete";
import { defaultKeymap, history, historyKeymap } from "@codemirror/commands";
import {
  bracketMatching,
  defaultHighlightStyle,
  foldKeymap,
  indentOnInput,
  StreamLanguage,
  syntaxHighlighting,
} from "@codemirror/language";
import { yaml } from "@codemirror/legacy-modes/mode/yaml";
import { lintKeymap } from "@codemirror/lint";
import { highlightSelectionMatches, searchKeymap } from "@codemirror/search";
import { EditorState } from "@codemirror/state";
import {
  crosshairCursor,
  dropCursor,
  highlightSpecialChars,
  keymap,
  // lineNumbers,
  rectangularSelection,
} from "@codemirror/view";
import { EditorView } from "codemirror";
import { el } from "../utilities/utilities";
import "./editor.css";

export type Editor = {
  parent: HTMLElement;
  editor_view: EditorView;
  path: string;
};

export function create_editor(path: string = "", default_text: string): Editor {
  const parent = el(
    "div",
    { class: "editor-container" },
    el("div", { class: "editor-heading", innerText: path })
  );

  // https://github.com/codemirror/basic-setup/blob/main/src/codemirror.ts
  const basic_setup = (() => [
    EditorView.updateListener.of((v) => {
      if (v.docChanged) {
        const event = new CustomEvent("change", { detail: v });
        v.view.dom.dispatchEvent(event);
      }
    }),
    highlightSpecialChars(),
    history(),
    dropCursor(),
    EditorState.allowMultipleSelections.of(true),
    indentOnInput(),
    syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
    bracketMatching(),
    closeBrackets(),
    rectangularSelection(),
    crosshairCursor(),
    highlightSelectionMatches(),
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
      extensions: [
        ...basic_setup,
        StreamLanguage.define(yaml),
        EditorView.lineWrapping,
      ],
    }),
    parent: parent,
  });

  editor_view.dispatch({ changes: [{ from: 0, insert: default_text }] });

  parent.append(el("pre", { class: "mermaid", innerHTML: "" }));

  return {
    editor_view,
    parent,
    path,
  };
}
