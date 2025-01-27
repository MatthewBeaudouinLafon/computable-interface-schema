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
import {
  highlightSelectionMatches,
  RegExpCursor,
  searchKeymap,
} from "@codemirror/search";
import { EditorState, Range, StateEffect, StateField } from "@codemirror/state";
import {
  crosshairCursor,
  Decoration,
  dropCursor,
  highlightSpecialChars,
  keymap,
  // lineNumbers,
  rectangularSelection,
} from "@codemirror/view";
import { EditorView } from "codemirror";
import { create_el } from "../utilities/utilities";
import "./editor.css";

const keywords = [
  "structures",
  "subsets",
  "constrains",
  "covers",
  "along",
  "groups",
  "represents",
  "with",
];

export function create_editor_alt(
  path: string = "",
  default_text: string
): Editor {
  const parent = create_el("div", "editor-container");

  if (path != "") {
    const heading = create_el("div", "editor-heading", parent);
    heading.innerText = `${path}`;
  }

  /* -------------------- Highlighting -------------------- */
  const highlight_effect = StateEffect.define<Range<Decoration>[]>();

  const highlight_extension = StateField.define({
    create() {
      return Decoration.none;
    },
    update(value, transaction) {
      value = value.map(transaction.changes);

      for (let effect of transaction.effects) {
        if (effect.is(highlight_effect))
          value = value.update({ add: effect.value, sort: true });
      }

      return value;
    },
    provide: (f) => EditorView.decorations.from(f),
  });

  const update_listener = EditorView.updateListener.of((update) => {
    if (update.docChanged) {
      let cursor = new RegExpCursor(
        view.state.doc,
        keywords.map((k) => `(${k})`).join("|")
      );

      while (cursor.next() && !cursor.done) {
        const highlight_decoration = Decoration.mark({
          attributes: { class: "cm-custom-highlight" },
        });

        view.dispatch({
          effects: highlight_effect.of([
            highlight_decoration.range(cursor.value.from, cursor.value.to),
          ]),
        });
      }
    }
  });

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

  const state = EditorState.create({
    extensions: [
      ...basic_setup,
      StreamLanguage.define(erlang),
      EditorView.lineWrapping,
      update_listener,
      highlight_extension,
    ],
  });

  const view = new EditorView({
    state,
    parent: parent,
  });

  view.dispatch({ changes: [{ from: 0, insert: default_text }] });

  return {
    editor_view: view,
    parent,
    path,
  };
}

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
        StreamLanguage.define(erlang),
        EditorView.lineWrapping,
      ],
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
