import { hstack } from "../utilities/ui-utilities";
import {
  assert,
  div,
  get_curve_between_bbox_pivot,
  path,
  pre,
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
};

export type Analogy = {
  inputs: string[];
  analogy: [Record<string, [string, boolean]>, unknown];
  punchline: [string, string][];
  cost: number;
  conceptual_connectivity: number;
  stdout: string[];
};

export type AnalogyViewer = {
  frag: HTMLElement;
  a: Spec;
  b: Spec;
  a_viewer: Viewer;
  b_viewer: Viewer;
  analogy: Analogy;
  num_pinned: number;
  num_highlighted: number;
};

export async function make_analogy_viewer(a: Spec, b: Spec, analogy: Analogy) {
  // Sub-views
  const a_viewer = await make_viewer(a);
  const b_viewer = await make_viewer(b);

  // View
  const frag = hstack(".analogy-viewer", [
    pre(
      ".analogy-info",
      analogy.stdout.join("\n")
      // `Cost: ${analogy.cost}\n\n` +
      //   `Analogy Punchline (unpruned conceptual nodes only):\n` +
      //   analogy.punchline
      //     .map((pair) => `  ${pair[0]} <=> ${pair[1]}`)
      //     .join("\n")
    ),
    div(".analogy-viewer-viewers", [
      a_viewer.frag,
      b_viewer.frag,
      svg("svg", ".overlay"),
    ]),
  ]);

  // frag.prepend(options);

  const analogy_viewer: AnalogyViewer = {
    frag,
    a,
    b,
    a_viewer,
    b_viewer,
    analogy,
    num_pinned: 0,
    num_highlighted: 0,
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
  const { a, b, a_viewer, b_viewer, analogy } = analogy_viewer;

  // Draw connections
  const overlay = analogy_viewer.frag.querySelector(
    ".overlay"
  )! as SVGSVGElement;
  overlay.innerHTML = "";

  const container_bbox = analogy_viewer.frag.getBoundingClientRect();
  const a_viewer_bbox = a_viewer.frag.getBoundingClientRect();
  const b_viewer_bbox = b_viewer.frag.getBoundingClientRect();

  for (const [from, _to] of Object.entries(analogy.analogy[0])) {
    if (_to[1] === true) continue; // Prune

    const to = _to[0];

    const from_paths = a.lookup.filter((l) => l[0] === from).map((l) => l[1]);
    const to_paths = b.lookup.filter((l) => l[0] === to).map((l) => l[1]);

    assert(a_viewer.view !== undefined);
    assert(b_viewer.view !== undefined);

    const from_nodes = from_paths
      .map((p) =>
        find_node_by(
          a_viewer.view!,
          (n) => JSON.stringify(n.path) === JSON.stringify(p)
        )
      )
      .filter((n) => n !== undefined);
    const to_nodes = to_paths
      .map((p) =>
        find_node_by(
          b_viewer.view!,
          (n) => JSON.stringify(n.path) === JSON.stringify(p)
        )
      )
      .filter((n) => n !== undefined);

    const from_img = a_viewer.frag.querySelector(
      `#${sanitize_name(from)}`
    ) as HTMLElement | null;

    console.log(sanitize_name(from), from_img);

    const to_img = b_viewer.frag.querySelector(
      `#${sanitize_name(to)}`
    ) as HTMLElement | null;

    // Draw connections
    const from_bboxes = from_nodes
      .map((n) => n.frag.getBoundingClientRect())
      .map((b) => {
        b.x -= container_bbox.x;
        b.y -= container_bbox.y;
        return b;
      });

    const to_bboxes = to_nodes
      .map((n) => n.frag.getBoundingClientRect())
      .map((b) => {
        b.x -= container_bbox.x;
        b.y -= container_bbox.y;
        return b;
      });

    const bundle_bbox = {
      x: (a_viewer_bbox.right + b_viewer_bbox.left) / 2 - container_bbox.x,
      y:
        from_bboxes.reduce((p, curr) => p + curr.y + curr.height / 2, 0) /
        from_bboxes.length,
      width: 1,
      height: 1,
    };

    const from_connections = from_bboxes.map((b) =>
      path(
        ".connection-path",
        get_curve_between_bbox_pivot(
          b,
          bundle_bbox,
          a_viewer_bbox.right - b.right - container_bbox.x,
          0
        )
      )
    );

    const to_connections = to_bboxes.map((b) =>
      path(
        ".connection-path",
        get_curve_between_bbox_pivot(
          bundle_bbox,
          b,
          0,
          b_viewer_bbox.left - b.left - container_bbox.x
        )
      )
    );

    // Event listeners
    setup_connection_event_listeners(
      to_nodes,
      from_nodes,
      to_connections,
      from_connections,
      to_img,
      from_img,
      analogy_viewer
    );
    overlay.append(...from_connections);
    overlay.append(...to_connections);

    // for (const from_path of from_paths) {
    //   const from_node = find_node_by(
    //     a_viewer.view,
    //     (n) => JSON.stringify(n.path) === JSON.stringify(from_path)
    //   );

    //   const from_img = a_viewer.frag.querySelector(
    //     `img[data-id=${sanitize_name(from)}]`
    //   ) as HTMLElement | null;

    //   if (from_node === undefined) continue;

    //   for (const to_path of to_paths) {
    //     const to_node = find_node_by(
    //       b_viewer.view,
    //       (n) => JSON.stringify(n.path) === JSON.stringify(to_path)
    //     );

    //     if (to_node === undefined) continue;

    //     const to_img = b_viewer.frag.querySelector(
    //       `img[data-id=${sanitize_name(to)}]`
    //     ) as HTMLElement | null;

    //     const to_bbox = to_node.frag.getBoundingClientRect();
    //     to_bbox.x -= container_bbox.x + 5;
    //     to_bbox.y -= container_bbox.y;

    //     const from_bbox = from_node.frag.getBoundingClientRect();
    //     from_bbox.x -= container_bbox.x - 5;
    //     from_bbox.y -= container_bbox.y;

    //     const p = path(
    //       ".connection-path",
    //       get_curve_between_bbox(
    //         from_bbox,
    //         to_bbox
    //         // a_viewer_bbox.right - from_bbox.right - container_bbox.x - 50,
    //         // b_viewer_bbox.left - to_bbox.left - container_bbox.x + 50
    //       )
    //     );

    //     // Event listeners
    //     setup_connection_event_listeners(
    //       to_node,
    //       from_node,
    //       p,
    //       to_img,
    //       from_img
    //     );

    //     overlay.append(p);
    //   }
    // }
  }
}

const HUES = [0, 180, 45, 135, 90];

function setup_connection_event_listeners(
  to_nodes: ViewNode[],
  from_nodes: ViewNode[],
  from_connections: SVGPathElement[],
  to_connections: SVGPathElement[],
  to_img: HTMLElement | null,
  from_img: HTMLElement | null,
  analogy_viewer: AnalogyViewer
) {
  const to_frags = to_nodes.map((n) => n.frag);
  const from_frags = from_nodes.map((n) => n.frag);
  const frags = [...to_frags, ...from_frags];

  frags.forEach((frag) => frag.classList.add("matched"));

  let clicked = false;

  let affected = [
    ...frags,
    ...from_connections,
    ...to_connections,
    to_img,
    from_img,
  ].filter((el) => el !== null);

  let update_focused = () => {
    if (analogy_viewer.num_highlighted > 0 || analogy_viewer.num_pinned > 0) {
      analogy_viewer.frag.classList.add("focused");
    } else {
      analogy_viewer.frag.classList.remove("focused");
    }
  };

  frags.forEach((el) => {
    el.addEventListener("mouseenter", () => {
      if (affected.some((el) => el.classList.contains("pinned"))) return;

      affected.forEach((el) => el.classList.add("highlight"));

      const hue_index = analogy_viewer.num_pinned % HUES.length;
      const hue = HUES[hue_index];
      affected.forEach((el) => (el.style.filter = `hue-rotate(${hue}deg)`));

      analogy_viewer.num_highlighted++;
      update_focused();
    });

    el.addEventListener("mouseleave", () => {
      if (affected.some((el) => el.classList.contains("pinned"))) return;

      affected.forEach((el) => el.classList.remove("highlight"));
      affected.forEach((el) => (el.style.filter = ``));

      analogy_viewer.num_highlighted--;
      update_focused();
    });

    el.addEventListener("mousedown", () => {
      if (clicked) {
        clicked = false;
        affected.forEach((el) => el.classList.remove("pinned"));
        affected.forEach((el) => (el.style.filter = ``));
        analogy_viewer.num_pinned--;
      } else {
        const hue_index = analogy_viewer.num_pinned % HUES.length;
        const hue = HUES[hue_index];
        clicked = true;
        affected.forEach((el) => el.classList.add("pinned"));
        affected.forEach((el) => (el.style.filter = `hue-rotate(${hue}deg)`));
        analogy_viewer.num_pinned++;
      }

      update_focused();
    });
  });
}
