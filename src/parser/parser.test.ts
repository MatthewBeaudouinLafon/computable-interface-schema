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
        name: { type: "Identifier", name: "prompt" },
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
        name: { type: "Identifier", name: "prompts" },
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
        name: { type: "Identifier", name: "prompt" },
      },
      {
        type: "DefinitionStatement",
        decorators: ["text"],
        name: { type: "Identifier", name: "response" },
      },
    ],
  } as Node & { type: "Program" });
});

/*

pattern text extends text:
	many: text: concepts mapto many words
	digraph: mindmap structures concepts
  
  */
test("pattern declaration", async () => {
  expect(
    parse(
      `pattern text extends text:` +
        `\n\tmany: text: concepts mapto many words` +
        `\n\tdigraph: mindmap structures concepts`
    )
  ).toEqual({
    type: "Program",
    statements: [
      {
        type: "PatternStatement",
        pattern_name: {
          type: "Identifier",
          name: "text",
        },
        args: [],
        statements: [
          {
            _type: "RelationStatement",
            left: {
              type: "DefinitionStatement",
              decorators: ["many", "text"],
              name: { type: "Identifier", name: "concepts" },
            },
            relation: "mapto many",
            right: {
              type: "Identifier",
              name: "words",
            },
          },
          {
            _type: "RelationStatement",
            left: {
              type: "DefinitionStatement",
              decorators: ["digraph"],
              name: { type: "Identifier", name: "mindmap" },
            },
            relation: "structures",
            right: {
              type: "Identifier",
              name: "words",
            },
          },
        ],
        extends: { type: "Identifier", name: "text" },
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
