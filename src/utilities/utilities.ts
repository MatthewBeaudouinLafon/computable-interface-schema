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
      props.data.forEach((d) => _el.setAttribute(d[0], d[1]));
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
  tag: string,
  props: ElementProps,
  children?: ElementChildren
): SVGPolygonElement;
export function svg(
  tag: "svg",
  props: ElementProps,
  children?: ElementChildren
): SVGSVGElement;
export function svg(
  tag: string,
  props: ElementProps,
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
