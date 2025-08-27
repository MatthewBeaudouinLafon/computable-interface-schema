import { hstack } from "../utilities/ui-utilities";
import {
  assert,
  get_curve_between_bbox_pivot,
  path,
  sanitize_name,
  svg,
} from "../utilities/utilities";
import "./analogy-viewer.css";
import {
  find_node_by,
  make_viewer,
  render_viewer,
  SpecPath,
  Viewer,
  ViewNode,
} from "./viewer/viewer";

export type Spec = {
  name: string;
  yaml: object;
  lookup: [string, SpecPath][];
  image_names: string[];
};

export type Analogy = {
  inputs: string[];
  analogy: Record<string, [string, boolean]>;
};

export type AnalogyViewer = {
  frag: HTMLElement;
  a: Spec;
  b: Spec;
  a_viewer: Viewer;
  b_viewer: Viewer;
  all_analogies: Analogy[];
};

export async function make_analogy_viewer(
  a: Spec,
  b: Spec,
  all_analogies: Analogy[]
) {
  // Sub-views
  const a_viewer = await make_viewer(a);
  const b_viewer = await make_viewer(b);

  // View
  const frag = hstack(".analogy-editor", [
    a_viewer.frag,
    b_viewer.frag,
    svg("svg", ".overlay"),
  ]);

  const analogy_viewer: AnalogyViewer = {
    frag,
    a,
    b,
    a_viewer,
    b_viewer,
    all_analogies,
  };

  // Event listeners

  // Initial setup
  await analogy_viewer_update_spec(analogy_viewer, a, b);

  return analogy_viewer;
}

export async function analogy_viewer_update_spec(
  analogy_viewer: AnalogyViewer,
  a: Spec,
  b: Spec
) {
  const { a_viewer, b_viewer } = analogy_viewer;

  analogy_viewer.a = a;
  analogy_viewer.b = b;

  a_viewer.spec = a;
  b_viewer.spec = b;

  await render_viewer(a_viewer);
  await render_viewer(b_viewer);

  // Show analogies
  setTimeout(() => analogy_viewer_draw_connections(analogy_viewer), 1000);
}

function analogy_viewer_draw_connections(analogy_viewer: AnalogyViewer) {
  const { a, b, a_viewer, b_viewer } = analogy_viewer;

  // Find the analogy
  const analogy = analogy_viewer.all_analogies.find(
    (an) => an.inputs.includes(a.name) && an.inputs.includes(b.name)
  );
  if (analogy === undefined) return;

  // Draw connections
  const overlay = analogy_viewer.frag.querySelector(
    ".overlay"
  )! as SVGSVGElement;
  overlay.innerHTML = "";

  const container_bbox = analogy_viewer.frag.getBoundingClientRect();
  const a_viewer_bbox = a_viewer.frag.getBoundingClientRect();
  const b_viewer_bbox = b_viewer.frag.getBoundingClientRect();

  for (const [from, _to] of Object.entries(analogy.analogy)) {
    if (_to[1] === true) continue; // Prune

    const to = _to[0];

    const from_paths = a.lookup.filter((l) => l[0] === from).map((l) => l[1]);
    const to_paths = b.lookup.filter((l) => l[0] === to).map((l) => l[1]);

    assert(a_viewer.view !== undefined);
    assert(b_viewer.view !== undefined);

    for (const from_path of from_paths) {
      const from_node = find_node_by(
        a_viewer.view,
        (n) => JSON.stringify(n.path) === JSON.stringify(from_path)
      );

      const from_img = a_viewer.frag.querySelector(
        `img[data-id=${sanitize_name(from)}]`
      ) as HTMLElement | null;

      if (from_node === undefined) continue;

      for (const to_path of to_paths) {
        const to_node = find_node_by(
          b_viewer.view,
          (n) => JSON.stringify(n.path) === JSON.stringify(to_path)
        );

        if (to_node === undefined) continue;

        const to_img = b_viewer.frag.querySelector(
          `img[data-id=${sanitize_name(to)}]`
        ) as HTMLElement | null;

        const to_bbox = to_node.frag.getBoundingClientRect();
        to_bbox.x -= container_bbox.x + 5;
        to_bbox.y -= container_bbox.y;

        const from_bbox = from_node.frag.getBoundingClientRect();
        from_bbox.x -= container_bbox.x - 5;
        from_bbox.y -= container_bbox.y;

        const p = path(
          ".connection-path",
          get_curve_between_bbox_pivot(
            from_bbox,
            to_bbox,
            a_viewer_bbox.right - from_bbox.right - container_bbox.x,
            b_viewer_bbox.left - to_bbox.left - container_bbox.x
          )
        );

        // Event listeners
        setup_connection_event_listeners(
          to_node,
          from_node,
          p,
          to_img,
          from_img
        );

        overlay.append(p);
      }
    }
  }
}

function setup_connection_event_listeners(
  to_node: ViewNode,
  from_node: ViewNode,
  p: SVGPathElement,
  to_img: HTMLElement | null,
  from_img: HTMLElement | null
) {
  to_node.frag.classList.add("matched");
  from_node.frag.classList.add("matched");

  let clicked = false;

  [to_node.frag, from_node.frag].forEach((el) => {
    el.addEventListener("mouseenter", () => {
      [to_node.frag, to_img, from_node.frag, from_img, p].forEach((el) =>
        el?.classList.add("highlight")
      );
    });

    el.addEventListener("mouseleave", () => {
      [to_node.frag, to_img, from_node.frag, from_img, p].forEach((el) =>
        el?.classList.remove("highlight")
      );
    });

    el.addEventListener("mousedown", () => {
      if (clicked) {
        clicked = false;
        [to_node.frag, to_img, from_node.frag, from_img, p].forEach((el) =>
          el?.classList.remove("pinned")
        );
      } else {
        clicked = true;
        [to_node.frag, to_img, from_node.frag, from_img, p].forEach((el) =>
          el?.classList.add("pinned")
        );
      }
    });
  });
}
