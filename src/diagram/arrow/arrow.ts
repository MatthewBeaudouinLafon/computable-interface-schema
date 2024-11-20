import { create_path_element, create_polygon_element, get_bbox_arrow_paths } from "../../utilities/utilities";
import { Dot } from "../dots/dots";
import { Scene } from "../scene";
import "./arrow.css";

export type Arrow = {
  path: SVGPathElement;
  arrow_head: SVGPolygonElement;
  from: Dot;
  to: Dot;
  pad_end: number;
  arrow_scale: number;
};

export function create_arrow(from: Dot, to: Dot, scene: Scene, pad_end: number = 8, arrow_scale: number = 1): Arrow {
  const path = create_path_element("s-arrow", scene.svg_el) as SVGPathElement;
  const arrow_head = create_polygon_element("s-arrow-head", scene.svg_el) as SVGPolygonElement;

  return {
    path,
    arrow_head,
    from,
    to,
    pad_end,
    arrow_scale,
  };
}

export function loop_arrow(arrow: Arrow, scene: Scene) {
  const from_bbox = arrow.from.el.getBoundingClientRect();
  const to_bbox = arrow.to.el.getBoundingClientRect();

  const scene_bbox = scene.el.getBoundingClientRect();

  from_bbox.x -= scene_bbox.x;
  to_bbox.x -= scene_bbox.x;

  from_bbox.y -= scene_bbox.y;
  to_bbox.y -= scene_bbox.y;

  const { arrow_head_points, arrow_head_transform, path_points } = get_bbox_arrow_paths(
    from_bbox,
    to_bbox,
    {
      padEnd: arrow.pad_end,
      padStart: 0,
    },
    arrow.arrow_scale,
  );

  arrow.path.setAttribute("d", path_points);
  arrow.arrow_head.setAttribute("transform", arrow_head_transform);
  arrow.arrow_head.setAttribute("points", arrow_head_points);
}

export function remove_arrow(arrow: Arrow) {
  arrow.arrow_head.remove();
  arrow.path.remove();
}
