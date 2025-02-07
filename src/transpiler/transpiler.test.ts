import { expect, test } from "vitest";
import { parse } from "../parser/parser";
import { transpile } from "./transpiler";

test("[transpiler] Sets/Objects 1", async () => {
  const input = "many: webpages";
  const output = "set(many, webpages)";

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] Sets/Objects 2", async () => {
  const input = "single: selection";
  const output = `set(single, selection)`;

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] Sets/Objects 3", async () => {
  const input = "single: number: opacity";
  const output = `set(single, opacity)
instance(number, opacity)`;

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] Sets/Objects 4", async () => {
  const input = "subset mapto superset";
  const output = `apply_mapto(single, subset, superset)`;

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] Sets/Objects 5", async () => {
  const input = "groups mapto many things";
  const output = `apply_mapto(many, groups, things)`;

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] Sets/Objects 6", async () => {
  const input = "superset<-subset";
  const output = `superset`;

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] Structures 1", async () => {
  const input = "structure: example";
  const output = `structure(example)`;

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] Structures 2", async () => {
  const input = "order: tab_order";
  const output = `structure(tab_order)
instance(order, tab_order)`;

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] Structures 3", async () => {
  const input = "structure: history structures webpages";
  const output = `structure(history)
apply_structure(history, webpages)`;

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] Structures 3", async () => {
  const input = "links constrains history";
  const output = `apply_constraint(links, history)`;

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] Structures 4", async () => {
  const input = "visited_today cover webpages along history";
  const output = `apply_cover(visited_today, webpages, history)`;

  expect(transpile(parse(input))).toEqual(output);
});

test("[transpiler] Classes 1", async () => {
  const input = `class ptn_name(param1, param2):
  shared: single: shared_set
  shared: linear: shared_struct structures shared_set
  many: attribute_set
  tree: attribute_struct structures attribute_set
  attribute_set mapto param1
end

many: ptn_name(input1, input2): instance_name`;

  const output = `set(many, instance_name)
instance(ptn_name, instance_name)
set(single, __ptn_name__shared_set)
structure(__ptn_name__shared_struct)
instance(linear, __ptn_name__shared_struct)
apply_structure(__ptn_name__shared_struct, __ptn_name__shared_set)
set(many, __instance_name__attribute_set)
map_mapto(many, instance_name, __instance_name__attribute_set)
set(many, __instance_name__attribute_struct)
map_structure(__instance_name__attribute_struct)
map_instance(tree, __instance_name__attribute_struct)
map_apply_structure(__instance_name__attribute_struct, __instance_name__attribute_set)
apply_mapto(single, __instance_name__attribute_set, input1)
`;

  expect(transpile(parse(input))).toEqual(output);
});
