import {
  Analogy,
  make_analogy_viewer,
  Spec,
} from "./analogy-viewer/analogy-viewer";
import { SpecPath } from "./analogy-viewer/viewer/viewer";
import "./style.css";
import { vtabs } from "./utilities/ui-utilities";
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
}

async function loop() {
  requestAnimationFrame(loop);
}

main();
loop();
