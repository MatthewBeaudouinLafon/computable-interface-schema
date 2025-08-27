import {
  Analogy,
  make_analogy_viewer,
  Spec,
} from "./analogy-viewer/analogy-viewer";
import { SpecPath } from "./analogy-viewer/viewer/viewer";
import "./style.css";
import { assert } from "./utilities/utilities";

async function main() {
  const specs = (await (await fetch("./specs.json")).json()) as Record<
    string,
    {
      image_names: string[];
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
      image_names: specs[name].image_names,
    };
  };

  for (const analogy_viewer_el of document.querySelectorAll("analogy-viewer")) {
    const from = analogy_viewer_el.getAttribute("from");
    const to = analogy_viewer_el.getAttribute("to");
    assert(from !== null);
    assert(to !== null);

    const analogy_viewer = await make_analogy_viewer(
      get_spec(from),
      get_spec(to),
      analogies
    );

    analogy_viewer_el.append(analogy_viewer.frag);
  }
}

async function loop() {
  requestAnimationFrame(loop);
}

main();
loop();
