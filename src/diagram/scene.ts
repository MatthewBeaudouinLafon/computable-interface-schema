import * as force from "d3-force";
import { create_el, create_svg_element, get_all_prolog_query_results, setup_drag } from "../utilities/utilities";
import { Action, create_action, loop_action, remove_action } from "./action/action";
import { create_obj, loop_obj, Obj, remove_obj } from "./objects/objects";
import { create_singleton } from "./objects/singleton";
import "./scene.css";
import {
  create_structure_relation,
  loop_structure_relation,
  remove_structure_relation,
  StructureRelation,
} from "./structure_relation/structure_relation";
import { create_structure, loop_structure, remove_structure, Structure, StructureType } from "./structures/structure";
import {
  create_subset_relation,
  loop_subset_relation,
  remove_subset_relation,
  SubsetRelation,
} from "./subset_relation/subset_relation";

export type SceneNode = Structure | Obj | Action;
export type SceneRelation = SubsetRelation | StructureRelation;

export type Scene = {
  el: HTMLElement;
  svg_el: SVGSVGElement;
  nodes: SceneNode[];
  relations: SceneRelation[];
  simulation: force.Simulation<any, any>;
};

export function create_scene(parent: HTMLElement): Scene {
  const el = create_el("div", "scene", parent);
  const svg_el = create_svg_element("scene-svg", el);

  const simulation = force.forceSimulation();
  simulation.force("charge", force.forceManyBody().strength(50));
  simulation.force("center", force.forceRadial(10));
  simulation.force("collision", force.forceCollide(50));
  simulation.stop();

  return { el, svg_el, nodes: [], relations: [], simulation };
}

export function update_scene(scene: Scene) {
  // --- Clean up
  const previous_positions = scene.nodes.map((g) => {
    return { name: g.name, x: g.x, y: g.y };
  });
  scene.nodes.forEach((d) => remove_node(d));
  scene.relations.forEach((r) => remove_relation(r));
  scene.nodes = [];
  scene.relations = [];

  // --- Visualize objects
  const obj_names = get_all_prolog_query_results("objects(X).").map((obj) => obj.X) as string[];
  const singleton_names = get_all_prolog_query_results("singleton(X).").map((obj) => obj.X) as string[];

  for (const obj_name of obj_names) {
    // Skip duplicates
    if (scene.nodes.find((g) => g.name == obj_name)) continue;

    let obj: Obj;

    if (singleton_names.includes(obj_name)) {
      obj = create_singleton(obj_name, scene);
    } else {
      obj = create_obj(obj_name, scene);
    }

    scene.nodes.push(obj);
  }

  // --- Show all structures
  const all_linear_structures = get_all_prolog_query_results("linear(X).").map((obj) => obj.X) as string[];

  for (const structure_name of all_linear_structures) {
    const structure = create_structure(structure_name, StructureType.Linear, scene);
    scene.nodes.push(structure);
  }

  // --- Show all actions
  const all_action_names = get_all_prolog_query_results("action(X).").map((obj) => obj.X) as string[];

  for (const action_name of all_action_names) {
    const action = create_action(action_name, scene);
    scene.nodes.push(action);
  }

  // --- Enforce subsets
  const all_subsets: [string, string][] = get_all_prolog_query_results("A subsets B.", {
    do_not_include_logical_rules: true,
  }).map((s) => [(s as any).A as string, (s as any).B as string]);

  for (const [A_name, B_name] of all_subsets) {
    const A_index = scene.nodes.findIndex((g) => g.type == "Obj" && g.name == A_name);
    const B_index = scene.nodes.findIndex((g) => g.type == "Obj" && g.name == B_name);

    if (A_index == -1 || B_index == -1) continue;
    if (A_index == B_index) continue;

    const A = scene.nodes[A_index] as Obj;
    const B = scene.nodes[B_index] as Obj;

    // Pick a few elements from B to map to A
    const n_picked = Math.min(A.n, Math.max(1, Math.floor(B.n * 0.3)));

    // Remove current 'A'
    remove_obj(A);

    // Create a new 'A' with n_picked dots
    scene.nodes[A_index] = create_obj(A.name, scene, n_picked);
  }

  // --- Create structure relations
  const all_structure_relations = get_all_prolog_query_results("A structures B.", {
    do_not_include_logical_rules: true,
  }).map((s) => [(s as any).A as string, (s as any).B as string]);

  for (const [A_name, B_name] of all_structure_relations) {
    const A_index = scene.nodes.findIndex((g) => g.type == "Structure" && g.name == A_name);
    const B_index = scene.nodes.findIndex((g) => g.type == "Obj" && g.name == B_name);

    if (A_index == -1 || B_index == -1) continue;

    let A = scene.nodes[A_index] as Structure;
    let B = scene.nodes[B_index] as Obj;

    // Remove the current 'A'
    remove_structure(A);

    // Create a new 'A' with B.n dots
    A = create_structure(A.name, A.structure_type, scene, B.n);
    scene.nodes[A_index] = A;

    // Copy the style of 'B' dots
    for (const dot of A.dots) {
      if (B.dots.length > 0) {
        dot.el.style.background = B.dots[0].el.style.background;
        dot.el.style.transform = B.dots[0].el.style.transform;
        dot.el.style.boxShadow = B.dots[0].el.style.boxShadow;
      }
    }

    for (const arrow of A.arrows) {
      arrow.arrow_scale = 1;
      arrow.pad_end = 5;
    }
  }

  for (const [A_name, B_name] of all_structure_relations) {
    const A = scene.nodes.find((g) => g.type == "Structure" && g.name == A_name) as Structure;
    const B = scene.nodes.find((g) => g.type == "Obj" && g.name == B_name) as Obj;

    if (A == null || B == null) continue;

    const other_subset_names = get_all_prolog_query_results(`X subsets ${B.name}.`).map((obj) => obj.X) as string[];
    const other_subsets = other_subset_names
      .map((name) => scene.nodes.find((g) => g.type == "Obj" && g.name == name))
      .filter((g) => g != null) as Obj[];

    const structures = create_structure_relation(A, [B, ...other_subsets], scene);
    scene.relations.push(structures);
  }

  // --- Actions
  const navigations = get_all_prolog_query_results("A moves B along C within D.", {
    do_not_include_logical_rules: true,
  }).map((s) => [(s as any).A as string, (s as any).B as string, (s as any).C as string, (s as any).D as string]);

  for (const navigation of navigations) {
    const [action_name, obj_name, structure_name, superset_name] = navigation;

    const action = scene.nodes.find((g) => g.type == "Action" && g.name == action_name);
    if (action == null) continue;

    const obj = scene.nodes.find((g) => g.type == "Obj" && g.name == obj_name) as Obj;
    if (obj == null) continue;

    const structure = scene.nodes.find((g) => g.type == "Structure" && g.name == structure_name) as Structure;
    if (structure == null) continue;

    const superset = scene.nodes.find((g) => g.type == "Obj" && g.name == superset_name);
    if (superset == null) continue;

    const structure_relations = scene.relations.filter(
      (rel) => rel.type == "StructureRelation" && rel.A.name == structure_name,
    ) as StructureRelation[];

    let curr_i = 0;
    action.el.addEventListener("click", () => {
      curr_i += 1;
      curr_i = curr_i % structure.dots.length;

      for (const rel of structure_relations) {
        const B_index = rel.Bs.findIndex((n) => n == obj);
        if (B_index == -1) continue;

        const shadow = rel.shadows[B_index];

        shadow.As = structure.dots.slice(curr_i, curr_i + obj.n);
      }
    });
  }

  // --- Create subset arrows
  for (const [A_name, B_name] of all_subsets) {
    const A = scene.nodes.find((g) => g.type == "Obj" && g.name == A_name) as Obj;
    const B = scene.nodes.find((g) => g.type == "Obj" && g.name == B_name) as Obj;

    if (A == null || B == null) continue;
    if (A == B) continue;

    // Pick a few elements from B to map to A
    const subset = create_subset_relation(A, B, scene);
    scene.relations.push(subset);
  }

  // --- Re-apply positions
  for (const node of scene.nodes) {
    const position = previous_positions.find((p) => p.name == node.name);

    if (position != null) {
      node.x = position.x;
      node.y = position.y;

      loop_node(node, scene);
    }
  }

  // --- Setup dragging
  for (let node_i = 0; node_i < scene.nodes.length; node_i++) {
    const node = scene.nodes[node_i];

    const on_begin_drag = () => {
      // Freeze all nodes
      scene.simulation.nodes().forEach((node, i) => {
        if (i != node_i) return;

        node.fx = node.x;
        node.fy = node.y;
      });
    };

    const on_drag = (dx: number, dy: number) => {
      const node = scene.simulation.nodes()[node_i];
      node.x += dx;
      node.y += dy;

      node.fx = node.x;
      node.fy = node.y;
    };

    const on_release_drag = () => {
      // Release all nodes
      scene.simulation.nodes().forEach((node, i) => {
        if (i != node_i) return;

        node.fx = null;
        node.fy = null;
      });
    };

    setup_drag("label_el" in node ? node.label_el : node.el, on_begin_drag, on_drag, on_release_drag);
  }

  // --- Setup the simulation
  // TODO: See if scene.nodes can be passed directly into simulation.nodes?
  const nodes = scene.nodes.map((group) => ({ x: group.x, y: group.y }));
  scene.simulation.nodes(nodes);
}

export function loop_scene(scene: Scene) {
  scene.simulation.tick(1);

  scene.simulation.nodes().forEach((node, i) => {
    const scene_node = scene.nodes[i];

    // Constrain the position
    const { width, height } = scene.el.getBoundingClientRect();
    node.x = Math.max(Math.min(node.x, width / 2), -width / 2);
    node.y = Math.max(Math.min(node.y, height / 2), -height / 2);

    // Update the position
    scene_node.x = node.x;
    scene_node.y = node.y;
  });

  scene.nodes.forEach((node) => loop_node(node, scene));
  scene.relations.forEach((relation) => loop_relation(relation, scene));
}

function remove_node(node: SceneNode) {
  switch (node.type) {
    case "Obj":
      return remove_obj(node);
    case "Structure":
      return remove_structure(node);
    case "Action":
      return remove_action(node);
  }
}

function remove_relation(relation: SceneRelation) {
  switch (relation.type) {
    case "SubsetRelation":
      return remove_subset_relation(relation);
    case "StructureRelation":
      return remove_structure_relation(relation);
  }
}

function loop_node(node: SceneNode, scene: Scene) {
  switch (node.type) {
    case "Obj":
      return loop_obj(node, scene);
    case "Structure":
      return loop_structure(node, scene);
    case "Action":
      return loop_action(node, scene);
  }
}

function loop_relation(relation: SceneRelation, scene: Scene) {
  switch (relation.type) {
    case "SubsetRelation":
      return loop_subset_relation(relation, scene);
    case "StructureRelation":
      return loop_structure_relation(relation, scene);
  }
}
