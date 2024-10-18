import { State } from "./State";

export function create_el(
  tag: string,
  classes: string[] | string = [],
  parent?: Element,
  prepend: boolean = false
) {
  const el = document.createElement(tag);

  if (Array.isArray(classes)) {
    el.classList.add(...classes);
  } else {
    el.classList.add(classes);
  }

  if (parent != undefined) {
    if (prepend) {
      parent.prepend(el);
    } else {
      parent.appendChild(el);
    }
  }

  return el;
}

/**
 * Returns a hash code from a string
 * @param  {String} str The string to hash.
 * @return {Number}    A 32bit integer
 * @see http://werxltd.com/wp/2010/05/13/javascript-implementation-of-javas-string-hashcode-method/
 */
export function hash_code(str: string): number {
  let hash = 0;
  for (let i = 0, len = str.length; i < len; i++) {
    let chr = str.charCodeAt(i);
    hash = (hash << 5) - hash + chr;
    hash |= 0; // Convert to 32bit integer
  }
  return (0.5 * hash) / 2_147_483_647 + 0.5;
}

export function query_result_to_div(
  query_code: string,
  data: { [key: string]: string } // { X: 'tabs', Y: '...' }
) {
  // Create a container
  const container = create_el("div", "query-result-container");
  let html = query_code;

  // Add in each result
  console.log(data);
  for (const [key, value] of Object.entries(data)) {
    if (key.startsWith("$")) continue;

    const index_start = html.indexOf(key);

    // Find index of next space or comma. Find index of each possible stop 
    // character, then pick the smallest value that's not -1.
    const html_length: number = html.length;
    const index_end: number = [' ', ',',')'].map(
      (char) => {
        return html.indexOf(char, index_start);
    }).reduce(
      (acc: number, curr: number) => curr > -1 ? Math.min(acc, curr) : acc,
      html_length
    );

    if (index_start >= 0) {
      const value_entry = create_el("div", "query-result-entry");
      value_entry.innerText = value;
      const hue = Math.floor(hash_code(value) * 360);
      value_entry.style.background = `oklch(0.7 0.4 ${hue}deg / 0.15)`;

      html =
        html.slice(0, index_start) + value_entry.outerHTML + html.slice(index_end);
    }
  }

  container.innerHTML = html;

  return container;
}

export function get_all_prolog_query_results(
  query_raw: string,
  limit: number = 50
) {
  const query = State.swipl.prolog.query(query_raw);
  let query_ret = query.next() as any;

  let query_results: any[] = [];
  let iters = 0;
  while (query_ret?.done != true && iters < limit) {
    delete query_ret.value["$tag"];
    query_results.push(query_ret.value);
    query_ret = query.next();
    iters++;
  }

  return query_results;
}
