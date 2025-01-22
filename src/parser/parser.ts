import { Node } from "./parser_types";

export function parse(code: string): Node & { type: "Program" } {
  const lines = code.split("\n");

  for (const line of lines) {
    // Identify the statement
  }
}
