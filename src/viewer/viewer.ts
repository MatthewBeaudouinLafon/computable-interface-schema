import { Spec } from "../analogy-viewer/analogy-viewer";
import { vstack } from "../utilities/ui-utilities";
import {
  div,
  does_image_exist,
  el,
  sanitize_name,
} from "../utilities/utilities";
import "./viewer.css";

export type Viewer = {
  frag: HTMLElement;
  spec: Spec;
  view: ViewNode | undefined;
};

export async function make_viewer(spec: Spec) {
  // View
  const frag = div(".viewer");

  const viewer: Viewer = {
    frag,
    spec,
    view: undefined,
  };

  // Event listeners

  // Initial setup
  await render_viewer(viewer);

  return viewer;
}

export async function render_viewer(viewer: Viewer) {
  viewer.frag.innerHTML = "";
  viewer.view = render(viewer.spec.yaml, []);

  const ui_image = await render_ui_image(viewer);
  viewer.frag.append(ui_image);

  viewer.frag.append(div(".viewer-yaml", viewer.view.frag));
}

async function render_ui_image(viewer: Viewer) {
  const get_path = (file_name: string) =>
    `./annotations/${viewer.spec.name}/${file_name}`;

  const visited = new Set();

  const layers = viewer.spec.lookup
    .map((s) => {
      const layer_name = sanitize_name(s[0]);
      if (visited.has(layer_name)) return null;

      const path = get_path(`${layer_name}.svg`);
      const exists = does_image_exist(path);

      if (exists) {
        visited.add(layer_name);
        return el("img", {
          class: "layer",
          src: path,
          data: [["id", layer_name]],
        });
      }

      return null;
    })
    .filter((l) => l !== null);

  return div(".viewer-ui", [
    el("img", {
      class: "viewer-ui-image",
      src: get_path(`${viewer.spec.name}.png`),
    }),
    ...layers,
  ]);
}

export type ViewNode = {
  frag: HTMLElement;
  path: SpecPath;
} & (
  | {
      type: "Object";
      keys: ViewNode[];
      values: ViewNode[];
    }
  | { type: "Array"; items: ViewNode[] }
  | { type: "Primitive"; value: string }
);

export type SpecPath = (number | string | ["__KEY", string])[];

function render(thing: any, path: SpecPath): ViewNode {
  if (typeof thing === "object" && !Array.isArray(thing)) {
    return render_obj(thing, path);
  } else if (typeof thing === "object" && Array.isArray(thing)) {
    return render_array(thing, path);
  } else if (typeof thing === "string") {
    return render_primitive(thing, path);
  } else {
    throw new Error("[render] Unknown object typ");
  }
}

function render_obj(
  thing: object,
  path: SpecPath
): ViewNode & { type: "Object" } {
  const keys = Object.keys(thing).map((k) =>
    render_primitive(k, [...path, ["__KEY", k]], true)
  );
  const values = Object.entries(thing).map(([k, v]) => render(v, [...path, k]));

  const frag = vstack(
    ".v-obj",
    Object.entries(thing).map((_, i) => {
      return div(".v-obj-entry", [
        div(".v-obj-key", keys[i].frag),
        div(".v-obj-value", values[i].frag),
      ]);
    })
  );

  return { type: "Object", frag, path, keys, values };
}

function render_array(
  thing: any[],
  path: SpecPath
): ViewNode & { type: "Array" } {
  const items = thing.map((v, i) => render(v, [...path, i]));
  const frag = vstack(
    ".v-array",
    thing.map((_, i) => {
      return div(".v-array-entry", items[i].frag);
    })
  );

  return { type: "Array", frag, path, items };
}

function render_primitive(
  thing: string,
  path: SpecPath,
  is_key: boolean = false
): ViewNode & { type: "Primitive" } {
  const classes = ["v-string"];
  if (is_key) classes.push("v-key");
  const frag = div({ class: classes }, thing);
  return { type: "Primitive", frag, path, value: thing };
}

export function find_node_by(
  node: ViewNode,
  condition: (v: ViewNode) => boolean
): ViewNode | undefined {
  if (condition(node)) return node;

  if (node.type === "Array") {
    for (const item of node.items) {
      const ret = find_node_by(item, condition);
      if (ret !== undefined) return ret;
    }
  }

  if (node.type === "Object") {
    for (const k of node.keys) {
      const ret = find_node_by(k, condition);
      if (ret !== undefined) return ret;
    }

    for (const v of node.values) {
      const ret = find_node_by(v, condition);
      if (ret !== undefined) return ret;
    }
  }

  return undefined;
}
