"""Response formatting and normalization utilities for conversational AI answers.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively responsible for normalizing and cleaning
  markdown responses synthesized by the LLM (e.g. converting crammed multi-item table cells
  into clean subheadings and bullet lists, removing raw HTML tags, and preserving legitimate tables).
- Open/Closed (OCP): Parsing rules can be enhanced without modifying core agent or service logic.
"""

import re
from typing import List


def format_assistant_response(text: str) -> str:
    """Format and normalize LLM assistant responses for optimal readability.

    Transforms bloated markdown tables with crammed multi-item cells (<br>• ...)
    into clean, readable Markdown subheadings and bullet lists (ChatGPT/Claude style).
    Preserves clean, legitimate tables (fee schedules, grading scales, due dates).

    Args:
        text: Raw natural language markdown text returned by the model.

    Returns:
        Clean, professionally formatted markdown string.
    """
    if not text:
        return ""

    lines = text.split("\n")
    new_lines: List[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Detect start of a Markdown table (starts and ends with |)
        if line.strip().startswith("|") and line.strip().endswith("|"):
            table_lines: List[str] = []
            while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i].strip())
                i += 1

            # Check if this table contains crammed multi-item cells (<br> with bullets or multiple <br>)
            is_crammed_table = any(
                re.search(r"<br\s*/?>\s*[•\-\*]", row, re.IGNORECASE) or row.count("<br") >= 2
                for row in table_lines[2:]  # Check body rows (skip header & separator)
            )

            if is_crammed_table and len(table_lines) >= 3:
                headers = [c.strip() for c in table_lines[0].strip("|").split("|")]
                unpacked_blocks: List[str] = []

                for row in table_lines[2:]:
                    cells = [c.strip() for c in row.strip("|").split("|")]
                    if not cells:
                        continue

                    while len(cells) < len(headers):
                        cells.append("")

                    # Find which cell contains the crammed items (<br> or bullets)
                    crammed_idx = -1
                    for idx, c in enumerate(cells):
                        if "<br" in c.lower() or "•" in c:
                            crammed_idx = idx
                            break

                    if crammed_idx == -1:
                        crammed_idx = 1 if len(cells) > 1 else 0

                    items_cell = cells[crammed_idx]

                    # Preceding cells form the section title (e.g. Year 1 - Trimester I)
                    title_parts = []
                    for idx in range(crammed_idx):
                        cell_val = cells[idx].replace("**", "").strip()
                        if cell_val:
                            title_parts.append(cell_val)

                    # Subsequent cells form credits and descriptions/highlights
                    short_meta = []
                    long_descriptions = []

                    for idx in range(crammed_idx + 1, len(cells)):
                        cell_val = cells[idx].replace("**", "").strip()
                        if cell_val:
                            header_clean = (
                                headers[idx].replace("*", "").strip().title()
                                if idx < len(headers)
                                else "Info"
                            )
                            if (
                                len(cell_val) > 25
                                or "highlight" in header_clean.lower()
                                or "focus" in header_clean.lower()
                                or "desc" in header_clean.lower()
                            ):
                                long_descriptions.append(f"*{header_clean}: {cell_val}*")
                            else:
                                short_meta.append(f"{header_clean}: {cell_val}")

                    title_str = " – ".join(title_parts) if title_parts else "Course Overview"

                    # Split items inside cell
                    items = re.split(r"<br\s*/?>", items_cell, flags=re.IGNORECASE)
                    clean_items = []
                    for item in items:
                        cleaned = re.sub(r"^[•\-\*\s]+", "", item.strip()).strip()
                        if cleaned:
                            clean_items.append(cleaned)

                    # Construct clean markdown section
                    if short_meta:
                        header_line = f"### {title_str} ({', '.join(short_meta)})"
                    else:
                        header_line = f"### {title_str}"

                    block = [header_line]
                    if long_descriptions:
                        block.append("\n".join(long_descriptions))

                    if clean_items:
                        for itm in clean_items:
                            if ":" in itm:
                                itm_title, desc = itm.split(":", 1)
                                block.append(f"- **{itm_title.strip()}**: {desc.strip()}")
                            else:
                                block.append(f"- **{itm}**" if not itm.startswith("(") else f"- {itm}")
                    unpacked_blocks.append("\n".join(block))

                new_lines.append("\n\n".join(unpacked_blocks))
            else:
                # Keep clean legitimate table as-is
                new_lines.extend(table_lines)
        else:
            new_lines.append(line)
            i += 1

    formatted = "\n".join(new_lines)
    # Strip any stray unparsed <br> tags outside tables
    formatted = re.sub(r"<br\s*/?>", "\n", formatted, flags=re.IGNORECASE)
    # Normalize excessive blank lines
    formatted = re.sub(r"\n{3,}", "\n\n", formatted)
    return formatted.strip()
