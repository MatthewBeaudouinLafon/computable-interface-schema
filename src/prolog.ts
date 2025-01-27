import SWIPL from "swipl-wasm";
import { State } from "./State";
import { Editor } from "./editor/editor";

export async function execute_prolog(
  header_editor: Editor,
  design_patterns_editor: Editor,
  rules_editor: Editor,
) {
  // TODO: Try to not reinitialize SWIPL
  State.swipl = await SWIPL({ arguments: ["-q"] });
  State.swipl_no_logical_rules = await SWIPL({ arguments: ["-q"] });

  const { swipl, swipl_no_logical_rules } = State;

  const header_code = header_editor.editor_view.state.doc.toString();
  // const spec_code = State.spec_editor.editor_view.state.doc.toString();
  const spec_code = "";
  const design_patterns_code =
    design_patterns_editor.editor_view.state.doc.toString();
  const rules_code = rules_editor.editor_view.state.doc.toString();

  const full_code = [
    header_code,
    spec_code,
    design_patterns_code,
    rules_code,
  ].reduce(
    (accumulator, currentValue) => accumulator + "\n" + currentValue,
    "",
  );

  const no_logical_rules_code = [
    header_code,
    spec_code,
    design_patterns_code,
  ].reduce(
    (accumulator, currentValue) => accumulator + "\n" + currentValue,
    "",
  );

  // TODO: consider renaming spec.pl to something like full_code.
  swipl.FS.writeFile("/spec.pl", full_code);
  swipl_no_logical_rules.FS.writeFile("/spec.pl", no_logical_rules_code);

  // Execute the full code spec
  let spec_query;
  let spec_query_ret;
  let success: boolean = true;

  try {
    spec_query = swipl.prolog.query(`consult('/spec.pl').`);
    spec_query_ret = spec_query.once() as any;
    success = spec_query_ret.success;
  } catch (e) {
    success = false;
    // console.log("[run_prolog > spec_query_ret]", e);
  }

  if (success == false) {
    console.error("Failed to execute specification.");
    return;
  }

  // Execute the no logical rules code spec
  try {
    spec_query = swipl_no_logical_rules.prolog.query(`consult('/spec.pl').`);
    spec_query_ret = spec_query.once() as any;
    success = spec_query_ret.success;
  } catch (e) {
    success = false;
  }

  if (success == false) {
    console.error("Failed to execute specification.");
    return;
  }
}
