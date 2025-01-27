import SWIPL from "swipl-wasm";

export class State {
  static swipl: SWIPL.SWIPLModule;
  static swipl_no_logical_rules: SWIPL.SWIPLModule;

  static file_system_handle: FileSystemDirectoryHandle;

  // Match the contents of public/interface-schema/specifications/
  // TODO: see if Vite can do this automatically
  static spec_list: string[] = ["web-browser", "tabs", "state-machine", "user"];
}
