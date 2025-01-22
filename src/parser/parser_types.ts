export type Range = {
  source: string;
  start: number;
  end: number;
};

export function rangeString({ source, start, end }: Range): string {
  return source.slice(start, end);
}

export type Statement =
  | {
      type: "ExpressionStatement";
      expression: Expression;
    }
  | {
      type: "RelationStatement";
      left: Expression | (Statement & { type: "DefinitionStatement" });
      right: Expression;
      relation: "mapto" | "mapto many" | "structures" | "constrains";
    }
  | {
      type: "DefinitionStatement";
      decorators: (
        | "many"
        | "single"
        | "structure"
        | string
        | (Node & { type: "PatternCall" })
      )[];
      var: Node & { type: "Var" };
    }
  | {
      type: "PatternStatement";
      pattern_name: Expression & { type: "Var" };
      args: (Expression & { type: "Var" })[];
      statements: Statement[];
      requires?: Statement[];
      extends?: Expression & { type: "Var" };
    }
  | {
      type: "ViewDefinitionStatement";
      name: Expression & { type: "Var" };
      data: {
        left: Expression;
        right?: Expression;
      };
      structure?: {
        left: Expression;
        right?: Expression;
      };
    };

export type Node =
  | Expression
  | Statement
  | (
      | {
          type: "PatternCall";
          args: (Expression & { type: "Var" })[];
          pattern_name: Expression & { type: "Var" };
        }
      | {
          type: "Program";
          statements: Statement[];
        }
    );

export type Expression =
  | {
      type: "Var";
      name: string;
    }
  | {
      type: "BinaryExpression";
      op: "." | "->";
      left: Expression;
      right: Expression;
    }
  | {
      type: "CoverExpression";
      left: Expression | (Statement & { type: "DefinitionStatement" });
      middle: Expression;
      right: Expression;
    };
