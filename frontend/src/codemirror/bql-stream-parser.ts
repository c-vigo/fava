import type { StreamParser, StringStream } from "@codemirror/language";

// Import the autogenerated (by a script in the 'contrib' directory) lists
import grammar from "./bql-grammar";

const keywords = new Set(grammar.keywords);
const columns = new Set(grammar.columns);
const functions = new Set(grammar.functions);

// This should match the grammar defined in Beancount (`query/query_parser.py`).
const string = /^("[^"]*"|'[^']*')/;
const date = /^(?:#(?:"[^"]*"|'[^']*')|\d\d\d\d-\d\d-\d\d)/;
const decimal = /^[-+]?([0-9]+\.[0-9]*|[0-9]*\.[0-9]+)/;
const integer = /^[-+]?[0-9]+/;

// Check for matches - convert the response of StringStream.match into a boolean explicitly
const m = (s: StringStream, p: RegExp) => {
  const match = s.match(p);
  return match != null && match !== false;
};

export const bqlStreamParser: StreamParser<unknown> = {
  token(stream) {
    if (stream.eatSpace() || stream.eol()) {
      return null;
    }
    if (m(stream, string)) {
      return "string";
    }
    if (m(stream, date) || m(stream, decimal) || m(stream, integer)) {
      return "number";
    }
    if (m(stream, /\w+/)) {
      const word = stream.current().toLowerCase();
      if (keywords.has(word)) {
        return "keyword";
      }
      if (columns.has(word)) {
        return "typeName";
      }
      if (functions.has(word) && stream.peek() === "(") {
        return "macroName";
      }
      return "name";
    }
    // Skip one character since no known token matched.
    const char = stream.next();
    if (char === "*") {
      return "typeName";
    }
    return null;
  },
};
