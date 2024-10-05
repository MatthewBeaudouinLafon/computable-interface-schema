import SWIPL from "swipl-wasm";
import { create_default_editor } from "./editor/editor";
import "./style.css";
import { create_el, hash_code } from "./utilities";

async function main() {
  // Setup specification and query editors

  let SPEC = await (await fetch("./spec.txt")).text();
  let QUERY = `objects(X).`;

  // Spec editor
  const { editor: spec_editor, parent: spec_parent } =
    create_default_editor("Specification");
  spec_parent.classList.add("spec-editor");
  spec_editor.dispatch({ changes: [{ from: 0, insert: SPEC }] });

  // Query editor
  const { editor: query_editor, parent: query_parent } =
    create_default_editor("Query");
  query_parent.classList.add("query-editor");
  query_editor.dispatch({ changes: [{ from: 0, insert: QUERY }] });

  // Status(es)
  const spec_status = create_el("div", "editor-status", spec_parent);
  spec_status.innerText = "-";

  const query_status = create_el("div", "editor-status", query_parent);
  query_status.innerText = "-";

  const swipl = await SWIPL({ arguments: ["-q"] });

  // Live programming
  let typingTimer: any | null;

  spec_editor.dom.addEventListener("change", (_) => {
    if (typingTimer != null) clearTimeout(typingTimer);
    typingTimer = setTimeout(() => run_prolog(), 1000);
  });

  query_editor.dom.addEventListener("change", (_) => {
    if (typingTimer != null) clearTimeout(typingTimer);
    typingTimer = setTimeout(() => run_prolog(), 1000);
  });

  function run_prolog() {
    let time = performance.now();

    const spec_code = spec_editor.state.doc.toString();
    const query_code = query_editor.state.doc.toString();

    // console.log(`${spec_code}\n${query_code}`);

    swipl.FS.writeFile("/spec.pl", spec_code);

    // Execute the spec
    const spec_query = swipl.prolog.query(`consult('/spec.pl').`);
    const spec_query_ret = spec_query.once() as any;
    console.log("[run_prolog > spec_query_ret]", spec_query_ret);
    spec_status.innerText = spec_query_ret.success ? "Success." : "Fail.";

    // Execute the query
    const query = swipl.prolog.query(query_code);
    let query_ret = query.next() as any;
    query_status.innerHTML = "";
    query_status.append(query_result_to_div(query_code, query_ret.value ?? {}));
    console.log("[run_prolog > query_ret]", query_ret);

    let MAX_LIMIT = 50;
    let ITERS = 0;
    while (query_ret?.done != true && ITERS < MAX_LIMIT) {
      query_ret = query.next();
      console.log("[run_prolog > query_ret]", query_ret);
      query_status.append(
        query_result_to_div(query_code, query_ret.value ?? {})
      );

      ITERS++;
    }

    if (ITERS == MAX_LIMIT) {
      query_status.innerHTML += `Max limit of ${MAX_LIMIT} reached.`;
    }

    query_status.innerHTML += `${Math.round(performance.now() - time)}ms.`;
  }

  run_prolog();
}

function query_result_to_div(
  query_code: string,
  data: { [key: string]: string }
) {
  // Create a container
  const container = create_el("div", "query-result-container");
  let html = query_code;

  console.log(data);

  // Add in each result
  for (const [key, value] of Object.entries(data)) {
    if (key.startsWith("$")) continue;

    const index = html.indexOf(key);

    if (index >= 0) {
      const value_entry = create_el("div", "query-result-entry");
      value_entry.innerText = value;
      const hue = Math.floor(hash_code(value) * 360);
      value_entry.style.background = `oklch(0.7 0.4 ${hue}deg / 0.15)`;

      html =
        html.slice(0, index) + value_entry.outerHTML + html.slice(index + 1);
    }

    // const result = create_el("div", "query-result", container);
    // const key_entry = create_el("div", "query-result-entry");
    // const value_entry = create_el("div", "query-result-entry");
    // key_entry.innerText = key;
    // value_entry.innerText = value;
    // result.append(key_entry, value_entry);
  }

  container.innerHTML = html;

  return container;
}

main();
