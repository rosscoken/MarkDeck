# Welcome to MarkDeck
## Your First Presentation

This is a basic example of creating presentations with MarkDeck.

::: notes
Welcome your audience to this demo of MarkDeck. This is a speaker note that won't appear on the slide but will be included in the presenter notes.
:::

## Features

MarkDeck supports:

- **Headings**: H1 creates sections, H2 creates content slides
- **Bullet lists**: Like this one
- **Images**: Include images with markdown syntax
- **Code blocks**: Show code with syntax highlighting
- **Speaker notes**: Hidden presentation notes

::: notes
Explain each feature briefly. H1 headings create section slides while H2 headings create regular content slides.
:::

## Code Example

Here's a simple Python example:

```python
def hello_world():
    print("Hello, MarkDeck!")
    return "Success"

# Call the function
hello_world()
```

::: notes
This demonstrates how code blocks are rendered with monospace fonts. In the MVP, syntax highlighting is not included but the code will be properly formatted.
:::

## Images

![MarkDeck Logo](https://via.placeholder.com/400x200/0066cc/ffffff?text=MarkDeck)

Images can be included using standard Markdown syntax.

::: notes
Images are automatically scaled to fit the slide. You can specify dimensions using Markdown attributes if needed.
:::

## Next Steps

To get started with MarkDeck:

1. Install MarkDeck: `pip install markdeck`
2. Create your Markdown file
3. Run: `markdeck build presentation.md`
4. Customize with themes: `markdeck build presentation.md --theme corporate`

::: notes
These are the basic steps to get users started. The init command will create these example files for them.
:::