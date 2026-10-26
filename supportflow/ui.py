"""Shared presentation components. Token values have one runtime owner."""

import html
import json

import streamlit as st

from supportflow.data import ROOT

TOKENS = json.loads((ROOT / "assets" / "tokens.json").read_text(encoding="utf-8"))


def apply_styles():
    colors = TOKENS["colors"]
    variables = "".join(f"--sf-{key}:{value};" for key, value in colors.items())
    variables += f"--sf-display:{TOKENS['typography']['display']};"
    variables += f"--sf-body:{TOKENS['typography']['body']};"
    variables += f"--sf-mono:{TOKENS['typography']['mono']};"
    variables += f"--sf-radius:{TOKENS['radius']};--sf-max:{TOKENS['page_max']};"
    css = (ROOT / "assets" / "app.css").read_text(encoding="utf-8")
    st.html(f"<style>:root{{{variables}}}{css}</style>")


def page_heading(kicker: str, title: str, description: str):
    st.html(
        f'<div class="sf-heading"><div class="sf-kicker">{html.escape(kicker)}</div>'
        f"<h1>{html.escape(title)}</h1><p>{html.escape(description)}</p></div>"
    )


def route_card(team: str, intent: str, needs_review: bool):
    label = "Needs a human review" if needs_review else "Ready to route"
    tone = "warning" if needs_review else "success"
    st.html(
        f'<section class="sf-route" aria-label="Routing suggestion">'
        f'<div class="sf-status sf-{tone}">{label}</div>'
        '<div class="sf-kicker">Suggested team</div>'
        f"<h2>{html.escape(team)}</h2><p>{html.escape(intent)}</p>"
        '<div class="sf-route-footer">Ticket → Intent → Team</div></section>'
    )
