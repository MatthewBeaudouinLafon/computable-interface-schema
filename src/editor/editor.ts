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
import { erlang } from "@codemirror/legacy-modes/mode/erlang";
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
import { create_el } from "../utilities";
import "./editor.css";

export function create_default_editor(
  heading_label: string = "",
  default_text: string,
  default_open: boolean = false, 
) {
  const parent = create_el("details", "editor-container", document.body);

  if (default_open) {
    parent.setAttribute("open", "");
  }

  if (heading_label != "") {
    const heading = create_el("summary", "editor-heading", parent);
    heading.innerText = `${heading_label}:`;
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

  const editor = new EditorView({
    extensions: [...basic_setup, StreamLanguage.define(erlang)],
    parent: parent,
  });

  editor.dispatch({ changes: [{ from: 0, insert: default_text }] });

  return {
    editor,
    parent,
  };
}
