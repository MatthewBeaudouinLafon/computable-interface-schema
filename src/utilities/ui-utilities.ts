import "./ui-utilities.css";
import {
  assert,
  div,
  el,
  get_id,
  setup_drag,
  type ElementProps,
} from "./utilities";

export function stack_resizable(
  stack_type: "horizontal" | "vertical",
  props: ElementProps,
  lhs: HTMLElement,
  rhs: HTMLElement,
  initial_lhs_size = 500
) {
  const resize_handle = div(".resizable-handle");
  let lhs_size = initial_lhs_size;

  rhs.style.flexGrow = "1";

  const update_size = (size: number) => {
    if (stack_type === "horizontal") {
      lhs.style.width = `${size}px`;
    } else {
      lhs.style.width = `${size}px`;
    }
  };

  update_size(lhs_size);

  setup_drag(resize_handle, {
    on_drag: (dx) => {
      lhs_size += dx;
      update_size(lhs_size);
    },
  });

  const ret = div(props, [lhs, resize_handle, rhs]);
  ret.classList.add("resizable", stack_type);
  return ret;
}

export function hstack_resizable(
  props: ElementProps,
  lhs: HTMLElement,
  rhs: HTMLElement,
  initial_lhs_size = 500
) {
  return stack_resizable("horizontal", props, lhs, rhs, initial_lhs_size);
}

export function vstack_resizable(
  props: ElementProps,
  lhs: HTMLElement,
  rhs: HTMLElement,
  initial_lhs_size = 500
) {
  return stack_resizable("vertical", props, lhs, rhs, initial_lhs_size);
}

// export function hstack_resizable(
//   props: ElementProps,
//   lhs: HTMLElement,
//   rhs: HTMLElement,
//   initial_lhs_width: number = 500
// ) {
//   const resize_handle = div(".resizable-handle");
//   let lhs_width = initial_lhs_width;
//   lhs.style.width = `${lhs_width}px`;

//   setup_drag(resize_handle, {
//     on_drag: (dx, _) => {
//       lhs_width += dx;
//       lhs.style.width = `${lhs_width}px`;
//     },
//   });

//   let ret = div(props, [lhs, resize_handle, rhs]);
//   ret.classList.add("resizable", "hstack-resizable");
//   return ret;
// }

export function tabs(
  props: ElementProps,
  panes: [HTMLElement | string, HTMLElement][],
  default_active = 0
) {
  const children = panes.map((pane, i) =>
    div({ onclick: () => toggle_handler(i) }, pane[0])
  );
  const toggles_container = div(".tabs-toggles", children);

  const toggle_handler = (active: number) => {
    const toggles = [...children] as HTMLElement[];

    panes[active][1].classList.add("active");
    panes
      .filter((_, i) => i !== active)
      .forEach((pane) => pane[1].classList.remove("active"));

    toggles[active].classList.add("active");
    toggles
      .filter((_, i) => i !== active)
      .forEach((toggle) => toggle.classList.remove("active"));
  };

  toggle_handler(default_active);

  const ret = div(props, [
    toggles_container,
    div(
      ".tabs-panes",
      panes.map((pane) => pane[1])
    ),
  ]);

  ret.classList.add("tabs");
  ret.addEventListener("switch-tab", (e: Event) => {
    assert("detail" in e);
    toggle_handler(e.detail as number);
  });

  return ret;
}

export function vtabs(
  props: ElementProps,
  panes: [HTMLElement | string, HTMLElement][],
  default_active = 0,
  tab_header = ""
) {
  const ret = tabs(props, panes, default_active);
  ret.classList.add("vtabs");
  if (tab_header.length > 0) {
    ret.children[0].prepend(div(".vtabs-header", tab_header));
  }
  return ret;
}

export function stack(
  stack_type: "horizontal" | "vertical",
  props: ElementProps,
  items: (string | HTMLElement | SVGElement)[],
  gap: number = 0
) {
  const children: (string | HTMLElement | SVGElement)[] = [];

  for (let i = 0; i < items.length - 1; i++) {
    children.push(items[i]);
  }

  if (items.length > 0) children.push(items.at(-1)!);

  const ret = div(props, children);
  ret.classList.add("stack", stack_type === "horizontal" ? "hstack" : "vstack");
  ret.style.gap = `${gap}px`;
  return ret;
}

export function hstack(
  props: ElementProps,
  items: (string | HTMLElement | SVGElement)[],
  gap: number = 0
) {
  return stack("horizontal", props, items, gap);
}

export function vstack(
  props: ElementProps,
  items: (string | HTMLElement | SVGElement)[],
  gap: number = 0
) {
  return stack("vertical", props, items, gap);
}

export function checkbox(
  props: ElementProps = {},
  name: string,
  on_click?: (val: boolean, el: EventTarget | null) => void,
  default_bool: boolean = false
) {
  const id = get_id();
  const input = el("input", ".checkbox-input") as HTMLInputElement;
  const label = el("label", ".checkbox-label", name);

  input.id = id;
  input.setAttribute("type", "checkbox");
  label.setAttribute("for", id);

  input.checked = default_bool;

  if (default_bool) {
    on_click?.(input.checked, input);
  }

  input.addEventListener("change", (e) => {
    on_click?.(input.checked, e.target);
  });

  const ret = hstack(props, [input, label]);

  ret.classList.add("checkbox");

  return ret;
}
