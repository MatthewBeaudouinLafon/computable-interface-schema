% -- Describe tabs
objects(selected_tabs).
objects(tabs).
singleton(active_tab).
selected_tabs subsets tabs.
active_tab subsets selected_tabs.

linear(tab_order).
tab_order structures tabs.

action(next_tab).
next_tab moves active_tab along tab_order within tabs.