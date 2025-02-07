import { Node } from "../parser/parser_types";
import { assert } from "../utilities/utilities";

export type TranspilerContext = {
  classes: (Node & { _type: "ClassDeclaration" })[];
  scope: {
    class: Node & { _type: "ClassDeclaration" };
    instance: Node & { _type: "Identifier" };
    renames: Record<string, string>;
  }[];
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
      return transpile_class_call(ast);
    case "ClassDeclaration":
      return transpile_class_declaration(ast);
    case "RepresentsRelation":
      return transpile_represents_relation(ast);
    case "WithExpression":
      return transpile_with(ast);
  }
}

function transpile_program(ast: Node & { _type: "Program" }) {
  context = { classes: [], structures: ["order", "linear", "tree"], scope: [] };
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

function transpile_class_call(ast: Node & { _type: "ClassCall" }) {
  const scope = context.scope.at(-1)!;
  const instance_name = transpile(scope.instance);

  const class_name = transpile(scope.class.name);
  const instance = `instance(${class_name}, ${instance_name})`;

  scope.renames = {};

  let post = "";
  let pre = "";

  const statements = scope.class.statements
    .map((s) => {
      let declarations = find_recursive_all(
        s,
        (n) => n._type === "DefinitionStatement"
      ) as (Node & { _type: "DefinitionStatement" })[];

      declarations.forEach((d) => {
        const is_shared = d.decorators.some(
          (d) => d._type !== "ClassCall" && transpile(d) === "shared"
        );

        scope.renames[d.name.name] = is_shared
          ? `__${class_name}__${d.name.name}`
          : `__${instance_name}__${d.name.name}`;
      });

      return pre + transpile(s) + post;
    })
    .join("\n");

  return `${instance}\n${statements}`;
}

function transpile_definition(ast: Node & { _type: "DefinitionStatement" }) {
  assert(ast.decorators.length >= 1);

  const var_name = transpile(ast.name);

  const scope = context.scope.at(-1);

  const many = ast.decorators.find(
    (d) => d._type !== "ClassCall" && d.name === "many"
  );

  const single = ast.decorators.find(
    (d) => d._type !== "ClassCall" && d.name === "single"
  );

  const shared = ast.decorators.find(
    (d) => d._type !== "ClassCall" && d.name === "shared"
  );

  const decorators = ast.decorators
    .filter((d) => d._type === "ClassCall" || transpile(d) !== "shared")
    .flatMap((d) => {
      if (d._type === "ClassCall") {
        // Does the decorator correspond to a class?
        const d_class = context.classes.find(
          (p) => transpile(p.name) === transpile(d.name)
        );

        if (d_class !== undefined) {
          const _d_class = structuredClone(d_class);

          context.scope.push({
            class: _d_class,
            instance: ast.name,
            renames: {},
          });
          const instance = transpile(d);
          context.scope.pop();

          return instance;
        }

        throw new Error("Could not resolve decorator");
      }

      let s: string[] = [];

      if (d.name === "single") {
        s.push(`set(single, ${var_name})`);
      } else if (d.name === "many") {
        s.push(`set(many, ${var_name})`);
      } else if (d.name === "structure") {
        s.push(`structure(${var_name})`);
      } else if (context.structures.includes(d.name)) {
        s.push(
          scope && !shared
            ? `map_structure(${var_name})`
            : `structure(${var_name})`
        );
        s.push(
          scope && !shared
            ? `map_instance(${d.name}, ${var_name})`
            : `instance(${d.name}, ${var_name})`
        );
      } else {
        s.push(`instance(${d.name}, ${var_name})`);
      }

      return s.join("\n");
    });

  let post: string[] = [];
  let pre: string[] = [];

  if (scope !== undefined) {
    const structure_instance = ast.decorators.find(
      (d) => d._type !== "ClassCall" && context.structures.includes(d.name)
    );

    if (many !== undefined) {
      post.push(`map_mapto(many, ${transpile(scope.instance)}, ${var_name})`);
    }

    if (shared === undefined && structure_instance !== undefined) {
      pre.push(`set(many, ${var_name})`);
    }
  }

  return [...pre, ...decorators, ...post].join("\n");
}

function transpile_expression(ast: Node & { _type: "ExpressionStatement" }) {
  return transpile(ast.expression);
}

function transpile_identifier(ast: Node & { _type: "Identifier" }) {
  const renames = context.scope.at(-1)?.renames ?? {};
  return ast.name in renames ? renames[ast.name] : ast.name;
}

function transpile_binary_relation(ast: Node & { _type: "BinaryRelation" }) {
  const scope = context.scope.at(-1);

  const shared =
    ast.left._type === "DefinitionStatement"
      ? ast.left.decorators.find(
          (d) => d._type !== "ClassCall" && d.name === "shared"
        )
      : undefined;

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

  if (scope && !shared && ast.left._type === "DefinitionStatement") {
    prefix = `map_${prefix}`;
  }

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
