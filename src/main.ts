import {
  Analogy,
  make_analogy_viewer,
  Spec,
} from "./analogy-viewer/analogy-viewer";
import { SpecPath } from "./analogy-viewer/viewer/viewer";
import { make_cost_matrix } from "./cost-matrix/cost-matrix";
import "./style.css";
import { checkbox, hstack, vtabs } from "./utilities/ui-utilities";
import { get_humane_name } from "./utilities/utilities";

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

  const app = document.getElementById("app")!;

  app.append(
    vtabs(
      ".app-tabs",
      analogy_viewers.map((v) => [
        `${get_humane_name(v.a.name)} / ${get_humane_name(v.b.name)}`,
        v.frag,
      ])
    )
  );

  document.querySelector(".tabs-toggles")!.prepend(cost_matrix.frag);

  const options = hstack(
    ".analogy-viewer-options",
    [
      checkbox({}, "Show syntax highlighting", () => {
        app.classList.toggle("show-syntax-highlighting");
      }),
      checkbox({}, "Show primitives inline", () => {
        app.classList.toggle("show-primitives-inline");
      }),
      checkbox({}, "Show cost matrix", (input) => {
        const cost_matrix = document.querySelector(".cost-matrix");
        if (cost_matrix === null) return;

        if (input) {
          cost_matrix.classList.add("visible");
        } else {
          cost_matrix.classList.remove("visible");
        }
      }),
    ],
    10
  );

  document.querySelector("header")!.append(options);
}

async function loop() {
  requestAnimationFrame(loop);
}

main();
loop();
