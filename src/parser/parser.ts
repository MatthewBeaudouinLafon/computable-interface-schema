import * as ohm from "ohm-js";
import { Node } from "./parser_types";

const grammar = ohm.grammar(String.raw`
IS {
  
  program = (statement eol+)*
    
  statement  (statement)
  = relation -- relation
    | class -- class
    | def -- definition
    | expr -- expression
    
  class = "class " ident class_args? (" extends " ident)?":"eol
     ("\t"statement eol)+"end"
     
  class_args = "(" ((def | expr) ", ")* (def | expr) ")"
     
  relation = ((def | expr) " represents " with_expr) (" as " with_expr)? -- represents
  | (def | expr) " cover " expr " along " expr -- cover
            | (def | expr) " " ("mapto many"  | "mapto" | "structures" | "constrains" | "groups") " " expr -- binary

  with_expr = expr (" with " expr)?

  def  (definition statement)
    = (expr class_args? ": ")+ ident
   
  expr
    = expr ("." | "<-") expr -- binary
    | ident -- name
   
  ident  (an identifier)
    = (alnum | "_")+

  number  (a number)
    = digit* "." digit+  -- fract
    | digit+             -- whole
      
  eol = "\r"? "\n"
}
`);

const semantics = grammar.createSemantics();

semantics.addOperation("parse", {
  program(statements, _eol) {
    return {
      _type: "Program",
      statements: statements.children.map((s) => s.parse()),
    };
  },
  statement(s) {
    return s.children[0].parse();
  },
  def(decorators, args, _, name) {
    const p_args = args.children.map((a) => {
      return a.children.at(0)?.parse() ?? undefined;
    });

    const p_decorators: any[] = decorators.children.map((d) => d.parse());

    for (let i = 0; i < p_args.length; i++) {
      if (p_args[i] !== undefined) {
        p_decorators[i] = {
          _type: "ClassCall",
          name: p_decorators[i],
          args: p_args[i],
        };
      }
    }

    return {
      _type: "DefinitionStatement",
      decorators: p_decorators,
      name: name.parse(),
    };
  },
  ident(v) {
    return {
      _type: "Identifier",
      name: v.sourceString,
    };
  },
  relation_binary(left, _space, relation, _space2, right) {
    return {
      _type: "BinaryRelation",
      left: left.parse(),
      right: right.parse(),
      relation: relation.sourceString,
    };
  },
  relation_cover(left, _covers, middle, _along, right) {
    return {
      _type: "CoverRelation",
      left: left.parse(),
      middle: middle.parse(),
      right: right.parse(),
    };
  },
  relation_represents(view, _represents, data_expr, _as, structure_expr) {
    return {
      _type: "RepresentsRelation",
      view: view.parse(),
      data: data_expr.parse(),
      structure: structure_expr.children.at(0)?.parse() ?? undefined,
    };
  },
  with_expr(left, _with, right_parent) {
    return {
      _type: "WithExpression",
      left: left.parse(),
      right: right_parent?.children.at(0)?.parse() ?? undefined,
    };
  },
  expr_binary(left, op, right) {
    return {
      _type: "BinaryExpression",
      op: op.sourceString,
      left: left.parse(),
      right: right.parse(),
    };
  },
  class(
    _class,
    name,
    class_args,
    _extends,
    extend_expr,
    _colon,
    _eol,
    _indents,
    statements,
    _newlines,
    _eol2
  ) {
    return {
      _type: "ClassDeclaration",
      name: name.parse(),
      args: class_args.children.at(0)?.parse() ?? undefined,
      statements: statements.children.map((s) => s.parse()),
      extends: extend_expr?.children.at(0)?.parse() ?? undefined,
    };
  },
  class_args(_lbracket, tail, _commas, head, _rbracket) {
    return [...tail.children.map((arg) => arg.parse()), head.parse()];
  },
});

export function parse(code: string): Node {
  // Pre-process
  code =
    code
      .split("\n")
      .filter((line) => !line.trim().startsWith("%") && line.trim() !== "")
      .map((line) => (line.startsWith("  ") ? `\t${line.slice(2)}` : line))
      .map((line) => (line.startsWith("    ") ? `\t${line.slice(4)}` : line))
      .join("\n") + "\n";

  console.log("Preprocessed code\n");
  console.log(code);

  const m = grammar.match(code);

  if (!m.succeeded()) {
    return {
      _type: "Error",
      reason: `[Failed!]

Did you make sure to use backward arrows?
End a class with an 'end'?
Remove inline comments?

Here's what the parser has to say about it:
${m.message}`,
    };
  }

  const parsed = semantics(grammar.match(code)).parse();
  console.log("Parsed AST", parsed);
  return parsed;
}
