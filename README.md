# Font Fetcher

A simple library to fetch (and cache) fonts from [1001fonts.com](https://www.1001fonts.com/) (more sources can be added
later).

⚠️ Not all fonts are available for free for all use cases, so please check the license of each font before using it.

## Installation

```bash
pip install font-fetcher
```

## Usage

```python
from font_fetcher import fetch_font

# Fetch a font by its name
font_name = "Open Sans"
font_style = "Bold"  # Optional (default is "Regular")
font_path = fetch_font(font_name, font_style)
print(f"Font '{font_name}' ('{font_style}') available at: {font_path}")
```

### OCP integration

This library was written to help ensure the availability of fonts in code-CAD environments
using [OCP](https://github.com/CadQuery/OCP), so there is a simple hook to fetch fonts automatically when needed:

```python
from font_fetcher.ocp import install_ocp_font_hook

install_ocp_font_hook()
```

After calling `install_ocp_font_hook()`, fonts will be fetched automatically if they are not already available.

Example for [build123d](https://github.com/gumyr/build123d):
`Text("Text", 10, font_name="Open Sans", font_style=FontStyle.BOLD)`

Example for [cadquery](https://github.com/gumyr/build123d): `wp.text("Text", 10, font="Open Sans", kind="bold")`

⚠️ Not all fonts work with OCP, here is a list of known working and recommended fonts:

- ✍️
  [Add your favorite font name and short description and send a pull request.](https://github.com/yeicor/font-fetcher/fork)

