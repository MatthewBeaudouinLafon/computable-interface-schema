import SWIPL from "swipl-wasm";
import { Scene } from "./diagram/scene";
import { Editor } from "./editor/editor";

export class State {
  static swipl: SWIPL.SWIPLModule;
  static swipl_no_logical_rules: SWIPL.SWIPLModule;

  static header_editor: Editor;
  static spec_editors: Editor[];
  static design_patterns_editor: Editor;
  static rules_editor: Editor;
  static query_editor: Editor;
  static query_output: HTMLElement;

  static file_system_handle: FileSystemDirectoryHandle;

  static scene: Scene;

  // Match the contents of public/interface-schema/specifications/
  // TODO: see if Vite can do this automatically
  static spec_list: string[] = ["web-browser", "tabs", "state-machine", "user"];
}
