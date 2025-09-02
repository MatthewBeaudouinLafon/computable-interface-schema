import { Analogy } from "../analogy-viewer/analogy-viewer";
import { div, remap } from "../utilities/utilities";
import "./cost-matrix.css";

export type CostMatrix = {
  frag: HTMLElement;
  analogies: Analogy[];
};

export function make_cost_matrix(analogies: Analogy[]) {
  // Sub views

  // View
  const frag = div(".cost-matrix");

  // Init
  const cost_matrix: CostMatrix = { frag, analogies };

  // Event Listeners

  // Initial setup
  render_cost_matrix(cost_matrix);

  return cost_matrix;
}

export function render_cost_matrix(cost_matrix: CostMatrix) {
  const analogies = cost_matrix.analogies;
  const spec_names = [...new Set(analogies.flatMap((a) => a.inputs))];

  cost_matrix.frag.innerHTML = "";

  const min_cost = analogies.reduce(
    (prev, a) => Math.min(prev, a.cost),
    Infinity
  );
  const max_cost = analogies.reduce((prev, a) => Math.max(prev, a.cost), 0);

  const rows = spec_names.map((row, idx_row) =>
    div(".cost-matrix-row", [
      ...spec_names.map((col, idx_col) => {
        const labels = [
          ...(idx_col === 0 ? [div(".cost-matrix-row-label", row)] : []),
          ...(idx_row === 0 ? [div(".cost-matrix-col-label", col)] : []),
        ];

        const cost = analogies.find(
          (a) =>
            (a.inputs[0] === row && a.inputs[1] === col) ||
            (a.inputs[1] === row && a.inputs[0] === col)
        )?.cost;

        let color = "none";

        if (cost !== undefined) {
          const h = Math.round((1 - remap(cost, 0, max_cost, 0, 1)) * 360);
          const s = 70;
          const l = 60;
          color = `hsl(${h}deg ${s}% ${l}%)`;
        }

        const title = `${cost ? cost : "-"} (${row}, ${col})`;

        return div(
          {
            class: "cost-matrix-item",
            title: title,
            style: { background: color },
          },
          labels
        );
      }),
    ])
  );

  cost_matrix.frag.append(...rows);
}
