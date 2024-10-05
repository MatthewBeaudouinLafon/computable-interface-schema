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
