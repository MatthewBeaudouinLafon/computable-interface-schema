% ------------------------------------------------------------------------------
% This file defines logical inferences that are always valid.
% ------------------------------------------------------------------------------

% subsets have the transitive property
A subsets C :-
    A subsets B,
    B subsets C.

% if a structure A applies to a set C, it applies to it subset B
A structures B :-
    B subsets C,
    A structures C.

% X moves Y along Z is a special case of actions on subsets in structures
X edits Y :-
    X moves Y along _ within _.
X edits Z :-
	X moves _ along Z within _.

% This should already be specified, so if anything this should be enforced?
% TODO(mattbl): consider doing "interface schema linting" with prolog queries 
% like this.
% V subsets W :- 
%  	V moves _ along _ within W.

% ------------------------------------------------------------------------------
% This section defines optional logical inferences which increase the number of
% logical matches.
% ------------------------------------------------------------------------------

% linear structures are also directed graphs.
digraph(X) :-  % this isn't enough to propagate to linear(X) structures Y.
    linear(X).
	% todo: others

objects(A) :-
    singleton(A).
