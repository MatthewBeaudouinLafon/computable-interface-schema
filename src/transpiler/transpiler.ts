import { Node } from "../parser/parser_types";
import { assert } from "../utilities/utilities";

export type TranspilerContext = {
  classes: (Node & { _type: "ClassDeclaration" })[];
  structures: string[];
};

let context: TranspilerContext;

export function transpile(ast: Node): string {
  switch (ast._type) {
    case "Error":
      return "[Error " + ast.reason + "]";
    case "Program":
      return transpile_program(ast);
    case "BinaryExpression":
      return transpile_binary_expression(ast);
    case "BinaryRelation":
      return transpile_binary_relation(ast);
    case "CoverRelation":
      return transpile_cover_relation(ast);
    case "DefinitionStatement":
      return transpile_definition(ast);
    case "ExpressionStatement":
      return transpile_expression(ast);
    case "Identifier":
      return transpile_identifier(ast);
    case "ClassCall":
      throw new Error("ClassCall directly passed in to transpile");
    case "ClassDeclaration":
      return transpile_class_declaration(ast);
    case "RepresentsRelation":
      return transpile_represents_relation(ast);
    case "WithExpression":
      return transpile_with(ast);
  }
}

function transpile_program(ast: Node & { _type: "Program" }) {
  context = { classes: [], structures: ["order", "linear", "tree"] };
  return ast.statements
    .map((s) => transpile(s))
    .filter((s) => s !== "")
    .join("\n");
}

function transpile_class_declaration(
  ast: Node & {
    _type: "ClassDeclaration";
  }
) {
  context.classes.push(ast);
  return "";
}

function transpile_class_instance(
  ast: Node & { _type: "ClassDeclaration" },
  instance_name: string
) {
  const class_name = transpile(ast.name);

  const instance = `instance(${class_name}, ${instance_name})`;

  const renames: Record<string, string> = {};

  const statements = ast.statements
    .flatMap((_s) => {
      // Don't want to actually rename the declarations,
      // in case the class is re-used.
      let s = structuredClone(_s);

      let declarations = find_recursive_all(
        s,
        (n) => n._type === "DefinitionStatement"
      ) as (Node & { _type: "DefinitionStatement" })[];

      declarations.forEach((d) => {
        const is_shared = d.decorators.some(
          (d) => d._type !== "ClassCall" && transpile(d) === "shared"
        );

        renames[d.name.name] = is_shared
          ? `__${class_name}__${d.name.name}`
          : `__${instance_name}__${d.name.name}`;

        // Rename all identifiers
        let identifiers = find_recursive_all(
          s,
          (id) => id._type === "Identifier" && id.name in renames
        ) as (Node & { _type: "Identifier" })[];

        identifiers.forEach((id) => (id.name = renames[id.name]));
      });

      let post = "";
      let pre = "";

      declarations.forEach((d) => {
        const is_shared = d.decorators.some(
          (d) => d._type !== "ClassCall" && transpile(d) === "shared"
        );

        const is_many = d.decorators.some(
          (d) => d._type !== "ClassCall" && transpile(d) === "many"
        );

        const is_structure = d.decorators.some(
          (d) => d._type !== "ClassCall" && context.structures.includes(d.name)
        );

        let statement = "";

        if (is_many) {
          statement = `mapto(many, ${instance_name}, ${transpile(d.name)})`;
        }

        if (!is_shared) {
          statement = `map_${statement}`;
        }

        if (statement !== "") {
          post += "\n" + statement;
        }

        if (is_structure && !is_shared) {
          pre += `set(many, ${transpile(d.name)})\n`;
        }
      });

      return pre + transpile(s) + post;
    })
    .join("\n");

  return `${instance}\n${statements}`;
}

function transpile_definition(ast: Node & { _type: "DefinitionStatement" }) {
  assert(ast.decorators.length >= 1);

  const var_name = transpile(ast.name);

  const decorators = ast.decorators
    .filter((d) => d._type === "ClassCall" || transpile(d) !== "shared")
    .flatMap((d) => {
      if (d._type === "ClassCall") {
        // Does the decorator correspond to a class?
        const d_class = context.classes.find(
          (p) => transpile(p.name) === transpile(d.name)
        );

        if (d_class !== undefined) {
          return transpile_class_instance(d_class, var_name);
        }

        throw new Error("Could not resolve decorator");
      }

      if (d.name === "single") {
        return `set(single, ${var_name})`;
      } else if (d.name === "many") {
        return `set(many, ${var_name})`;
      } else if (d.name === "structure") {
        return `structure(${var_name})`;
      } else if (context.structures.includes(d.name)) {
        return [`structure(${var_name})`, `instance(${d.name}, ${var_name})`];
      } else {
        return `instance(${d.name}, ${var_name})`;
      }
    })
    .join("\n");

  return decorators;
}

function transpile_expression(ast: Node & { _type: "ExpressionStatement" }) {
  return transpile(ast.expression);
}

function transpile_identifier(ast: Node & { _type: "Identifier" }) {
  return ast.name;
}

function transpile_binary_relation(ast: Node & { _type: "BinaryRelation" }) {
  let pre =
    ast.left._type === "DefinitionStatement" ? transpile(ast.left) + "\n" : "";

  let left =
    ast.left._type === "DefinitionStatement" ? ast.left.name : ast.left;

  // Prefix
  let prefix =
    ast.relation === "constrains"
      ? "apply_constraint("
      : ast.relation === "mapto"
      ? "apply_mapto(single, "
      : ast.relation === "mapto many"
      ? "apply_mapto(many, "
      : ast.relation === "structures"
      ? "apply_structure("
      : "[No prefix]";

  return `${pre}${prefix}${transpile(left)}, ${transpile(ast.right)})`;
}

function transpile_binary_expression(
  ast: Node & { _type: "BinaryExpression" }
) {
  if (ast.op === "<-") {
    return `${transpile(ast.left)}`;
  } else {
    return "[Binary Expression . not implemented yet]";
  }
}

function transpile_cover_relation(ast: Node & { _type: "CoverRelation" }) {
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
}

function transpile_represents_relation(
  ast: Node & { _type: "RepresentsRelation" }
) {
  return "[Represents not yet implemented]";
}

function transpile_with(ast: Node & { _type: "WithExpression" }) {
  return "[With not implemented]";
}

export function find_recursive_all(
  ast: Node,
  f: (node: Node) => boolean
): Node[] {
  let satisfying: Node[] = [];

  if (f(ast)) satisfying.push(ast);

  switch (ast._type) {
    case "Program":
      ast.statements.forEach((s) => {
        satisfying.push(...find_recursive_all(s, f));
      });
      break;
    case "BinaryExpression":
      [ast.left, ast.right].forEach((s) => {
        satisfying.push(...find_recursive_all(s, f));
      });
      break;
    case "BinaryRelation":
      [ast.left, ast.right].forEach((s) => {
        satisfying.push(...find_recursive_all(s, f));
      });
      break;
    case "CoverRelation":
      [ast.left, ast.middle, ast.right].forEach((s) => {
        satisfying.push(...find_recursive_all(s, f));
      });
      break;
    case "DefinitionStatement":
      [...ast.decorators, ast.name].forEach((s) => {
        satisfying.push(...find_recursive_all(s, f));
      });
      break;
    case "ExpressionStatement":
      satisfying.push(...find_recursive_all(ast.expression, f));
      break;
    case "ClassCall":
      satisfying.push(...find_recursive_all(ast.name, f));
      break;
    case "ClassDeclaration":
      [...(ast.args ?? []), ast.name, ...ast.statements].forEach((s) => {
        satisfying.push(...find_recursive_all(s, f));
      });
      break;
    case "RepresentsRelation":
      [ast.data, ast.structure, ast.view]
        .filter((v) => v !== undefined)
        .forEach((s) => {
          satisfying.push(...find_recursive_all(s, f));
        });
      break;
    case "WithExpression":
      [ast.left, ast.right]
        .filter((v) => v !== undefined)
        .forEach((s) => {
          satisfying.push(...find_recursive_all(s, f));
        });
      break;
    case "Identifier":
      break;
  }

  return satisfying;
}
