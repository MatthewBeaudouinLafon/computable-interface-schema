import { EditorView } from "codemirror";
import { Query } from "swipl-wasm";
import { State } from "../State";

export function create_el(
  tag: string,
  classes: string[] | string = [],
  parent?: Element,
  options?: Partial<HTMLElement> | Partial<SVGElement>
) {
  const el = document.createElement(tag);

  if (Array.isArray(classes)) {
    el.classList.add(...classes);
  } else {
    el.classList.add(classes);
  }

  parent?.appendChild(el);

  Object.assign(el, options ?? {});

  return el;
}

export function assert_never(_never: never, message?: string): never {
  throw new Error(
    message || `Reached unreachable code: unexpected value ${_never}`
  );
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
  for (const [key, value] of Object.entries(data)) {
    if (key.startsWith("$")) continue;

    const index_start = html.indexOf(key);

    // Find index of next space or comma. Find index of each possible stop
    // character, then pick the smallest value that's not -1.
    const html_length: number = html.length;
    const index_end: number = [" ", ",", ")"]
      .map((char) => {
        return html.indexOf(char, index_start);
      })
      .reduce(
        (acc: number, curr: number) => (curr > -1 ? Math.min(acc, curr) : acc),
        html_length
      );

    if (index_start >= 0) {
      const value_entry = create_el("div", "query-result-entry");
      value_entry.innerText = value;
      const hue = Math.floor(hash_code(value) * 360);
      value_entry.style.background = `oklch(0.7 0.4 ${hue}deg / 0.15)`;

      html =
        html.slice(0, index_start) +
        value_entry.outerHTML +
        html.slice(index_end);
    }
  }

  container.innerHTML = html;

  return container;
}

export function get_all_prolog_query_results(
  query_raw: string,
  options: { limit?: number; do_not_include_logical_rules?: boolean } = {}
) {
  let query: Query;

  if (options.do_not_include_logical_rules == true) {
    query = State.swipl_no_logical_rules.prolog.query(query_raw);
  } else {
    query = State.swipl.prolog.query(query_raw);
  }

  let query_ret = query.next() as any;
  let query_results: any[] = [];

  if ("value" in query_ret) {
    query_results.push(query_ret.value);
  }

  let iters = 0;
  let limit = options.limit ?? 50;

  while (query_ret?.done != true && iters < limit) {
    query_ret = query.next();

    if (query_ret != null && "value" in query_ret) {
      query_results.push(query_ret.value);
    }
    iters++;
  }

  return query_results;
}

const highlight_keywords = ["structures", "subsets"];

// export function custom_highlighting(editor: EditorView);

export function add_custom_highlighting(editor: EditorView) {
  editor.dom.addEventListener("change", (_) => {
    // console.log(editor.dom)
    const els = [...editor.dom.querySelectorAll(".ͼc")] as HTMLElement[];

    for (const el of els) {
      if (highlight_keywords.includes(el.innerText)) {
        el.classList.add("cm-ok-dev");
      }
    }
  });
}

export function range(size: number, start: number = 0): Array<number> {
  return [...Array(size).keys()].map((i) => i + start);
}

export function create_svg_element(
  classes: string[] | string = [],
  parent?: Element
) {
  const svg_el = document.createElementNS("http://www.w3.org/2000/svg", "svg");

  if (Array.isArray(classes)) {
    svg_el.classList.add(...classes);
  } else {
    svg_el.classList.add(classes);
  }

  if (parent != undefined) {
    parent.appendChild(svg_el);
  }

  return svg_el;
}

export function create_path_element(
  classes: string[] | string = [],
  parent?: Element
): SVGPathElement {
  const pathEl = document.createElementNS("http://www.w3.org/2000/svg", "path");

  if (Array.isArray(classes)) {
    pathEl.classList.add(...classes);
  } else {
    pathEl.classList.add(classes);
  }

  if (parent != undefined) {
    parent.appendChild(pathEl);
  }

  return pathEl;
}

export function create_polygon_element(
  classes: string[] | string = [],
  parent?: Element
): SVGPolygonElement {
  const pathEl = document.createElementNS(
    "http://www.w3.org/2000/svg",
    "polygon"
  );

  if (Array.isArray(classes)) {
    pathEl.classList.add(...classes);
  } else {
    pathEl.classList.add(classes);
  }

  if (parent != undefined) {
    parent.appendChild(pathEl);
  }

  return pathEl;
}

export function setup_drag(
  el: HTMLElement,
  on_begin_drag: () => void,
  on_drag: (dx: number, dy: number) => void,
  on_release_drag: () => void
) {
  let mx = 0;
  let my = 0;

  let is_dragging = false;

  document.body.addEventListener("mousemove", (e) => {
    if (is_dragging) {
      on_drag(e.x - mx, e.y - my);
    }

    mx = e.x;
    my = e.y;
  });

  el.addEventListener("mousedown", (e) => {
    if (!is_dragging) {
      is_dragging = true;
      on_begin_drag();
    }
  });

  document.body.addEventListener("mouseup", (e) => {
    if (is_dragging) {
      is_dragging = false;

      on_release_drag();
    }
  });
}

export function lerp(a: number, b: number, t: number, threshold: number = 0) {
  if (Math.abs(a - b) < threshold) return b;

  return a * (1 - t) + b * t;
}

export function squared_polar(
  point: [number, number],
  centre: [number, number]
) {
  return [
    Math.atan2(point[1] - centre[1], point[0] - centre[0]),
    (point[0] - centre[0]) ** 2 + (point[1] - centre[1]) ** 2, // Square of distance
  ];
}

// https://stackoverflow.com/questions/59287928/algorithm-to-create-a-polygon-from-points
export function poly_sort(points: [number, number][]) {
  // Get "centre of mass"
  let centre: [number, number] = [
    points.reduce((sum, p) => sum + p[0], 0) / points.length,
    points.reduce((sum, p) => sum + p[1], 0) / points.length,
  ];

  // Sort by polar angle and distance, centered at this centre of mass.
  let polars = points.map((p) => ({
    point: p,
    polar: squared_polar(p, centre),
  }));
  polars.sort((a, b) => a.polar[0] - b.polar[0] || a.polar[1] - b.polar[1]);

  return polars.map((p) => p.point);
}

// https://stackoverflow.com/questions/7054272/how-to-draw-smooth-curve-through-n-points-using-javascript-html5-canvas
export function get_curve_points(
  pts: number[],
  tension: number = 0.5,
  isClosed: boolean = false,
  numOfSegments: number = 16
) {
  var _pts = [],
    res = [], // clone array
    x,
    y, // our x,y coords
    t1x,
    t2x,
    t1y,
    t2y, // tension vectors
    c1,
    c2,
    c3,
    c4, // cardinal points
    st,
    t,
    i; // steps based on num. of segments

  // clone array so we don't change the original
  //
  _pts = pts.slice(0);

  // The algorithm require a previous and next point to the actual point array.
  // Check if we will draw closed or open curve.
  // If closed, copy end points to beginning and first points to end
  // If open, duplicate first points to befinning, end points to end
  if (isClosed) {
    _pts.unshift(pts[pts.length - 1]);
    _pts.unshift(pts[pts.length - 2]);
    _pts.unshift(pts[pts.length - 1]);
    _pts.unshift(pts[pts.length - 2]);
    _pts.push(pts[0]);
    _pts.push(pts[1]);
  } else {
    _pts.unshift(pts[1]); //copy 1. point and insert at beginning
    _pts.unshift(pts[0]);
    _pts.push(pts[pts.length - 2]); //copy last point and append
    _pts.push(pts[pts.length - 1]);
  }

  // ok, lets start..

  // 1. loop goes through point array
  // 2. loop goes through each segment between the 2 pts + 1e point before and after
  for (i = 2; i < _pts.length - 4; i += 2) {
    for (t = 0; t <= numOfSegments; t++) {
      // calc tension vectors
      t1x = (_pts[i + 2] - _pts[i - 2]) * tension;
      t2x = (_pts[i + 4] - _pts[i]) * tension;

      t1y = (_pts[i + 3] - _pts[i - 1]) * tension;
      t2y = (_pts[i + 5] - _pts[i + 1]) * tension;

      // calc step
      st = t / numOfSegments;

      // calc cardinals
      c1 = 2 * Math.pow(st, 3) - 3 * Math.pow(st, 2) + 1;
      c2 = -(2 * Math.pow(st, 3)) + 3 * Math.pow(st, 2);
      c3 = Math.pow(st, 3) - 2 * Math.pow(st, 2) + st;
      c4 = Math.pow(st, 3) - Math.pow(st, 2);

      // calc x and y cords with common control vectors
      x = c1 * _pts[i] + c2 * _pts[i + 2] + c3 * t1x + c4 * t2x;
      y = c1 * _pts[i + 1] + c2 * _pts[i + 3] + c3 * t1y + c4 * t2y;

      //store points in array
      res.push(x);
      res.push(y);
    }
  }

  return res;
}

export function union_bboxes(
  bboxes: { left: number; top: number; width: number; height: number }[]
) {
  const left = Math.min(...bboxes.map((b) => b.left));
  const top = Math.min(...bboxes.map((b) => b.top));

  const right = Math.max(...bboxes.map((b) => b.left + b.width));
  const bottom = Math.max(...bboxes.map((b) => b.top + b.height));

  const width = right - left;
  const height = bottom - top;

  return { left, top, width, height };
}
