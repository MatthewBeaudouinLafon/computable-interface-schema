import {
  autocompletion,
  closeBrackets,
  closeBracketsKeymap,
  completionKeymap,
} from "@codemirror/autocomplete";
import {
  defaultKeymap,
  history,
  historyKeymap,
  indentWithTab,
} from "@codemirror/commands";
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
import { EditorState, Transaction } from "@codemirror/state";
import {
  crosshairCursor,
  dropCursor,
  highlightSpecialChars,
  keymap,
  lineNumbers,
  rectangularSelection,
} from "@codemirror/view";
import type { SourceLocation } from "acorn";
import { EditorView } from "codemirror";
import { div } from "../../utilities/utilities";
import "./codemirror.css";

export type CodeMirrorEditor = {
  frag: HTMLElement;
  value: string;
  set_value: (value: string) => void;
  get_selection: () => SourceLocation;
  location_to_coords: (loc: number) => { line: number; column: number };
  coords_to_location: (column: number, line: number) => number;
  editor_view: EditorView;
};

export function create_codemirror(code = ""): CodeMirrorEditor {
  // https://github.com/codemirror/basic-setup/blob/main/src/codemirror.ts
  const editor_view = new EditorView({
    doc: code,
    extensions: [
      EditorView.updateListener.of((v) => {
        if (v.docChanged) {
          const event = new CustomEvent("change", { detail: v });
          v.view.dom.dispatchEvent(event);
        }

        v.transactions
          .filter((t) => t.isUserEvent)
          .map((t: Transaction) => {
            const event = new CustomEvent("user-event", {
              detail: t,
            });
            v.view.dom.dispatchEvent(event);
          });
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
      autocompletion(),

      lineNumbers(),
      keymap.of([
        ...closeBracketsKeymap,
        ...defaultKeymap,
        ...searchKeymap,
        ...historyKeymap,
        ...foldKeymap,
        ...completionKeymap,
        ...lintKeymap,
        indentWithTab,
      ]),
      // theme,
      StreamLanguage.define(yaml),
    ],
  });

  return {
    frag: div({ className: "codemirror-wrapper" }, editor_view.dom),
    get value() {
      return editor_view.state.doc.toString();
    },
    editor_view,
    set_value: (value: string) => {
      editor_view.dispatch({
        changes: {
          from: 0,
          to: editor_view.state.doc.length,
          insert: value,
        },
      });
    },
    location_to_coords: (loc: number) => {
      const start_line = editor_view.state.doc.lineAt(loc);

      return {
        line: start_line.number,
        column: loc - start_line.from,
      };
    },
    coords_to_location: (column: number, line: number) => {
      return editor_view.state.doc.line(line).from + column;
    },
    get_selection: () => {
      const selection = editor_view.state.selection;

      const start_line = editor_view.state.doc.lineAt(selection.ranges[0].from);

      const end_line = editor_view.state.doc.lineAt(selection.ranges[0].to);

      return {
        start: {
          line: start_line.number,
          column: selection.ranges[0].from - start_line.from,
        },
        end: {
          line: end_line.number,
          column: selection.ranges[0].to - end_line.from,
        },
      };

      // const start_col = selection.ranges[0].from - start_line + 1;
      // const end_col = selection.ranges[0].to - start_line + 1;
    },
  };
}
