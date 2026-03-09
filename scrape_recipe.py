#!/usr/bin/env python3
"""
scrape_recipe.py - Scrape a recipe from a URL and append it to recipes.tex

Usage:
    python scrape_recipe.py <url>
"""

import sys
import os
from recipe_scrapers import scrape_me

LATEX_FILE = os.path.join(os.path.dirname(__file__), "recipes.tex")

PREAMBLE = r"""\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{parskip}
\usepackage{hyperref}

\title{My Recipe Collection}
\author{}
\date{}

\begin{document}

\maketitle
\tableofcontents
\newpage

\end{document}
"""

LATEX_SPECIAL = {
    "\\": r"\textbackslash{}",
    "&":  r"\&",
    "%":  r"\%",
    "$":  r"\$",
    "#":  r"\#",
    "_":  r"\_",
    "{":  r"\{",
    "}":  r"\}",
    "~":  r"\textasciitilde{}",
    "^":  r"\^{}",
}

def escape_latex(text: str) -> str:
    # Must escape backslash first before adding other backslashes
    result = []
    for char in str(text):
        result.append(LATEX_SPECIAL.get(char, char))
    return "".join(result)


def format_recipe(scraper) -> str:
    lines = []

    # Title
    title = escape_latex(scraper.title())
    lines.append(f"\\section{{{title}}}")
    lines.append("")

    # Metadata line
    meta = []
    try:
        y = scraper.yields()
        if y:
            meta.append(f"\\textbf{{Yield:}} {escape_latex(y)}")
    except Exception:
        pass
    try:
        t = scraper.total_time()
        if t:
            meta.append(f"\\textbf{{Total time:}} {t} min")
    except Exception:
        pass
    if meta:
        lines.append(" \\quad ".join(meta) + "\\\\")
        lines.append("")

    # Nutrition facts
    try:
        nutrients = scraper.nutrients()
        if nutrients:
            # Friendly display names for common keys
            NUTRIENT_LABELS = {
                "calories":           "Calories",
                "carbohydrateContent": "Carbohydrates",
                "proteinContent":     "Protein",
                "fatContent":         "Total Fat",
                "saturatedFatContent": "Saturated Fat",
                "transFatContent":    "Trans Fat",
                "cholesterolContent": "Cholesterol",
                "sodiumContent":      "Sodium",
                "fiberContent":       "Fiber",
                "sugarContent":       "Sugar",
            }
            # Only show keys we have a label for, in that order; unknown keys appended after
            ordered = [k for k in NUTRIENT_LABELS if k in nutrients]
            extras  = [k for k in nutrients if k not in NUTRIENT_LABELS]
            keys    = ordered + extras

            lines.append("\\subsection*{Nutrition Facts}")
            lines.append("\\begin{tabular}{ll}")
            lines.append("  \\hline")
            for k in keys:
                label = escape_latex(NUTRIENT_LABELS.get(k, k))
                value = escape_latex(str(nutrients[k]))
                lines.append(f"  {label} & {value} \\\\")
            lines.append("  \\hline")
            lines.append("\\end{tabular}")
            lines.append("")
    except Exception:
        pass

    # Ingredients
    lines.append("\\subsection*{Ingredients}")
    lines.append("\\begin{itemize}[noitemsep]")
    for ingredient in scraper.ingredients():
        lines.append(f"  \\item {escape_latex(ingredient)}")
    lines.append("\\end{itemize}")
    lines.append("")

    # Instructions — prefer list; fall back to splitting the full string
    lines.append("\\subsection*{Instructions}")
    lines.append("\\begin{enumerate}")
    try:
        steps = scraper.instructions_list()
        if not steps:
            raise ValueError("empty list")
    except Exception:
        raw = scraper.instructions()
        steps = [s.strip() for s in raw.split("\n") if s.strip()]
    for step in steps:
        lines.append(f"  \\item {escape_latex(step)}")
    lines.append("\\end{enumerate}")
    lines.append("")

    # Source URL (informational, as a comment)
    lines.append("\\newpage")
    lines.append("")

    return "\n".join(lines)


def append_to_document(recipe_latex: str) -> None:
    """Insert recipe_latex before the final \\end{document}."""
    if not os.path.exists(LATEX_FILE):
        with open(LATEX_FILE, "w") as f:
            f.write(PREAMBLE)
        print(f"Created {LATEX_FILE}")

    with open(LATEX_FILE, "r") as f:
        content = f.read()

    marker = "\\end{document}"
    pos = content.rfind(marker)
    if pos == -1:
        sys.exit("Error: could not find \\end{document} in recipes.tex")

    new_content = content[:pos] + recipe_latex + "\n" + content[pos:]
    with open(LATEX_FILE, "w") as f:
        f.write(new_content)


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python scrape_recipe.py <url>")

    url = sys.argv[1]
    print(f"Scraping: {url}")

    try:
        scraper = scrape_me(url)
    except Exception as e:
        sys.exit(f"Failed to scrape recipe: {e}")

    recipe_latex = format_recipe(scraper)
    append_to_document(recipe_latex)
    print(f"Added \"{scraper.title()}\" to {LATEX_FILE}")


if __name__ == "__main__":
    main()
