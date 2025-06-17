export function el(
  tag: string,
  props: Partial<
    | HTMLElement
    | { class: string | (string | null)[] }
    | { data: string[][] }
    | { style: Partial<CSSStyleDeclaration> }
  >,
  children?: HTMLElement[] | HTMLElement,
  parent?: HTMLElement
) {
  const el = document.createElement(tag);

  if ("class" in props && props.class !== undefined) {
    el.classList.add(
      ...(Array.isArray(props.class)
        ? props.class.filter((p) => p !== null)
        : [props.class])
    );
  }

  if ("data" in props && props.data !== undefined) {
    props.data.forEach((d) => el.setAttribute(d[0], d[1]));
  }

  if (children !== undefined) {
    el.append(...(Array.isArray(children) ? children : [children]));
  }

  parent?.append(el);
  Object.assign(el, props ?? {});

  return el;
}

export function div(
  props: Partial<
    | HTMLElement
    | { class: string | (string | null)[] }
    | { data: string[][] }
    | { style: Partial<CSSStyleDeclaration> }
  >,
  children?: HTMLElement[] | HTMLElement,
  parent?: HTMLElement
) {
  return el("div", props, children, parent);
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
