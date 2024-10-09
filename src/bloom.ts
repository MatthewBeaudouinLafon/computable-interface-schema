import * as bl from "@penrose/bloom";
import { disjoint } from "@penrose/bloom/dist/core/constraints";
import { State } from "./State";
import { get_all_prolog_query_results } from "./utilities";

export async function setup_bloom() {
  // Get all the objects(X).

  const objects: string[] = get_all_prolog_query_results("objects(X)").map(
    (v) => v.X
  );

  const subsets: [string, string][] = get_all_prolog_query_results(
    "X subsets Y"
  ).map((v) => [v.X, v.Y]);

  const db = new bl.DiagramBuilder(bl.canvas(400, 400), "abcd", 1);

  const {
    type,
    predicate,
    circle,
    line,
    text,
    build,
    forall,
    forallWhere,
    ensure,
    encourage,
  } = db;

  // Types
  const Arrow = type();
  const Objects = type();
  const ObjectLabels = type();
  const Subsets = predicate();
  const Labeled = predicate();

  const vObjectLabels = objects.map((obj) => {
    const t = ObjectLabels();

    t.icon = text({
      string: obj,
      fillColor: [8 / 255, 77 / 255, 189 / 255, 1],
    });

    return t;
  });

  const pointRad = 2;
  const pointMargin = 0;

  const vObjects = objects.map((_) => {
    const t = Objects();

    t.icon = circle({
      r: pointRad,
      fillColor: [0, 0, 0, 1],
    });

    return t;
  });

  vObjects.forEach((obj, i) => {
    Labeled(obj, vObjectLabels[i]);
  });

  for (const [a, b] of subsets) {
    const ai = objects.indexOf(a);
    const bi = objects.indexOf(b);

    const arrow = Arrow();

    Subsets(vObjects[ai], vObjects[bi], arrow);
  }

  forallWhere(
    { a: Arrow, o1: Objects, o2: Objects },
    ({ o1, o2, a }) => Subsets.test(o1, o2, a),
    ({ o1, o2, a }) => {
      const pq = bl.ops.vsub(o2.icon.center, o1.icon.center); // vector from p to q
      const pqNorm = bl.ops.vnormalize(pq); // direction from p to q
      const pStart = bl.ops.vmul(pointRad + pointMargin, pqNorm); // vector from p to line start
      const start = bl.ops.vadd(o1.icon.center, pStart); // line start
      const end = bl.ops.vsub(o2.icon.center, pStart); // line end

      a.icon = line({
        start: start as bl.Vec2,
        end: end as bl.Vec2,
        endArrowhead: "straight",
        endArrowheadSize: 0.7,
      });
    }
  );

  // forall({ t: Text }, ({ t }) => {
  //   t.icon = text({
  //     string: `:${Math.random() > 0.5 ? "(" : ")"}`,
  //   });
  // });

  // const arrow = Arrow();
  // Connects(arrow, p1, p2);

  // forall({ p: Point }, ({ p }) => {
  //   p.icon = circle({
  //     r: pointRad,
  //     drag: true,
  //   });
  // });

  forallWhere(
    { p: Objects, t: ObjectLabels },
    ({ p, t }) => Labeled.test(p, t),
    ({ p, t }) => {
      const pq = bl.ops.vsub(bl.ops.vadd(p.icon.center, [0, 8]), t.icon.center);

      ensure(bl.constraints.lessThan(bl.ops.vnorm(pq), 0.01));
    }
  );

  forallWhere(
    { p: Objects, q: Objects },
    () => true,
    ({ p, q }) => {
      ensure(
        bl.constraints.greaterThan(
          bl.ops.vdist(p.icon.center, q.icon.center),
          2 * (pointRad + pointMargin) + 20
        )
      );

      const d = bl.ops.vnorm(bl.ops.vsub(p.icon.center, q.icon.center));
      const k = 1.0;
      const L = 150;

      const dL = bl.sub(d, L);

      const target = bl.div(bl.mul(k, bl.mul(dL, dL)), 2);

      encourage(bl.eq(0, target));
      // scalar d = norm( x1 - x2 )
      // scalar k = 1. -- spring stiffness
      // scalar L = global.targetEdgeLength -- rest length
      // encourage equal( 0., k*(d-L)*(d-L)/2. ) -- minimize ½ k(d-L)²
    }
  );

  forall({ p: ObjectLabels, q: ObjectLabels }, ({ p, q }) => {
    ensure(disjoint(p.icon, q.icon));
  });

  // disjoint(p.icon, q.icon, 20)

  const db_built = await build();

  // Iterate on the diagram
  let should_iterate = true;
  let max_iters = 100;
  let iter = 0;
  while (should_iterate && iter < max_iters) {
    should_iterate = await db_built.optimizationStep();
    iter++;
  }

  const { svg } = await db_built.render();

  State.diagram_output.innerHTML = "";
  State.diagram_output.append(svg);

  return db;
}
