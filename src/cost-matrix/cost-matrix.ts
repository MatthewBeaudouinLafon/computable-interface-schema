import { Analogy } from "../analogy-viewer/analogy-viewer";
import {
  div,
  get_humane_name,
  get_humane_pair_name,
  remap,
} from "../utilities/utilities";
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
    (prev, a) => Math.min(prev, a.conceptual_connectivity),
    Infinity
  );
  const max_cost = analogies.reduce(
    (prev, a) => Math.max(prev, a.conceptual_connectivity),
    0
  );

  const rows = spec_names.map((row, idx_row) =>
    div({ class: "cost-matrix-row", style: {} }, [
      ...spec_names.map((col, idx_col) => {
        const labels = [
          ...(idx_col === 0
            ? [div(".cost-matrix-row-label", get_humane_name(row))]
            : []),
          ...(idx_row === 0
            ? [div(".cost-matrix-col-label", get_humane_name(col))]
            : []),
        ];

        const analogy = analogies.find(
          (a) =>
            (a.inputs[0] === row && a.inputs[1] === col) ||
            (a.inputs[1] === row && a.inputs[0] === col)
        );

        const cost = analogy?.conceptual_connectivity;

        let color = "none";
        const classes = ["cost-matrix-item"];

        if (analogy !== undefined) {
          let iters_raw = analogy.stdout.find((l) =>
            l.startsWith("num-iterations")
          );
          let iters = iters_raw
            ? Number(iters_raw.split(":").at(1)?.trim())
            : undefined;

          if (iters !== undefined && iters <= 3) {
            classes.push("insignificant");
          }
        }

        if (cost !== undefined) {
          const n = remap(cost, 0, max_cost, 0, 1);
          // const h = 210; // Math.round((1 - remap(cost, 0, max_cost, 0, 1)) * 360);
          // const s = 70;
          // const l = n * 90;
          // const opacity = idx_col > idx_row ? 0.5 : 1;
          // color = `hsl(${h}deg ${s}% ${l}% / ${opacity})`;
          color = `oklab(${0.5} ${0.1} ${-0.2} / ${n * 0.9})`;
        }

        const title = `${cost !== undefined ? cost : "-"} (${row}, ${col})`;

        return div(
          {
            class: classes,
            title: title,
            style: {
              background: color,
            },
            data: [
              ["name", get_humane_pair_name(row, col)],
              ["alt_name", get_humane_pair_name(col, row)],
            ],
          },
          labels
        );
      }),
    ])
  );

  cost_matrix.frag.append(...rows);
}
