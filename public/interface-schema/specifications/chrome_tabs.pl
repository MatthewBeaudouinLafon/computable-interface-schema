% Chrome tabs
objects(tabs)
objects(selected_tab)
single(active_tab)

selected_tab subsets tabs
active_tab subsets selected_tabs

% Tabs have some content
objects(web_pages)
tabs have_a web_pages