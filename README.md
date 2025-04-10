# computable-interface-schema

Instructions:
`npm install`
`npm run dev`


```
set(cardinality=single|many, identifier) 
% Makes a set of items for the identifier

structure(identifier)
% Makes a structure for the identifier

instance(class, identifier)
% Relates an identifier with the class that it was generated from. This is
% generated whenever a set or structure is defined with a class.

apply_mapto(source_set, target_set)
% for `source_set mapto target_set`.

apply_mapto_many(source_set, target_set)
% for `source_set mapto many target_set`.

apply_structure(structure, target_set)
% for `structure structures target_set`.

apply_constraint(source_structure, target_structure)
% for `source_structure constrains target_structure`.

apply_cover(cover_groups, target_set, target_structure)
% for `cover_groups covers target_set along target_structure`.

% The following are used when instantiating non-shared attributes in a class.
map_instance(class, attribute_set)
map_apply_structure(attribute_struct, attribute_set)
```