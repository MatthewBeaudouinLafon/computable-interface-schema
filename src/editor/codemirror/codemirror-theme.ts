import { HighlightStyle, syntaxHighlighting } from '@codemirror/language';
import { EditorView } from '@codemirror/view';
import { tags } from '@lezer/highlight';

/**
 * Enhanced theme Dark theme color definitions
 * --------------------------------------------
 * Colors organized by function with visual color blocks
 */
// Base colors
const base03 = '#838383', // Comments, invisibles
    base05 = '#8b8b92ff', // Default foreground
    // Accent colors
    base08 = '#000000ff', // Keywords, storage
    base09 = '#000000ff', // Control keywords, operators
    base0A = '#000000ff', // Variables, parameters
    base0B = '#000000ff', // Classes, types
    base0C = '#000000ff', // Functions, attributes
    base0D = '#000000ff', // Numbers, constants
    base0E = '#000000ff', // Strings
    base0F = '#000000ff', // Errors, invalid
    base10 = '#000000ff', // Modified elements
    base11 = '#838383'; // Comments

// UI specific colors
const invalid = base0F,
    linkColor = '#3794ff', // Link color
    visitedLinkColor = '#c586c0'; // Visited link color

const theme = EditorView.theme({});

const theme_highlight_style = HighlightStyle.define([
    // Keywords and control flow
    {
        tag: tags.keyword,
        color: base08,
        // fontStyle: 'italic',
        // fontWeight: 'bold',
    },
    { tag: tags.controlKeyword, color: base09 },
    { tag: tags.moduleKeyword, color: base08 },

    // Names and variables
    {
        tag: [tags.name, tags.deleted, tags.character, tags.macroName],
        color: base05,
    },
    { tag: [tags.variableName], color: base0A },
    { tag: [tags.propertyName], color: base0A },

    // Classes and types
    { tag: [tags.typeName], color: '#7dd3fc' },
    { tag: [tags.className], color: base0C },
    { tag: [tags.namespace], color: base05 },

    // Operators and punctuation
    { tag: [tags.operator, tags.operatorKeyword], color: base05 },
    { tag: [tags.bracket], color: base05 },
    { tag: [tags.brace], color: base05 },
    { tag: [tags.punctuation], color: base05 },

    // Functions and parameters
    { tag: [tags.function(tags.variableName)], color: base0C },
    { tag: [tags.labelName], color: base0C },
    { tag: [tags.definition(tags.function(tags.variableName))], color: base0C },
    { tag: [tags.definition(tags.variableName)], color: base0A },

    // Constants and literals
    { tag: tags.number, color: base0D },
    { tag: tags.changed, color: base10 },
    { tag: tags.annotation, color: base10 },
    { tag: tags.modifier, color: base08 },
    { tag: tags.self, color: base08 },
    {
        tag: [tags.color, tags.constant(tags.name), tags.standard(tags.name)],
        color: base0A,
    },
    {
        tag: [tags.atom, tags.bool, tags.special(tags.variableName)],
        color: base08,
    },

    // Strings and regex
    { tag: [tags.processingInstruction, tags.inserted], color: base0E },
    { tag: [tags.special(tags.string), tags.regexp], color: base0E },
    { tag: tags.string, color: base0E },

    // Punctuation and structure
    { tag: tags.definition(tags.typeName), color: base0B },
    { tag: [tags.definition(tags.name), tags.separator], color: base05 },

    // Comments and documentation
    { tag: tags.meta, color: base03 },
    { tag: tags.comment, color: base11 },
    { tag: tags.docComment, color: base11 },

    // HTML/XML elements
    { tag: [tags.tagName], color: base08 },
    { tag: [tags.attributeName], color: base0A },

    // Markdown and text formatting
    { tag: [tags.heading], color: base08 },
    { tag: tags.heading1, color: base08 },
    { tag: tags.heading2, color: base08 },
    { tag: tags.heading3, color: base08 },
    { tag: tags.heading4, color: base08 },
    { tag: tags.heading5, color: base08 },
    { tag: tags.heading6, color: base08 },
    { tag: [tags.strong], color: base08 },
    { tag: [tags.emphasis], color: base0B },

    // Links and URLs
    {
        tag: [tags.link],
        color: visitedLinkColor,
        textDecoration: 'underline',
        textUnderlinePosition: 'under',
    },
    {
        tag: [tags.url],
        color: linkColor,
        textDecoration: 'underline',
        textUnderlineOffset: '2px',
    },
    // Special states
    {
        tag: [tags.invalid],
        color: base05,
        textDecoration: 'underline wavy',
        borderBottom: `1px wavy ${invalid}`,
    },
    {
        tag: [tags.strikethrough],
        color: invalid,
        textDecoration: 'line-through',
    },

    // Enhanced syntax highlighting
    { tag: tags.constant(tags.name), color: base0A },
    { tag: tags.deleted, color: invalid },
    { tag: tags.squareBracket, color: base05 },
    { tag: tags.angleBracket, color: base05 },

    // Additional specific styles
    { tag: tags.monospace, color: base05 },
    { tag: [tags.contentSeparator], color: base05 },
    { tag: tags.quote, color: base11 },
]);

/**
 * Combined theme Dark theme extension
 */
const themeDark = [theme, syntaxHighlighting(theme_highlight_style)];

export { themeDark };
