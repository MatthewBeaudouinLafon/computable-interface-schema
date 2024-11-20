import { Scene } from "../scene";
import { create_obj, loop_obj, Obj, remove_obj } from "./objects";

export type Singleton = Obj & {
  is_singleton: true;
};

export function create_singleton(name: string, scene: Scene): Singleton {
  return { ...create_obj(name, scene, 1), is_singleton: true };
}

export function loop_singleton(singleton: Singleton, scene: Scene) {
  loop_obj(singleton, scene);
}

export function remove_singleton(singleton: Singleton) {
  remove_obj(singleton);
}
