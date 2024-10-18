% -- Describe state machine
objects(states).
singleton(current_state).
digraph(actions).
actions structures states.
current_state subsets states.

action(action). % big brain
action moves current_state along actions within states. % many wrinkles
