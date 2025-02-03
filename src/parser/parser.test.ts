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
        decorators: [
          {
            _type: "Identifier",
            name: "text",
          },
        ],
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
        decorators: [
          {
            _type: "Identifier",
            name: "text",
          },
          {
            _type: "Identifier",
            name: "many",
          },
        ],
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
        decorators: [
          {
            _type: "Identifier",
            name: "text",
          },
        ],
        name: { _type: "Identifier", name: "prompt" },
      },
      {
        _type: "DefinitionStatement",
        decorators: [
          {
            _type: "Identifier",
            name: "text",
          },
        ],
        name: { _type: "Identifier", name: "response" },
      },
    ],
  };

  expect(parse(raw)).toEqual(ast);
});

test("Class declaration", async () => {
  const raw = `class text extends text:
  many: text: concepts mapto many words
  digraph: mindmap structures concepts
end`;

  const ast: Node = {
    _type: "Program",
    statements: [
      {
        _type: "ClassDeclaration",
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
              decorators: [
                {
                  _type: "Identifier",
                  name: "many",
                },
                {
                  _type: "Identifier",
                  name: "text",
                },
              ],
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
              decorators: [
                {
                  _type: "Identifier",
                  name: "digraph",
                },
              ],
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

test("Class 1", async () => {
  const raw = `class ptn_name(param):
  shared: single: shared_set
end
  
many: ptn_name(five): instance_name
`;
  const ast: Node = {
    _type: "Program",
    statements: [
      {
        _type: "ClassDeclaration",
        name: {
          _type: "Identifier",
          name: "ptn_name",
        },
        args: [
          {
            _type: "Identifier",
            name: "param",
          },
        ],
        statements: [
          {
            _type: "DefinitionStatement",
            decorators: [
              {
                _type: "Identifier",
                name: "shared",
              },
              {
                _type: "Identifier",
                name: "single",
              },
            ],
            name: {
              _type: "Identifier",
              name: "shared_set",
            },
          },
        ],
      },
      {
        _type: "DefinitionStatement",
        decorators: [
          {
            _type: "Identifier",
            name: "many",
          },
          {
            _type: "ClassCall",
            name: { _type: "Identifier", name: "ptn_name" },
            args: [{ _type: "Identifier", name: "five" }],
          },
        ],
        name: {
          _type: "Identifier",
          name: "instance_name",
        },
      },
    ],
  };

  expect(parse(raw)).toEqual(ast);
});
