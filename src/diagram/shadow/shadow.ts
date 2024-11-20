import { convexhull } from "../../utilities/convex-hull";
import { create_path_element, get_curve_points, poly_sort, union_bboxes } from "../../utilities/utilities";
import { Scene } from "../scene";
import "./shadow.css";

// Create a 'shadow' between A and B
export type Shadow = {
  el: SVGPathElement;
  As: { el: HTMLElement }[];
  Bs: { el: HTMLElement }[];
};

export function create_shadow(As: { el: HTMLElement }[], Bs: { el: HTMLElement }[], scene: Scene): Shadow {
  const el = create_path_element("s-shadow", scene.svg_el);
  return { el, As, Bs };
}

export function loop_shadow(shadow: Shadow, scene: Scene) {
  // Get the bounding boxes
  const A_bbox = union_bboxes(shadow.As.map((A) => A.el.getBoundingClientRect()));
  const B_bbox = union_bboxes(shadow.Bs.map((B) => B.el.getBoundingClientRect()));

  const scene_bbox = scene.el.getBoundingClientRect();

  const points = [A_bbox, B_bbox]
    .map((d) => {
      return [
        { x: d.left, y: d.top },
        { x: d.left, y: d.top + d.height / 2 },
        { x: d.left, y: d.top + d.height },
        { x: d.left + d.width / 2, y: d.top + d.height },
        { x: d.left + d.width, y: d.top + d.height },
        { x: d.left + d.width, y: d.top + d.height / 2 },
        { x: d.left + d.width, y: d.top },
        { x: d.left + d.width / 2, y: d.top },
      ];
    })
    .flat()
    .map((p) => {
      return { x: p.x - scene_bbox.left, y: p.y - scene_bbox.top };
    });

  const hull = convexhull.makeHull(points);

  const polygon_points = poly_sort(hull.map((p) => [p.x, p.y]));
  const curve_polygon = get_curve_points(polygon_points.flat(), 0.1, true);

  let d = `M ${curve_polygon[0]} ${curve_polygon[1]}`;

  for (let i = 2; i < curve_polygon.length; i += 2) {
    let x = curve_polygon[i];
    let y = curve_polygon[i + 1];
    d += `L ${x} ${y}`;
  }

  d += `Z`;
  shadow.el.setAttribute("d", d);
}

export function remove_shadow(shadow: Shadow) {
  shadow.el.remove();
}
