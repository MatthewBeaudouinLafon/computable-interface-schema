import { expect, test } from "vitest";
import { parse } from "./parser";
import { Node } from "./parser_types";

test("basic declaration", async () => {
  expect(parse("text: prompt")).toEqual({
    type: "Program",
    statements: [
      {
        type: "DefinitionStatement",
        decorators: ["text"],
        var: { type: "Var", name: "prompt" },
      },
    ],
  } as Node & { type: "Program" });
});

test("declaration with multiple decorators", async () => {
  expect(parse("text: many: prompts")).toEqual({
    type: "Program",
    statements: [
      {
        type: "DefinitionStatement",
        decorators: ["text", "many"],
        var: { type: "Var", name: "prompts" },
      },
    ],
  } as Node & { type: "Program" });
});

test("multiple declaration", async () => {
  expect(parse("text: prompt\ntext: response")).toEqual({
    type: "Program",
    statements: [
      {
        type: "DefinitionStatement",
        decorators: ["text"],
        var: { type: "Var", name: "prompt" },
      },
      {
        type: "DefinitionStatement",
        decorators: ["text"],
        var: { type: "Var", name: "response" },
      },
    ],
  } as Node & { type: "Program" });
});

test("pattern declaration", async () => {
  expect(
    parse(
      `pattern text extends text:` +
        `\n\tmany: text: concepts mapto many words` +
        `\n\tdigraph: mindmap structures concepts`,
    ),
  ).toEqual({
    type: "Program",
    statements: [
      {
        type: "PatternStatement",
        pattern_name: {
          type: "Var",
          name: "text",
        },
        args: [],
        statements: [
          {
            type: "RelationStatement",
            left: {
              type: "DefinitionStatement",
              decorators: ["many", "text"],
              var: { type: "Var", name: "concepts" },
            },
            relation: "mapto many",
            right: {
              type: "Var",
              name: "words",
            },
          },
          {
            type: "RelationStatement",
            left: {
              type: "DefinitionStatement",
              decorators: ["digraph"],
              var: { type: "Var", name: "mindmap" },
            },
            relation: "structures",
            right: {
              type: "Var",
              name: "words",
            },
          },
        ],
        extends: { type: "Var", name: "text" },
      },
    ],
  } as Node & { type: "Program" });
});

// text: prompt
// text: response

// ; Chat model
// view: prompt_view represents prompt as prompt.textbox_view
// view: chat_view represents response as response.textbox_view
// ; textbox view is built into the text pattern

// ; Graphologue
// pattern text extends text:
// 	many: text: concepts mapto many words
// 	digraph: mindmap structures concepts

// 	view: mindmap_view represents concepts as concepts.textbox_view
// 		with mindmap as gui.node_arrow_digraph

// view: prompt_view represents prompt as prompt.textbox_view
// view: chat_view represents response as response.textbox_view
// view: mindmap represents response as response.mindmap_view
