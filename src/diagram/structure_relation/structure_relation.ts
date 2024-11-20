import { Obj } from "../objects/objects";
import { Scene } from "../scene";
import { create_shadow, loop_shadow, remove_shadow, Shadow } from "../shadow/shadow";
import { Structure } from "../structures/structure";

// A structures B
export type StructureRelation = {
  type: "StructureRelation";
  shadows: Shadow[];
  A: Structure;
  Bs: Obj[];
};

export function create_structure_relation(A: Structure, Bs: Obj[], scene: Scene): StructureRelation {
  const shadows = Bs.map((B) => {
    let shadow: Shadow;

    if (B.n == A.n) {
      shadow = create_shadow([A], [B], scene);
    } else {
      shadow = create_shadow(A.dots.slice(0, B.n), [B], scene);
    }

    shadow.el.style.fill = B.el.style.background;

    return shadow;
  });

  return { type: "StructureRelation", A, Bs, shadows: shadows };
}

export function loop_structure_relation(structure_relation: StructureRelation, scene: Scene) {
  // TODO: Make sure the dots are placed in the same place?

  structure_relation.shadows.forEach((shadow) => loop_shadow(shadow, scene));
}

export function remove_structure_relation(structure_relation: StructureRelation) {
  structure_relation.shadows.forEach((shadow) => remove_shadow(shadow));
}
