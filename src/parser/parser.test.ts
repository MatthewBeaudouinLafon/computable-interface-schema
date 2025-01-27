import { expect, test } from "vitest";
import { parse } from "./parser";
import { Node } from "./parser_types";

test("basic declaration", async () => {
  const raw = "text: prompt";
  const ast: Node = {
    _type: "Program",
    statements: [
      {
        _type: "DefinitionStatement",
        decorators: ["text"],
        name: { _type: "Identifier", name: "prompt" },
      },
    ],
  };

  expect(parse(raw)).toEqual(ast);
});

test("declaration with multiple decorators", async () => {
  const raw = "text: many: prompts";

  const ast: Node = {
    _type: "Program",
    statements: [
      {
        _type: "DefinitionStatement",
        decorators: ["text", "many"],
        name: { _type: "Identifier", name: "prompts" },
      },
    ],
  };

  expect(parse(raw)).toEqual(ast);
});

test("multiple declaration", async () => {
  const raw = "text: prompt\ntext: response";
  const ast: Node = {
    _type: "Program",
    statements: [
      {
        _type: "DefinitionStatement",
        decorators: ["text"],
        name: { _type: "Identifier", name: "prompt" },
      },
      {
        _type: "DefinitionStatement",
        decorators: ["text"],
        name: { _type: "Identifier", name: "response" },
      },
    ],
  };

  expect(parse(raw)).toEqual(ast);
});

/*

pattern text extends text:
	many: text: concepts mapto many words
	digraph: mindmap structures concepts
  
  */
test("pattern declaration", async () => {
  const raw =
    `pattern text extends text:` +
    `\n\tmany: text: concepts mapto many words` +
    `\n\tdigraph: mindmap structures concepts` +
    `\nend`;

  const ast: Node = {
    _type: "Program",
    statements: [
      {
        _type: "PatternStatement",
        name: {
          _type: "Identifier",
          name: "text",
        },
        args: undefined,
        statements: [
          {
            _type: "BinaryRelation",
            left: {
              _type: "DefinitionStatement",
              decorators: ["many", "text"],
              name: { _type: "Identifier", name: "concepts" },
            },
            relation: "mapto many",
            right: {
              _type: "Identifier",
              name: "words",
            },
          },
          {
            _type: "BinaryRelation",
            left: {
              _type: "DefinitionStatement",
              decorators: ["digraph"],
              name: { _type: "Identifier", name: "mindmap" },
            },
            relation: "structures",
            right: {
              _type: "Identifier",
              name: "concepts",
            },
          },
        ],
        extends: { _type: "Identifier", name: "text" },
      },
    ],
  };

  expect(parse(raw)).toEqual(ast);
});
