export type Range = {
  source: string;
  start: number;
  end: number;
};

export function rangeString({ source, start, end }: Range): string {
  return source.slice(start, end);
}

export type RelationStatement =
  | {
      _type: "BinaryRelation";
      left: Expression | (Statement & { _type: "DefinitionStatement" });
      right: Expression;
      relation: "mapto" | "mapto many" | "structures" | "constrains";
    }
  | {
      _type: "CoverRelation";
      left: Expression | (Statement & { _type: "DefinitionStatement" });
      middle: Expression;
      right: Expression;
    }
  | {
      _type: "RepresentsRelation";
      view: Expression | (Statement & { _type: "DefinitionStatement" });
      data: WithExpression;
      structure?: WithExpression;
    };

export type WithExpression = {
  _type: "WithExpression";
  left: Expression;
  right?: Expression;
};

export type Statement =
  | RelationStatement
  | {
      _type: "ExpressionStatement";
      expression: Expression;
    }
  | {
      _type: "DefinitionStatement";
      decorators: (
        | (Node & { _type: "Identifier" })
        | (Node & { _type: "ClassCall" })
      )[];
      name: Node & { _type: "Identifier" };
    }
  | {
      _type: "ClassDeclaration";
      name: Expression & { _type: "Identifier" };
      args:
        | (
            | (Expression & { _type: "Identifier" })
            | (Statement & { _type: "DefinitionStatement" })
          )[]
        | undefined;
      statements: Statement[];
      extends?: Expression & { _type: "Identifier" };
    };

export type Node =
  | Expression
  | Statement
  | (
      | {
          _type: "ClassCall";
          args: (Expression & { _type: "Identifier" })[];
          name: Expression & { _type: "Identifier" };
        }
      | {
          _type: "Program";
          statements: Statement[];
        }
    )
  | WithExpression
  | {
      _type: "Error";
      reason: string;
    };

export type Expression =
  | {
      _type: "Identifier";
      name: string;
    }
  | {
      _type: "BinaryExpression";
      op: "." | "<-";
      left: Expression;
      right: Expression;
    };
