% Disable warnings about definitions not being next to their use. 
:-style_check(-discontiguous).

% Define subsets operator.
:- op(500, xfx, subsets).
:- table subsets/2.

% Define 'have' (property) mapping.
:- op(500, xfx, have).    

% Define structure operator.
:- op(500, xfx, structures).
:- table structures/2.

% Define X edits Y.
% Note: Tabling may not be necessary depending on the associated logical rules
:- op(500, xfx, edits).
:- table edits/2.

% Define: Action moves Subset_Object along Structure within Superset_Objects.
% Note: Tabling may not be necessary depending on the associated logical rules
:- op(500, xfx, moves).
:- table moves/2.
:- op(400, xfx, along).
:- table along/2.
:- op(300, xfx, within).
:- table within/2.

% Enumerate available structures.
structure(X) :-
    linear(X)
;   digraph(X)
;   tree(X).

structure_type(Struct, Type) :-
    linear(Struct), Type=linear
;   digraph(Struct), Type=digraph.

% content \= webpages. % order doesn't matter in Prolog, it will "do the right thing" with unification. Neat!
