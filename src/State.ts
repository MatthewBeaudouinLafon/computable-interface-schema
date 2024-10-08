import { EditorView } from "codemirror";
import SWIPL from "swipl-wasm";

export class State {
  static swipl: SWIPL.SWIPLModule;

  static spec_editor: EditorView;
  static query_editor: EditorView;

  static spec_output: HTMLElement;
  static query_output: HTMLElement;

  static diagram_output: HTMLElement;
}
