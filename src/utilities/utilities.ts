export type ElementProps =
  | Partial<
      | SVGElement
      | HTMLElement
      | { class: string | (string | null)[] }
      | { data: string[][] }
      | { style: Partial<CSSStyleDeclaration> }
      | { src: string }
    >
  | string;

export type ElementChildren = (Element | string)[] | Element | string;

function el_helper(
  _el: HTMLElement | SVGElement,
  props: ElementProps = {},
  children: ElementChildren = []
) {
  if (typeof props === "string") {
    if (props.at(0) === ".") {
      _el.classList.add(props.slice(1));
    } else if (props.at(0) === "#") {
      _el.id = props.slice(1);
    } else {
      console.trace(
        "[el] Props is a string but not qualified with a class (.) or id (#)."
      );
    }
  }

  if (typeof props !== "string") {
    Object.assign(_el, props ?? {});

    if ("class" in props && props.class !== undefined) {
      _el.classList.add(
        ...(Array.isArray(props.class)
          ? props.class.filter((p) => p !== null)
          : [props.class])
      );
    }

    if ("data" in props && props.data !== undefined) {
      props.data.forEach((d) => (_el.dataset[d[0]] = d[1]));
    }

    if ("style" in props && props.style !== undefined) {
      for (const [name, value] of Object.entries(props.style)) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (_el.style as any)[name] = `${value}`;
      }
    }
  }

  if (children !== undefined) {
    _el.append(...(Array.isArray(children) ? children : [children]));
  }
}

export function el(
  tag: string,
  props: ElementProps = {},
  children: ElementChildren = []
) {
  const _el = document.createElement(tag);
  el_helper(_el, props, children);

  return _el;
}

export function svg(
  tag: "polygon",
  props?: ElementProps,
  children?: ElementChildren
): SVGPolygonElement;
export function svg(
  tag: "svg",
  props?: ElementProps,
  children?: ElementChildren
): SVGSVGElement;
export function svg(
  tag: string,
  props?: ElementProps,
  children?: ElementChildren
): SVGElement;
export function svg(
  tag: string,
  props: ElementProps = {},
  children: ElementChildren = []
) {
  const _svg = document.createElementNS("http://www.w3.org/2000/svg", tag);
  el_helper(_svg, props, children);
  return _svg;
}

export function div(props: ElementProps = {}, children: ElementChildren = []) {
  return el("div", props, children);
}

export function pre(props: ElementProps = {}, children: ElementChildren = []) {
  return el("pre", props, children);
}

export function path(props: ElementProps = {}, d = ""): SVGPathElement {
  const ret = svg("path", props) as SVGPathElement;
  ret.setAttribute("d", d);

  return ret;
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

export function range(size: number, start: number = 0): Array<number> {
  return [...Array(size).keys()].map((i) => i + start);
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

export function assert(condition: boolean, msg?: string): asserts condition {
  if (!condition) {
    throw new Error(msg ?? "Assertion failed");
  }
}

export function setup_drag(
  _el: HTMLElement,
  handlers: {
    on_begin_drag?: () => void;
    on_drag?: (dx: number, dy: number) => void;
    on_release_drag?: () => void;
  } = {}
) {
  let mx = 0;
  let my = 0;

  let being_dragged = false;

  document.body.addEventListener("mousemove", (e) => {
    if (being_dragged) {
      handlers.on_drag?.(e.x - mx, e.y - my);
    }

    mx = e.x;
    my = e.y;
  });

  _el.addEventListener("mousedown", (_) => {
    if (!being_dragged) {
      being_dragged = true;
      handlers.on_begin_drag?.();
      _el.classList.add("being-dragged");
    }
  });

  document.body.addEventListener("mouseup", (_) => {
    if (being_dragged) {
      being_dragged = false;
      handlers.on_release_drag?.();
      _el.classList.remove("being-dragged");
    }
  });
}

type BBox = { x: number; y: number; width: number; height: number };
export function get_curve_between_bbox(a: BBox, b: BBox) {
  // b.x += 5;
  // a.x -= 5;

  const h = 1;

  a.y += a.height / 2 - h;
  a.height = h * 2;

  b.y += b.height / 2 - h;
  b.height = h * 2;

  const p1 = [a.x + a.width, a.y];
  const p2 = [(a.x + a.width + b.x) / 2, a.y];
  const p3 = [(a.x + a.width + b.x) / 2, b.y];
  const p4 = [b.x, b.y];

  // Top
  let d = `M ${p1[0]} ${p1[1]} C ${p2[0]} ${p2[1]}, ${p3[0]} ${p3[1]}, ${p4[0]} ${p4[1]}`;

  // Bottom
  d += `L ${p4[0]} ${p4[1] + b.height} C ${p3[0]} ${p3[1] + b.height}, ${
    p2[0]
  } ${p2[1] + a.height}, ${p1[0]} ${p1[1] + a.height}`;

  return d;
}

export function get_curve_between_bbox_pivot(
  a: BBox,
  b: BBox,
  a_pivot: number,
  b_pivot: number
) {
  // b.x += 5;
  // a.x -= 5;

  const h = 1;

  a.y += a.height / 2 - h;
  a.height = h * 2;

  b.y += b.height / 2 - h;
  b.height = h * 2;

  a.x += a_pivot;
  b.x += b_pivot;

  const p1 = [a.x + a.width, a.y];
  const p2 = [(a.x + a.width + b.x) / 2, a.y];
  const p3 = [(a.x + a.width + b.x) / 2, b.y];
  const p4 = [b.x, b.y];

  // Top
  let d = `M ${p1[0] - a_pivot} ${p1[1] + a.height / 2} L ${p1[0]} ${p1[1]} C ${
    p2[0]
  } 
${p2[1]}, ${p3[0]} ${p3[1]}, ${p4[0]} ${p4[1]} L ${p4[0] - b_pivot} ${
    p4[1] + b.height / 2
  }`;

  // Bottom
  d += `L ${p4[0] - b_pivot} ${p4[1] + b.height / 2} L ${p4[0]} ${
    p4[1] + b.height
  } C ${p3[0]} ${p3[1] + b.height}, 
  ${p2[0]} ${p2[1] + a.height}, ${p1[0]} ${p1[1] + a.height}
  L ${p1[0] - a_pivot} ${p1[1] + a.height / 2}`;

  return d;
}

export function does_image_exist(url: string) {
  const img = new Image();
  img.src = url;
  return img.height != 0;
}

export function sanitize_name(path: string) {
  return path
    .replaceAll("->", "__A__")
    .replaceAll(".", "__D__")
    .replaceAll("/", "__S__")
    .replaceAll("=", "__E__");
}

export function string_to_hue(str: string) {
  return Math.floor(hash_code(str) * 360);
}

export function get_id() {
  return Math.round(Math.random() * 1000000).toString();
}

export function get_humane_name(name: string) {
  let humane = name
    .split("-")
    .map((s) => s[0].toUpperCase() + s.slice(1))
    .join(" ");

  if (name === "imessage") {
    return "iMessage";
  }

  return humane;
}

export function remap(
  value: number,
  start1: number,
  stop1: number,
  start2: number,
  stop2: number
) {
  return start2 + (stop2 - start2) * ((value - start1) / (stop1 - start1));
}

export function get_humane_pair_name(a: string, b: string) {
  return `${get_humane_name(a)} / ${get_humane_name(b)}`;
}
