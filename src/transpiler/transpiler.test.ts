import { expect, test } from "vitest";
import { parse } from "../parser/parser";
import { transpile } from "./transpiler";

test("[transpiler] basic declaration", async () => {
  const input = "many: webpages";
  const output = "objects(many, webpages)";

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] multiple decorators", async () => {
  const input = "single: number: opacity";
  const output = `objects(single, opacity)` + `\ninstance(number, opacity)`;

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] mapto", async () => {
  const input = "subset mapto superset";
  const output = `apply_mapto(subset, superset)`;

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] structures", async () => {
  const input = "a structures b";
  const output = `apply_structures(a, b)`;

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] structures", async () => {
  const input = "a structures b";
  const output = `apply_structures(a, b)`;

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] structure 2", async () => {
  const input = "structure: example";
  const output = `structure(example)`;

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] structure 3", async () => {
  const input = "structure: history structures webpages";
  const output = `structure(history)` + `\napply_structures(history, webpages)`;

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] mapto 2", async () => {
  const input = "structure: history mapto many webpages";
  const output = `structure(history)` + `\napply_mapto_many(history, webpages)`;

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] constrains", async () => {
  const input = "history constrains webpages";
  const output = `apply_constrains(history, webpages)`;

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] cover", async () => {
  const input = "visited_today covers webpages along history";
  const output = `apply_cover(visited_today, webpages, history)`;

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] arrow", async () => {
  const input = "webpages<-visited_today";
  const output = `webpages`;

  expect(transpile(parse(input))).toEqual(output);
});
