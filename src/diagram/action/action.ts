import { create_el } from "../../utilities/utilities";
import { Scene } from "../scene";
import "./action.css";

export type Action = {
  el: HTMLElement;

  type: "Action";
  name: string;

  x: number;
  y: number;
};

export function create_action(name: string, scene: Scene): Action {
  const el = create_el("button", ["pushable", "s-action"], scene.el);
  el.innerHTML = name;

  return {
    el,
    type: "Action",
    name,
    x: 0,
    y: 0,
  };
}

export function loop_action(action: Action, scene: Scene) {
  const { width: scene_width, height: scene_height } = scene.el.getBoundingClientRect();
  const { width, height } = action.el.getBoundingClientRect();

  action.el.style.left = `${action.x + scene_width / 2 - width / 2}px`;
  action.el.style.top = `${action.y + scene_height / 2 - height / 2}px`;
}

export function remove_action(action: Action) {
  action.el.remove();
}
