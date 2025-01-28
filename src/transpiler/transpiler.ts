import { assert } from "vitest";
import { Node } from "../parser/parser_types";

export function transpile(ast: Node | string): string {
  if (typeof ast === "string") return ast;

  if (ast._type === "Program") {
    return ast.statements.map((s) => transpile(s)).join("\n");
  } else if (ast._type === "DefinitionStatement") {
    assert(ast.decorators.length >= 1);
    const name = transpile(ast.name);

    const d0 = transpile(ast.decorators[0]);
    let head = `objects(${d0}, ${name})`;

    if (d0 === "structure") {
      head = `structure(${name})`;
    }

    const tail = ast.decorators
      .slice(1)
      .map((dec) => `instance(${transpile(dec)}, ${name})`)
      .join("\n");

    // TODO: should single/many have an _?
    return head + (tail.length > 0 ? `\n${tail}` : "");
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
  } else {
    console.log(ast._type);
  }
}
