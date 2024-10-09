import { setup_bloom } from "./bloom";
import { State } from "./State";
import { query_result_to_div } from "./utilities";

export async function execute_prolog() {
  const time = performance.now();
  const { swipl, spec_output, query_output } = State;
  const spec_code = State.spec_editor.state.doc.toString();
  const query_code = State.query_editor.state.doc.toString();

  swipl.FS.writeFile("/spec.pl", spec_code);

  // Execute the spec
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

  // console.log("[run_prolog > spec_query_ret]", spec_query_ret);
  spec_output.innerText = success ? "Success." : "Fail.";

  query_output.innerHTML = "";

  // Execute the query
  if (spec_query_ret.success) {
    const query = swipl.prolog.query(query_code);
    let query_ret = query.next() as any;
    query_output.append(query_result_to_div(query_code, query_ret.value ?? {}));
    // console.log("[run_prolog > query_ret]", query_ret);

    let MAX_LIMIT = 50;
    let ITERS = 0;
    while (query_ret?.done != true && ITERS < MAX_LIMIT) {
      query_ret = query.next();
      // console.log("[run_prolog > query_ret]", query_ret);
      query_output.append(
        query_result_to_div(query_code, query_ret.value ?? {})
      );

      ITERS++;
    }

    if (ITERS == MAX_LIMIT) {
      query_output.innerHTML += `Max limit of ${MAX_LIMIT} reached.`;
    }

    query_output.innerHTML += `${Math.round(performance.now() - time)}ms.`;
  }

  setup_bloom();
}
