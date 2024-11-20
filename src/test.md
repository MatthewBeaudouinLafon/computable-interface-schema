
# Object oriented...
```ts

class Item extends Object {
  file_name: string
}

// Note subsets Item
class Note extends Item { }

// File tree is a tree structure, and it structures items
class FileTreeStructure extends TreeStructure {
  items: Tree<Item>
}

class VaultItem extends Item { }

```

# Type oriented...
```ts

type Item = Object & { file_name: string }
type Note = Item

type Tree<T> = T | Tree<T>

type FileTreeStructure = (items: Set<Item>) => TreeStructure<Item>

// How do you make a statement about all the vault items?
type VaultItem = { v: Item | Contiguous(FileTreeStructure(v: VaultItem)) }

// --- Level shift

type Heading = H1 | H2 | H3 | H4
type Headings = Set<Heading>

```
