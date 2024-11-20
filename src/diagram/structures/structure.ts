import * as force from "d3-force";
import { create_el, range } from "../../utilities/utilities";
import { Arrow, create_arrow, loop_arrow, remove_arrow } from "../arrow/arrow";
import { create_dot, Dot, loop_dots, remove_dot } from "../dots/dots";
import { Scene } from "../scene";
import "./structure.css";

export enum StructureType {
  "Linear",
  "Digraph",
}

export type Structure = {
  type: "Structure";
  el: HTMLElement;
  label_el: HTMLElement;

  name: string;
  structure_type: StructureType;
  dots: Dot[];
  arrows: Arrow[];

  simulation: force.Simulation<any, any>;

  x: number;
  y: number;

  n: number;
};

export function create_structure(name: string, type: StructureType, scene: Scene, n: number = 8): Structure {
  const el = create_el("div", "s-structure", scene.el);
  const label_el = create_el("div", "s-structure-label", scene.el);
  label_el.innerText = name;
  // el.style.background = `rgba(0,0,0,0.05)`;
  el.style.borderColor = `rgba(0,0,0,0.2)`;

  if (type == StructureType.Digraph) {
    n = 12;
  }

  const dots = range(n).map(() => {
    const dot = create_dot(scene);
    dot.el.style.background = `rgba(0,0,0,0)`;
    dot.el.style.transform = `scale(0.2)`;
    dot.el.style.border = `none`;
    dot.el.style.boxShadow = `none`;

    return dot;
  });

  let arrows: Arrow[] = [];

  let links: {
    source: { x: number; y: number };
    target: { x: number; y: number };
  }[] = [];
  let nodes = dots.map((d) => ({ x: d.x, y: d.y }));

  if (type == StructureType.Linear) {
    for (let i = 0; i < n - 1; i++) {
      arrows.push(create_arrow(dots[i], dots[i + 1], scene, 2, 0.5));
      links.push({ source: nodes[i], target: nodes[i + 1] });
    }
  }

  const simulation = force.forceSimulation(nodes);

  simulation.stop();
  simulation.force("charge", force.forceManyBody().strength(0.1));
  simulation.force("center", force.forceCenter().strength(1));
  simulation.force("collision", force.forceCollide(12));
  simulation.force("link", force.forceLink(links).distance(20));

  return {
    type: "Structure",
    name,
    el,
    structure_type: type,
    n,
    label_el,
    dots,
    arrows,
    simulation,
    x: 0,
    y: 0,
  };
}

export function loop_structure(structure: Structure, scene: Scene) {
  structure.simulation.tick(1);

  structure.simulation.nodes().forEach((node, i) => {
    structure.dots[i].x = node.x;
    structure.dots[i].y = node.y;
  });

  structure.dots.forEach((dot) => loop_dots(dot, scene, structure));
  structure.arrows.forEach((arrow) => loop_arrow(arrow, scene));

  const { width: scene_width, height: scene_height } = scene.el.getBoundingClientRect();

  const dots_min_x = Math.min(...structure.dots.map((d) => d.x));
  const dots_max_x = Math.max(...structure.dots.map((d) => d.x));

  const dots_min_y = Math.min(...structure.dots.map((d) => d.y));
  const dots_max_y = Math.max(...structure.dots.map((d) => d.y));

  const width = dots_max_x - dots_min_x + 20;
  const height = dots_max_y - dots_min_y + 20;

  structure.el.style.width = `${width}px`;
  structure.el.style.height = `${height}px`;

  structure.el.style.left = `${structure.x + scene_width / 2 - width / 2}px`;
  structure.el.style.top = `${structure.y + scene_height / 2 - height / 2}px`;

  structure.label_el.style.left = `${structure.x + scene_width / 2 - width / 2}px`;
  structure.label_el.style.top = `${structure.y + scene_height / 2 - height / 2 - 25}px`;
  structure.label_el.style.width = `${width}px`;
}

export function remove_structure(structure: Structure) {
  structure.el.remove();
  structure.label_el.remove();
  structure.dots.forEach((dot) => remove_dot(dot));
  structure.arrows.forEach((arrow) => remove_arrow(arrow));
}
