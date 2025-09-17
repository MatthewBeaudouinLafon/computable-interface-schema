import {
  Analogy,
  make_analogy_viewer,
  Spec,
} from "./analogy-viewer/analogy-viewer";
import { SpecPath } from "./analogy-viewer/viewer/viewer";
import { make_cost_matrix } from "./cost-matrix/cost-matrix";
import "./style.css";
import { vtabs } from "./utilities/ui-utilities";
import { get_humane_pair_name } from "./utilities/utilities";

async function main() {
  const specs = (await (await fetch("./specs.json")).json()) as Record<
    string,
    {
      yaml: object;
      lookup: [string, SpecPath][];
    }
  >;

  const analogies = (await (
    await fetch("./analogies.json")
  ).json()) as Analogy[];

  const get_spec = (name: string): Spec => {
    return {
      name,
      yaml: specs[name].yaml,
      lookup: specs[name].lookup,
    };
  };

  const analogy_viewers = await Promise.all(
    analogies.map((a) =>
      make_analogy_viewer(
        get_spec(a.inputs[0]),
        get_spec(a.inputs[1]),
        analogies.find(
          (an) =>
            an.inputs.includes(a.inputs[0]) && an.inputs.includes(a.inputs[1])
        )!
      )
    )
  );

  const cost_matrix = make_cost_matrix(analogies);

  const tabs = vtabs(
    ".app-tabs",
    analogy_viewers.map((v) => [
      get_humane_pair_name(v.a.name, v.b.name),
      v.frag,
    ])
  );

  const tab_items = [
    ...tabs.querySelectorAll(".tabs-toggles > *:not(.cost-matrix)"),
  ] as HTMLElement[];

  const cells = [
    ...cost_matrix.frag.querySelectorAll(".cost-matrix-item"),
  ] as HTMLElement[];

  cells.forEach((cell) => {
    const index = tab_items.findIndex(
      (item) =>
        item.innerText === cell.dataset.name ||
        item.innerText === cell.dataset.alt_name
    );
    if (index === -1) return;

    cell.addEventListener("click", () => {
      tabs.dispatchEvent(new CustomEvent("switch-tab", { detail: index }));

      cells.forEach((c) => c.classList.remove("active"));
      cells
        .filter(
          (c) =>
            c.dataset.name === cell.dataset.name ||
            c.dataset.alt_name === cell.dataset.name
        )
        .forEach((c) => c.classList.add("active"));
    });
  });

  cells
    .filter(
      (c) =>
        c.dataset.name === tab_items[0].innerText ||
        c.dataset.alt_name === tab_items[0].innerText
    )
    .forEach((c) => c.classList.add("active"));

  const app = document.getElementById("app")!;

  app.append(tabs);

  document.querySelector(".tabs-toggles")!.prepend(cost_matrix.frag);
}

async function loop() {
  requestAnimationFrame(loop);
}

main();
loop();
