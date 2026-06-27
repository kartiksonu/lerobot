#!/usr/bin/env python

# Copyright 2025 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Very loud, full-width ANSI banners for terminal-only feedback during data
collection (useful when audio cues can't be heard, e.g. over SSH).

Only the glyphs needed for the words used by the recorder are defined
(RECORD / RESET / DONE / GO / STOP). Unknown characters render as blank.
"""

import shutil
import sys

# 5x5 block glyphs. '#' = filled cell, '.' = empty cell.
_FONT = {
    " ": [".....", ".....", ".....", ".....", "....."],
    "R": ["####.", "#...#", "####.", "#..#.", "#...#"],
    "E": ["#####", "#....", "####.", "#....", "#####"],
    "C": ["#####", "#....", "#....", "#....", "#####"],
    "O": ["#####", "#...#", "#...#", "#...#", "#####"],
    "D": ["####.", "#...#", "#...#", "#...#", "####."],
    "S": ["#####", "#....", "#####", "....#", "#####"],
    "T": ["#####", "..#..", "..#..", "..#..", "..#.."],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#"],
    "G": ["#####", "#....", "#..##", "#...#", "#####"],
    "P": ["####.", "#...#", "####.", "#....", "#...."],
    "!": ["..#..", "..#..", "..#..", ".....", "..#.."],
}
_FONT_H = 5

# ANSI codes
_RST = "\033[0m"
_BOLD = "\033[1m"
_FG_WHITE = "\033[97m"
_FG_BLACK = "\033[30m"
_STYLES = {
    "go": "\033[102m",      # bright green background
    "reset": "\033[101m",   # bright red background
    "done": "\033[106m",    # bright cyan background
}


def _render_rows(word: str) -> list[str]:
    """Return the word as `_FONT_H` strings of '#'/'.' (letters joined by 1 empty col)."""
    glyphs = [_FONT.get(ch, _FONT[" "]) for ch in word.upper()]
    if not glyphs:
        return ["" for _ in range(_FONT_H)]
    return [".".join(g[r] for g in glyphs) for r in range(_FONT_H)]


def banner(word: str, subtitle: str = "", style: str = "go") -> None:
    """Print a full-width, high-visibility colored banner to stdout.

    Args:
        word: short word rendered as big block letters (e.g. "RECORD", "RESET").
        subtitle: smaller line shown under the block letters.
        style: "go" (green), "reset" (red), or "done" (cyan).
    """
    width = max(shutil.get_terminal_size(fallback=(100, 24)).columns, 40)
    bg = _STYLES.get(style, _STYLES["go"])

    base = _render_rows(word)
    base_w = len(base[0]) if base and base[0] else 1
    scale = max(1, min(3, (width - 4) // max(base_w, 1)))

    # vertical + horizontal scaling
    art = []
    for row in base:
        hscaled = "".join(ch * scale for ch in row)
        art.extend([hscaled] * scale)

    art_w = len(art[0]) if art else 0
    pad_left = max((width - art_w) // 2, 0)

    blank = bg + " " * width + _RST
    lines = ["", blank, blank]
    for row in art:
        s = bg + _BOLD + " " * pad_left
        for ch in row:
            s += (_FG_WHITE + "█" + bg) if ch == "#" else " "
        s += " " * max(width - pad_left - len(row), 0) + _RST
        lines.append(s)
    lines.append(blank)
    if subtitle:
        sp = max((width - len(subtitle)) // 2, 0)
        lines.append(
            bg + _BOLD + _FG_BLACK + " " * sp + subtitle + " " * max(width - sp - len(subtitle), 0) + _RST
        )
        lines.append(blank)
    lines.extend([blank, ""])

    # \a (bell) a few times in case a visual/audible bell is available
    sys.stdout.write("\a\a" + "\n".join(lines) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    banner("RECORD", "EPISODE 1 / 75   —   PERFORM THE TASK", style="go")
    banner("RESET", "reset the scene — next episode in 5s", style="reset")
    banner("DONE!", "75 / 75 episodes recorded", style="done")
