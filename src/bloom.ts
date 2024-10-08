import * as bl from "@penrose/bloom";
import { State } from "./State";

export async function setup_bloom() {
  const db = new bl.DiagramBuilder(bl.canvas(400, 200), "abcd", 1);

  const { type, predicate, circle, line, build, forall, forallWhere, ensure } =
    db;

  // diagramming goes here!
  const Point = type();
  const Arrow = type();
  const Connects = predicate();

  for (let i = 0; i < 10; i++) {
    const p1 = Point();
    const p2 = Point();
    const arrow = Arrow();
    Connects(arrow, p1, p2);
  }

  const pointRad = 10;
  const pointMargin = 10;

  forall({ p: Point }, ({ p }) => {
    p.icon = circle({
      r: pointRad,
      drag: true,
    });
  });

  forallWhere(
    { a: Arrow, p: Point, q: Point },
    ({ a, p, q }) => Connects.test(a, p, q),
    ({ a, p, q }) => {
      const pq = bl.ops.vsub(q.icon.center, p.icon.center); // vector from p to q
      const pqNorm = bl.ops.vnormalize(pq); // direction from p to q
      const pStart = bl.ops.vmul(pointRad + pointMargin, pqNorm); // vector from p to line start
      const start = bl.ops.vadd(p.icon.center, pStart); // line start
      const end = bl.ops.vsub(q.icon.center, pStart); // line end

      a.icon = line({
        start: start as bl.Vec2,
        end: end as bl.Vec2,
        endArrowhead: "straight",
      });

      ensure(
        bl.constraints.greaterThan(
          bl.ops.vdist(p.icon.center, q.icon.center),
          2 * (pointRad + pointMargin) + 20
        )
      );
    }
  );

  forallWhere(
    { p: Point, q: Point },
    () => true,
    ({ p, q }) => {
      const pq = bl.ops.vsub(q.icon.center, p.icon.center); // vector from p to q
      const pqNorm = bl.ops.vnormalize(pq); // direction from p to q
      const pStart = bl.ops.vmul(pointRad + pointMargin, pqNorm); // vector from p to line start

      ensure(
        bl.constraints.greaterThan(
          bl.ops.vdist(p.icon.center, q.icon.center),
          2 * (pointRad + pointMargin) + 20
        )
      );
    }
  );

  const db_built = await build();

  // Iterate on the diagram
  let should_iterate = true;
  let max_iters = 100;
  let iter = 0;
  while (should_iterate && iter < max_iters) {
    console.log(iter);
    should_iterate = await db_built.optimizationStep();
    iter++;
  }

  const { svg } = await db_built.render();

  State.diagram_output.innerHTML = "";
  State.diagram_output.append(svg);

  return db;
}
