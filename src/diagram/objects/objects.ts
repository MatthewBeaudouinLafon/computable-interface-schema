import * as force from "d3-force";
import { create_el, hash_code, range } from "../../utilities/utilities";
import { create_dot, Dot, loop_dots, remove_dot } from "../dots/dots";
import { Scene } from "../scene";
import "./objects.css";

export type Obj = {
  type: "Obj";

  el: HTMLElement;
  label_el: HTMLElement;
  name: string;
  dots: Dot[];
  simulation: force.Simulation<any, any>;

  x: number;
  y: number;

  n: number;
};

export function create_obj(name: string, scene: Scene, n: number = 12): Obj {
  const el = create_el("div", "s-obj", scene.el);
  const label_el = create_el("div", "s-obj-label", scene.el);
  label_el.innerText = name;
  const hue = Math.floor(hash_code(name) * 360);
  el.style.background = `oklch(0.7 0.4 ${hue}deg / 0.1)`;
  el.style.borderColor = `oklch(0.7 0.4 ${hue}deg / 0.25)`;

  const dots = range(n).map(() => {
    const dot = create_dot(scene);
    dot.el.style.background = `oklch(0.7 0.4 ${hue}deg / 0.5)`;

    return dot;
  });

  // TODO: See if dots can be directly used in forceSimulation
  const simulation = force.forceSimulation(dots.map((d) => ({ x: d.x, y: d.y })));

  simulation.stop();
  simulation.force("charge", force.forceManyBody().strength(1));
  simulation.force("center", force.forceCenter());
  simulation.force("collision", force.forceCollide(8));

  return {
    type: "Obj",
    name,
    el,
    n,
    label_el,
    dots,
    simulation,
    x: 0,
    y: 0,
  };
}

export function loop_obj(obj: Obj, scene: Scene) {
  obj.simulation.tick(1);

  obj.simulation.nodes().forEach((node, i) => {
    obj.dots[i].x = node.x;
    obj.dots[i].y = node.y;
  });

  obj.dots.forEach((dot) => loop_dots(dot, scene, obj));

  const { width: scene_width, height: scene_height } = scene.el.getBoundingClientRect();

  const dots_min_x = Math.min(...obj.dots.map((d) => d.x));
  const dots_max_x = Math.max(...obj.dots.map((d) => d.x));

  const dots_min_y = Math.min(...obj.dots.map((d) => d.y));
  const dots_max_y = Math.max(...obj.dots.map((d) => d.y));

  const width = dots_max_x - dots_min_x + 20;
  const height = dots_max_y - dots_min_y + 20;

  obj.el.style.width = `${width}px`;
  obj.el.style.height = `${height}px`;

  obj.el.style.left = `${obj.x + scene_width / 2 - width / 2}px`;
  obj.el.style.top = `${obj.y + scene_height / 2 - height / 2}px`;

  obj.label_el.style.left = `${obj.x + scene_width / 2 - width / 2}px`;
  obj.label_el.style.top = `${obj.y + scene_height / 2 - height / 2 - 25}px`;
  obj.label_el.style.width = `${width}px`;
}

export function remove_obj(obj: Obj) {
  obj.el.remove();
  obj.label_el.remove();
  obj.dots.forEach((dot) => remove_dot(dot));
}
