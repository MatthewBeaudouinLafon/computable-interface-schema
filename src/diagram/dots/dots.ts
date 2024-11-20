import { create_el } from "../../utilities/utilities";
import { Obj } from "../objects/objects";
import { Scene } from "../scene";
import { Structure } from "../structures/structure";
import "./dots.css";

export type Dot = {
  el: HTMLElement;
  x: number;
  y: number;
};

export function create_dot(scene: Scene): Dot {
  return {
    el: create_el("div", "s-dot", scene.el),
    x: Math.random(),
    y: Math.random(),
  };
}

export function loop_dots(dot: Dot, scene: Scene, parent: Obj | Structure) {
  const { width, height } = scene.el.getBoundingClientRect();

  dot.el.style.left = `${parent.x + dot.x + width / 2 - 4}px`;
  dot.el.style.top = `${parent.y + dot.y + height / 2 - 4}px`;
}

export function remove_dot(dot: Dot) {
  dot.el.remove();
}
