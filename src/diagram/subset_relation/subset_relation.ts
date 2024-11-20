import { Arrow, create_arrow, loop_arrow, remove_arrow } from "../arrow/arrow";
import { Obj } from "../objects/objects";
import { Scene } from "../scene";
import "./subset_relation.css";

// A subsets B
export type SubsetRelation = {
  type: "SubsetRelation";
  A: Obj;
  B: Obj;
  arrows: Arrow[];
};

export function create_subset_relation(A: Obj, B: Obj, scene: Scene): SubsetRelation {
  // Make arrows between them
  const arrows: Arrow[] = [];
  for (let i = 0; i < A.n; i++) {
    const arrow = create_arrow(A.dots[i], B.dots[i], scene);

    B.dots[i].el.classList.add("s-subset-selected");
    A.dots[i].el.classList.add("s-subset-selected");

    arrows.push(arrow);
  }

  return { type: "SubsetRelation", A, B, arrows };
}

export function loop_subset_relation(subset: SubsetRelation, scene: Scene) {
  subset.arrows.forEach((arrow) => loop_arrow(arrow, scene));
}

export function remove_subset_relation(subset: SubsetRelation) {
  subset.arrows.forEach((arrow) => remove_arrow(arrow));
}
