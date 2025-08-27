import mermaid from "mermaid";
import {
  Analogy,
  make_analogy_viewer,
  Spec,
} from "./analogy-viewer/analogy-viewer";
import "./style.css";
import { el } from "./utilities/utilities";
import { SpecPath } from "./viewer/viewer";

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

  // Mermaid styling
  mermaid.initialize({
    theme: "neutral",
    flowchart: {
      padding: 0,
      nodeSpacing: 0,
    },
  });

  const get_spec = (name: string): Spec => {
    return {
      name,
      yaml: specs[name].yaml,
      lookup: specs[name].lookup,
    };
  };

  const analogy_viewer_messages = await make_analogy_viewer(
    get_spec("imessage"),
    get_spec("slack"),
    analogies
  );

  const analogy_viewer_cv = await make_analogy_viewer(
    get_spec("calendar"),
    get_spec("video-editor"),
    analogies
  );

  const app = document.getElementById("app")!;

  app.append(el("h2", { innerText: "IMessage v. Slack" }));
  app.append(el("p", { innerText: "Huh." }));
  app.append(analogy_viewer_messages.frag);

  app.append(el("hr"));

  app.append(el("h2", { innerText: "Calendar v. Video Editor" }));
  app.append(el("p", { innerText: "Huh." }));
  app.append(analogy_viewer_cv.frag);
}

async function loop() {
  requestAnimationFrame(loop);
}

main();
loop();
