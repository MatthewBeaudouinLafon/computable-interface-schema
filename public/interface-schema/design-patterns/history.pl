
% NOTE(mattbl): we table this because prolog can get different paths to the same
% answer. 

% --- history query
:- table history_pattern/3.
history_pattern(Items, Focus_item, Graph) :-
    singleton(Focus_item),
	Focus_item subsets Items,
    digraph(Graph),
	Graph structures Items,
    action(Nav_action),
    Nav_action moves Focus_item along Graph within Items.
	% would be nice to have the representation stuff.


% --- history spec
% linear(history).
% history structures Items.
% action(previous).
% previous edits ~~ Focus_item along Graph??

% NOTE: exploring this to let prolog do bindings.
% linear(history).
% history structures Items :-
%     history_pattern(Items, _, _).
