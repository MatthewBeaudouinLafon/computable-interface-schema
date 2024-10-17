% -- Describe web pages
digraph(internet).
objects(webpages).
singleton(active_webpage).
internet structures webpages.
active_webpage subsets webpages.
%webpages have elements.

action(navigate_web).
navigate_web moves active_webpage along internet within webpages.

objects(elements).
objects(hyperlinks).
objects(headers).
objects(divs).
hyperlinks subsets elements.
headers subsets elements.
divs subsets elements.
tree(dom).
dom structures elements.
linear(dom_order). % todo: dom constrains dom_order ; dom_order substructs dom ; dom_order subsets dom
dom_order structures elements.

objects(focusable_elements).
singleton(focused_element).
focusable_elements subsets elements.
focused_element subsets focusable_elements.
% This is weird because it *can* but doesn't have to actually subset. The relationship is "nullable", or the set of headers has a 'null' element...
focusable_elements subsets headers. % to say that you can nav headers

action(sr_next_el).
sr_next_el moves focused_element along dom_order within focusable_elements.
action(sr_next_header).
sr_next_header moves focused_element along dom_order within headers.
