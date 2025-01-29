import { Node } from "../parser/parser_types";
import { assert } from "../utilities/utilities";

export type TranspilerContext = {
  patterns: (Node & { _type: "PatternStatement" })[];
};

let context: TranspilerContext = { patterns: [] };

export function transpile(ast: Node | string): string {
  if (typeof ast === "string") return ast;

  if (ast._type === "Program") {
    context = { patterns: [] };
    return ast.statements
      .map((s) => transpile(s))
      .filter((s) => s !== "")
      .join("\n");
  } else if (ast._type === "PatternStatement") {
    context.patterns.push(ast);
    return "";
  } else if (ast._type === "DefinitionStatement") {
    assert(ast.decorators.length >= 1);

    const def_name = transpile(ast.name);

    let resolve_decorator = (
      decorator: string | (Node & { _type: "PatternCall" }),
      index: number
    ) => {
      const decorator_name =
        typeof decorator === "string" ? decorator : decorator.name.name;

      // Maybe it couldn't find the pattern because user forgot to define
      // ...should probably not be okay with a pattern that has args, but
      // ...doesn't actually exist.
      const decorator_pattern = context.patterns.find(
        (p) => p.name.name === decorator_name
      );

      let decorator_str = "";

      console.log(decorator_name, decorator_pattern, index);

      if (index === 0) {
        decorator_str +=
          decorator_name === "structure"
            ? `structure(${def_name})\n`
            : `set(${decorator_name}, ${def_name})\n`;

        if (decorator_pattern !== undefined) {
          decorator_str += transpile_pattern(decorator_pattern, def_name);
        }
      } else {
        if (decorator_pattern === undefined) {
          decorator_str +=
            decorator_name === "structure"
              ? `structure(${def_name})\n`
              : `instance(${decorator_name}, ${def_name})\n`;
        } else if (decorator_pattern !== undefined) {
          decorator_str += transpile_pattern(decorator_pattern, def_name);
        }
      }

      return decorator_str;
    };

    let decorators = "";

    ast.decorators = ast.decorators.filter(
      (d) => !(typeof d === "string" && d === "shared")
    );

    for (const [i, decorator] of ast.decorators.entries()) {
      decorators += resolve_decorator(decorator, i);
    }

    if (decorators.at(-1) === "\n") {
      decorators = decorators.slice(0, -1);
    }

    return decorators;
  } else if (ast._type === "Identifier") {
    return ast.name;
  } else if (ast._type === "BinaryRelation") {
    const relation =
      ast.relation === "mapto many" ? "mapto_many" : ast.relation;

    if (ast.left._type === "DefinitionStatement") {
      return (
        `${transpile(ast.left)}\n` +
        `apply_${relation}(${transpile(ast.left.name)}, ${transpile(
          ast.right
        )})`
      );
    }

    return `apply_${relation}(${transpile(ast.left)}, ${transpile(ast.right)})`;
  } else if (ast._type === "CoverRelation") {
    if (ast.left._type === "DefinitionStatement") {
      return (
        `${transpile(ast.left)}\n` +
        `apply_cover(${transpile(ast.left.name)}, ${transpile(
          ast.middle
        )}, ${transpile(ast.right)})`
      );
    }

    return `apply_cover(${transpile(ast.left)}, ${transpile(
      ast.middle
    )}, ${transpile(ast.right)})`;
  } else if (ast._type === "BinaryExpression") {
    if (ast.op === "<-") {
      return `${transpile(ast.left)}`;
    }
  } else {
    console.log(ast._type);
  }
}

function transpile_pattern(
  pattern: Node & { _type: "PatternStatement" },
  instance_name: string
) {
  let ptn_str = "";
  const pattern_name = transpile(pattern.name);

  ptn_str += `apply_instance(${pattern_name}, ${instance_name})\n`;

  pattern.statements.forEach((s) => {
    if (s._type === "DefinitionStatement") {
      if (s.decorators.some((d) => d === "shared")) {
        s.name.name = `__${pattern_name}__${s.name.name}`;
      } else {
        s.name.name = `__${instance_name}__${s.name.name}`;
      }
    }

    ptn_str += transpile(s) + "\n";

    if (s._type === "DefinitionStatement") {
      ptn_str += `apply_mapto(${instance_name}, ${s.name.name})\n`;
    }
  });

  return ptn_str;
}
