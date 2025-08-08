"""
This file aims to ingest a yaml 6.4 specification and spit out a list of relations.

A YAML file looks like this:
- object-expression  # includes a.b->c/d
- source-expression:
    left-hand-side: target-expression
# TODO: fill this out for documentation.
"""

import yaml
from pprint import pformat
from pathlib import Path
import re
import enum
from enum import Enum


def parse_yaml(raw):
    return yaml.safe_load(raw)


# --- interpreted relations
class rel(Enum):
    # objects
    MAPTO = enum.auto()
    SUBSET = enum.auto()
    ALIAS = enum.auto()

    # structures
    GROUP = enum.auto()
    GROUP_FOREACH = enum.auto()
    AFFECTS = enum.auto()
    COVERS = enum.auto()

    # type
    TYPE = enum.auto()

    # This is a catchall for relations I haven't figured out what to do yet
    TBD = enum.auto()


def make_edge(
    interp: list, source: str, relation: rel, target: str, verbose=False
):
    """
    Declares an edge in the graph by appending it to interp.
    """
    interp.append({"source": source, "relation": relation, "target": target})
    pretty_source = source
    pretty_relation = relation.name
    pretty_target = target
    if verbose:
        print(f"{pretty_source}  -{pretty_relation}->  {pretty_target}")


# --- Parse spec
def incrementally_aggregate(array: list, symbol: str):
    # Map an array to such that each term uses a combined sequence of the previous.
    # For example, here using the `/` symbol.
    # [a, b, c] => [a, a/b, a/b/c]
    aggregate = []
    for idx, term in enumerate(array):
        if idx == 0:
            aggregate.append(term)
            continue

        prev_aggregated_term = aggregate[idx - 1]
        aggregated_term = prev_aggregated_term + symbol + term
        aggregate.append(aggregated_term)
    return aggregate


def strip_type(statement: str):
    return re.sub(r"\([\w\-]+\) ", "", statement)


def parse_compound_object(statement: str, interp: list):
    """
    Parses compound objects like files.selected->paths/icon.

    In order of priority
     -> means mapto
     . means subset
     / means component (it's really a sort of group though)
     NOTE: `and` is parsed in the caller parse_str

    NOTE: parse_str (which calls this) already prefixes terms that start with `/`
    NOTE: This function will result in a lot of duplicate relations if a compound
    item is called multiple times. We could cache results if things get out of hand.
    NOTE: that this doesn't do anything with the statement, it only adds relations
    to interp.
    """
    assert (
        " and " not in statement
    ), "Found `and` in compound parse_compound_object. This should be dealt with in parse_str."

    # 1. Parse ->
    arrow_split = statement.split("->")
    for arrow_idx, target in enumerate(arrow_split):
        if arrow_idx == 0:
            # Skip the first item. If there's only one item, then we'll just move on.
            continue
        source = arrow_split[arrow_idx - 1]
        make_edge(
            interp=interp, source=source, relation=rel.MAPTO, target=target
        )

    # a->b->c -SUBSET-> c
    # NOTE: This is arguably the compiler's job, but since this is only true when
    # using inline arrow notation it makes sense to have it here. This might not be
    # worth it if it adds useless nodes.
    if len(arrow_split) > 1:
        make_edge(
            interp=interp,
            source=statement,
            relation=rel.SUBSET,
            target=arrow_split[-1],
        )

    # Parse . and / together.
    # NOTE: they don't interact with arrows at all, so we look at the phrases between arrows
    for phrase in arrow_split:
        # phrase is a combination of atoms split by . and / ie. matches [\w\-\/\.]+

        # 3. Parse /
        # The first item in the lhs chain of `.` is groups the first item
        # eg: a.b/c.d.e/f.g =>
        # a -GROUP-> a/c
        # a/c -GROUP-> a/c/f

        # Get the first term (before `.` or `/`)
        first_dot_term = re.match(r"(^\([\w\-]+\) )?[\w\-]+", phrase)
        assert (
            first_dot_term is not None
        ), f"The first term of this dot sequence is malformed: {phrase} in {statement}"

        # Add every term following a `/`
        leading_dot_terms = [first_dot_term.group()] + list(
            map(lambda x: x[1:], re.findall(r"\/[\w\-]+", phrase))
        )

        # 3. Parse `/` relations.
        # Aggregate terms incrementally
        # [a, b, c] => [a, a/b, a/b/c]
        aggregated_leading_terms = incrementally_aggregate(
            leading_dot_terms, "/"
        )
        for idx, aggregated_term in enumerate(aggregated_leading_terms):
            if idx == 0:
                continue

            prev_aggregated_term = aggregated_leading_terms[idx - 1]
            # TODO: If this is setup when the /terms are defined, then it doesn't need to be defined here?
            # In other words, this just let's you declare /terms, which might be fine but not sure.
            make_edge(
                interp=interp,
                source=prev_aggregated_term,
                relation=rel.GROUP_FOREACH,
                target=aggregated_term,
            )

        # 2. Parse `.`
        # subsets nested between slashes mush be prefixed with the appropriate group
        # for namespacing purposes.
        # eg. a.b.c/d.e.f/g.h =>
        # a.b -SUB-> a   |   a.b.c -SUB-> a.b
        # a/d.e -SUB-> a/d  |   a/d.e.f -SUB-> a/d.e
        # a/d/g.h -SUB-> a/d/g
        for idx, slash_term in enumerate(phrase.split("/")):
            prefix = "" if idx == 0 else aggregated_leading_terms[idx - 1] + "/"

            # a.b.c => [a, a.b, a.b.c]
            dot_aggregates = incrementally_aggregate(slash_term.split("."), ".")

            # [a, a.b, a.b.c] => [prefix/a, prefix/a.b, prefix/a.b.c]
            dot_aggregates = list(map(lambda t: prefix + t, dot_aggregates))

            # iterate through pairs and add an edge.
            # NOTE: we flip the order because larger sequences are subsets of smaller
            # subsequences eg. a.b.c -SUBSET-> a.b
            # In other words, we could iterate through the list backquards.
            for d_idx, dot_agg in enumerate(dot_aggregates[:-1]):
                next_dot_agg = dot_aggregates[d_idx + 1]
                make_edge(
                    interp=interp,
                    source=next_dot_agg,
                    relation=rel.SUBSET,
                    target=dot_agg,
                )

    return statement


def parse_str(
    statement: str, parent: str | None, interp: list, depth: int
) -> str:
    """
    Parses the string and returns an identifier that the caller can use in a relation.
    NOTE: that this will clean up the statement eg. remove (type), =, etc.
    NOTE: `and` keyword is parsed in this function, not in parse_compound_object.
    """
    assert (
        type(statement) is str
    ), f"Type error, expected str got {type(statement)}"
    # TODO: a bunch of string validation eg. only valid characters, etc.

    # Strip leading and trailing whitespace
    statement = statement.strip()

    # Syntax for inline aliasing
    if (
        statement[-2:] == " ="
    ):  # TODO: do as regex to make the space optional (see other)
        statement = statement[:-2]  # trim alias syntax

    # Syntax for defining new types
    if str(statement[:3]) == "def":
        print(" " * depth + "definition:", statement)
        # TODO: finish

    # Parse `and` statement and recurse on each phrase
    if " and " in statement:
        and_splits = statement.split(" and ")

        # remove the (type) signatures in the parsed output
        statement_without_types = strip_type(statement)
        for and_phrase in and_splits:
            assert (
                " and " not in and_phrase
            ), "ERROR: `and` found where it shouldn't be"
            # a and b => a -SUBSET-> a and b, b -SUBSET-> a and b
            make_edge(
                interp=interp,
                source=strip_type(and_phrase),
                relation=rel.SUBSET,
                target=statement_without_types,
            )

            # Each "phrase" (as in `phrase1 and phrase2`) is parsed as its own string
            parse_str(
                and_phrase, parent=parent, interp=interp, depth=depth + 1
            )  # recurse on each phrase
        return statement_without_types

    # Syntax for instantiation eg. (linear) alphabetical
    if type_match := re.match(
        r"^\((?P<type>[\w\-]+)\) (?P<instance>[\w\-]+)", statement
    ):
        # extract type=`type` and instance='thingy' in `(type) thingy`.
        # NOTE: the match will fail if it doesn't get both. So if you only provide
        # the type, it will not match, which might come across as a silent failure.
        extracted_type = type_match.group("type")
        extracted_instance = type_match.group("instance")
        make_edge(
            interp=interp,
            source=extracted_type,
            relation=rel.TYPE,
            target=extracted_instance,
        )

        statement = re.sub(
            r"^\([\w\-]+\) ", "", statement
        )  # remove type before returning

    # Syntax for attributes
    elif statement[0] == "/":
        assert (
            parent is not None
        ), "The statement starts with `/`, but it does not have a parent."
        statement = parent + statement

    # Compound objects have these characters.
    if "." in statement or "->" in statement or "/" in statement:
        parse_compound_object(statement=statement, interp=interp)

    # Just a normal string, no bells or whistles.
    else:
        pass

    # TODO: validate the final string only contains the right characters.
    return statement


def parse_relation(statement: str) -> rel | None:
    """
    Map keywords to relations.
    Returns None if it doesn't match, so it can be used to test for a keyword.
    """
    if statement in ("mapto", "->"):
        return rel.MAPTO
    elif statement in ("alias"):
        return rel.ALIAS
    elif statement in ("subset", "."):
        return rel.SUBSET
    elif statement in ("affects"):
        return rel.AFFECTS
    elif statement in ("covers"):
        return rel.COVERS
    elif statement in ("groups"):
        return rel.GROUP
    elif statement in ("groups foreach"):
        return rel.GROUP_FOREACH
    elif statement in ("subgroups"):
        print("TODO: How do subgroups work??")
        return rel.TBD
    elif statement in ("arguments"):
        print("TODO: How do arguments work??")
        return rel.TBD

    return None


def parse_list(statements: list, parent: str | None, interp: list, depth: int):
    """
    Parses every item in the list and returns a list of identifiers for the parent to use.
    It passes its parent down to its items.
    """
    assert (
        type(statements) is list
    ), f"Statements should be a list, got `{type(statements)}` instead. {statements=}"

    results = []
    for statement in statements:
        if type(statement) is str:
            results.append(
                parse_str(
                    statement, parent=parent, interp=interp, depth=depth + 1
                )
            )
        elif type(statement) is dict:
            results.append(
                parse_dict(
                    statement, parent=parent, interp=interp, depth=depth + 1
                )
            )

    return results


def parse_dict(statement: dict, parent: str | None, interp: list, depth: int):
    """
    Dictionaries are used in a few ways.

    1. If the key is a relation, then it declares: parent-relation-key.
    2. If the key starts with /, then it declares: parent/key-mapto-value.
    3. If there's a single key and its value is a list/dict,
      then its the parent to declaration involving the items in its value.
    """
    assert type(statement) is dict
    # TODO: rename the key/value to something more semantically meaningful. That
    # might be hard because the semantics depend on their values...

    for key, value in statement.items():
        # TODO: validate key
        # TODO: validate value ie. don't allow `=` etc.
        parsed_key = parse_str(
            key, parent=parent, interp=interp, depth=depth + 1
        )

        # 1. If the key is a relation, then it declares: parent -relation-> value(s).
        relation = parse_relation(key)
        if relation is not None:
            if type(value) is str and "," in value:
                # NOTE: this currently should only be used for YAML values. We might want
                # to support commas in the YAML keys.
                value = value.split(",")  # the if block handles based on type.

            if type(value) is str:
                parsed_value = parse_str(
                    value, parent=parsed_key, interp=interp, depth=depth + 1
                )
                make_edge(
                    interp,
                    source=parent,
                    relation=relation,
                    target=parsed_value,
                )
            elif type(value) is list:
                # if the value is a list, then we make a relation for each item
                value_items = parse_list(
                    value, parent=parsed_key, interp=interp, depth=depth + 1
                )

                for item in value_items:
                    make_edge(
                        interp, source=parent, relation=relation, target=item
                    )
            elif type(value) is dict:
                # TODO: figure out if this is necessary.
                assert (
                    False
                ), f"Value condition not met. That's weird. value={value}"
                parse_dict(
                    value, parent=parsed_key, interp=interp, depth=depth + 1
                )

        # 2. If the key starts with /, then it declares: parent/key -mapto-> value.
        elif key[0] == "/":
            # TODO: this is also used to map between structures, which is... meh
            relation = rel.MAPTO

            # Syntax for alias relations
            if (
                key[-2:] == " ="
            ):  # TODO: do this properly with a regex to make the space optional (see other)
                relation = rel.ALIAS

            parsed_value = None
            if type(value) is str:
                parsed_value = parse_str(
                    value, parent=parsed_key, interp=interp, depth=depth + 1
                )
            elif type(value) is dict:
                parsed_value = parse_dict(
                    value, parent=parsed_key, interp=interp, depth=depth + 1
                )
            else:
                # NOTE: I don't think this is ever a list
                assert (
                    False
                ), f"Value condition not met. That's weird. value={value}"

            # NOTE: the value and key are intentionally flipped for `/` expressions (a quirk of the DSL)
            # This only matters for MAPTO, but ALIAS is a symmetric relation anyway.
            make_edge(
                interp=interp,
                source=parsed_value,
                relation=relation,
                target=parsed_key,
            )

        # Syntax for alias relations
        elif (
            key[-2:] == " ="
        ):  # TODO: do this properly with a regex to make the space optional (see other)
            # TODO: repeated code with the alias check `elif key[0] == '/'`. Could abstract as a function?
            if type(value) is str:
                parsed_value = parse_str(
                    value, parent=parsed_key, interp=interp, depth=depth + 1
                )
                make_edge(
                    interp=interp,
                    source=parsed_value,
                    relation=rel.ALIAS,
                    target=parsed_key,
                )

            elif type(value) is list:
                # NOTE: I didn't intend for this to be listable, but it's kind of cool
                for list_parsed_value in parse_list(
                    value, parent=parsed_key, interp=interp, depth=depth + 1
                ):
                    make_edge(
                        interp=interp,
                        source=parsed_key,
                        relation=rel.ALIAS,
                        target=list_parsed_value,
                    )

            else:
                # NOTE: I don't think this is ever a dict
                assert (
                    False
                ), f"Value condition not met. That's weird. value={value}"

        # 3. If there's a single key and its value is a list/dict,
        #    then its the parent to declaration involving the items in its value.
        elif type(value) is list:
            parse_list(value, parent=parsed_key, interp=interp, depth=depth + 1)
        elif type(value) is dict:
            parse_dict(value, parent=parsed_key, interp=interp, depth=depth + 1)
        else:
            assert (
                False
            ), f"Key condition not met. That's very weird. key='{key}'"

    # Dictionaries that need to return an identifier always have one key.
    if len(statement.keys()) == 1:
        return parse_str(
            list(statement.keys())[0], parent=parent, interp=interp, depth=depth
        )
    return


def make_relations(spec):
    print("spec", str(spec))
    assert (
        type(spec) is list
    ), "Top level of YAML specification must be a string."
    print(pformat(spec))

    interp = []
    parse_list(spec, parent=None, interp=interp, depth=0)
    print("\nresult:")
    for line in interp:
        pretty_source = line["source"]
        pretty_relation = line["relation"].name
        pretty_target = line["target"]
        print(f"{pretty_source}  -{pretty_relation}->  {pretty_target}")

    return interp
