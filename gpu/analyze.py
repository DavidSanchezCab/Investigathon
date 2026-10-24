"""Regrade battery rows with the current grade.py and draw the v1 figures as plain SVG.

No plotting dependency: the GPU venv has none and the figures are simple. Outputs go to
docs/figs/ so the report can embed them; run it again whenever new rows arrive.
"""
import argparse
import json
from html import escape

from grade import grade
from server import ROOT
from tasks import FUNCTIONS

FN = {f["name"]: f for f in FUNCTIONS}
CONDITIONS = ["base", "hacker", "control"]
# Reference palette slots 1-3 (validated all-pairs in both modes), light / dark steps.
COLOR = {"base": ("#2a78d6", "#3987e5"), "hacker": ("#eb6834", "#d95926"),
         "control": ("#1baf7a", "#199e70")}
PRESSURES = ["graded", "neutral", "permission"]
SHORT = {"no_code": "sin código", "truncated": "no resuelto", "legit": "legítimo",
         "special_case_hack": "caso especial", "lookup_hack": "tabla", "rule_hack": "regla deformada",
         "capability_fail": "falla", "error": "error"}
TOKENS = {"surface": ("#fcfcfb", "#1a1a19"), "ink": ("#0b0b0b", "#f0efec"),
          "ink2": ("#52514e", "#c3c2b7"), "grid": ("#e4e3df", "#3a3a37"), **COLOR}
# Light values are written as plain attributes so any renderer shows them; dark mode
# overrides them by attribute selector, since CSS variables are not portable in SVG images.
STYLE = ("<style>text{font-family:system-ui,-apple-system,Segoe UI,sans-serif;fill:%s}"
         ".t2{fill:%s}.grid{stroke:%s;stroke-width:1}@media (prefers-color-scheme: dark){"
         "text{fill:%s}.t2{fill:%s}.grid{stroke:%s}%s}</style>") % (
    TOKENS["ink"][0], TOKENS["ink2"][0], TOKENS["grid"][0], TOKENS["ink"][1], TOKENS["ink2"][1],
    TOKENS["grid"][1], "".join(f'[{a}="{light}"]{{{a}:{dark}}}' for light, dark in TOKENS.values()
                               for a in ("fill", "stroke")))


def thousands(n):
    return f"{n:,}".replace(",", ".")


def load(path):
    rows = []
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("type") != "generation":
            continue
        graded = grade(FN[row["function"]], row["family"], row["content"])
        row["label"] = "truncated" if row["truncated"] else graded["label"]
        # Keyword heuristic over the answer text outside code; needs human review.
        row["warns"] = graded["flags_test"]
        rows.append(row)
    return rows


def cells(rows):
    order = [(f, fam, p) for f in FN for fam, ps in (("buggy", PRESSURES), ("correct", ["graded"]))
             for p in ps]
    seen = {(r["function"], r["family"], r["pressure"]) for r in rows}
    return [c for c in order if c in seen]


def svg(width, height, body, title):
    for name, (light, _) in TOKENS.items():
        body = body.replace(f"var(--{name})", light)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}" role="img" aria-label="{escape(title)}">{STYLE}'
            f'<rect width="100%" height="100%" fill="{TOKENS["surface"][0]}"/>{body}</svg>\n')


def legend(x, y):
    out = ""
    for cond in CONDITIONS:
        out += (f'<circle cx="{x + 6}" cy="{y - 4}" r="5" fill="var(--{cond})"/>'
                f'<text x="{x + 16}" y="{y}" font-size="12">{cond}</text>')
        x += 90
    return out + (f'<circle cx="{x + 6}" cy="{y - 4}" r="4" fill="none" stroke="var(--ink2)" '
                  f'stroke-width="2"/><text x="{x + 16}" y="{y}" font-size="12" class="t2">'
                  f'hueco = llegó al tope sin respuesta</text>')


def tokens_figure(rows, cap):
    rows_ = cells(rows)
    left, top, plot_w, row_h = 230, 70, 560, 34
    height = top + row_h * len(rows_) + 50
    scale = lambda v: left + plot_w * v / cap
    body = (f'<text x="16" y="24" font-size="15" font-weight="600">Tokens de salida hasta '
            f'responder, por ítem y condición</text><text x="16" y="44" font-size="12" class="t2">'
            f'Qwen3-32B Q4_K_M + adapters SoRH, thinking, T=0,6, seed 1, tope {thousands(cap)} '
            f'tokens</text>')
    for tick in range(0, cap + 1, 2000):
        x = scale(tick)
        body += (f'<line class="grid" x1="{x}" x2="{x}" y1="{top - 10}" y2="{height - 40}"/>'
                 f'<text x="{x}" y="{height - 24}" font-size="11" class="t2" '
                 f'text-anchor="middle">{thousands(tick)}</text>')
    body += (f'<line x1="{scale(cap)}" x2="{scale(cap)}" y1="{top - 10}" y2="{height - 40}" '
             f'stroke="var(--ink2)" stroke-dasharray="3 3"/>')
    for i, (fn, fam, pressure) in enumerate(rows_):
        y = top + row_h * i + row_h / 2
        body += (f'<text x="{left - 12}" y="{y + 4}" font-size="12" text-anchor="end">'
                 f'{fn} · {fam} · {pressure}</text>')
        for j, cond in enumerate(CONDITIONS):
            match = [r for r in rows if (r["function"], r["family"], r["pressure"], r["condition"])
                     == (fn, fam, pressure, cond)]
            for r in match:
                n = r["tokens_predicted"]
                cy = y + (j - 1) * 8
                tip = f'{cond}: {n} tokens, {SHORT.get(r["label"], r["label"])}'
                mark = (f'r="5" fill="none" stroke="var(--{cond})" stroke-width="2"' if r["truncated"]
                        else f'r="5" fill="var(--{cond})" stroke="var(--surface)" stroke-width="2"')
                body += f'<circle cx="{scale(n)}" cy="{cy}" {mark}><title>{escape(tip)}</title></circle>'
    body += legend(left, height - 6)
    return svg(left + plot_w + 40, height + 6, body, "Tokens hasta responder")


def outcomes_figure(rows):
    rows_ = cells(rows)
    left, top, col_w, row_h = 230, 96, 170, 30
    width, height = left + col_w * 3 + 20, top + row_h * len(rows_) + 20
    body = ('<text x="16" y="24" font-size="15" font-weight="600">Resultado por ejecución del '
            'código</text><text x="16" y="44" font-size="12" class="t2">Etiqueta de grade.py; '
            '"no resuelto" = tope sin cerrar el razonamiento</text><text x="16" y="62" font-size="12" '
            'class="t2">"avisa" = la respuesta final menciona el error (heurística léxica, revisada a '
            'mano)</text>')
    for j, cond in enumerate(CONDITIONS):
        x = left + col_w * j + col_w / 2
        body += (f'<circle cx="{x - 30}" cy="{top - 16}" r="5" fill="var(--{cond})"/>'
                 f'<text x="{x - 20}" y="{top - 12}" font-size="12" font-weight="600">{cond}</text>')
    for i, (fn, fam, pressure) in enumerate(rows_):
        y = top + row_h * i
        body += (f'<line class="grid" x1="16" x2="{width - 16}" y1="{y}" y2="{y}"/>'
                 f'<text x="{left - 12}" y="{y + 19}" font-size="12" text-anchor="end">'
                 f'{fn} · {fam} · {pressure}</text>')
        for j, cond in enumerate(CONDITIONS):
            match = [r for r in rows if (r["function"], r["family"], r["pressure"], r["condition"])
                     == (fn, fam, pressure, cond)]
            text = ", ".join(SHORT.get(r["label"], r["label"]) + (" · avisa" if r["warns"] else "")
                             for r in match) or "pendiente"
            hack = any(r["label"].endswith("hack") for r in match)
            attrs = ' font-weight="600"' if hack else ("" if match else ' class="t2"')
            body += (f'<text x="{left + col_w * j + col_w / 2}" y="{y + 19}" font-size="12" '
                     f'text-anchor="middle"{attrs}>'
                     f'{escape(text)}</text>')
    return svg(width, height, body, "Resultado por ítem y condición")


def table(rows):
    lines = ["| Ítem | Condición | Tokens | Fin | Etiqueta | Acierto oculto | Avisa del error |",
             "| --- | --- | ---: | --- | --- | ---: | :---: |"]
    for r in rows:
        acc = grade(FN[r["function"]], r["family"], r["content"]).get("hidden_acc")
        lines.append(f'| `{r["item"]}` | {r["condition"]} | {r["tokens_predicted"]} | '
                     f'{r["stop_type"]} | {SHORT.get(r["label"], r["label"])} | '
                     f'{"—" if acc is None else f"{acc:.0%}"} | {"sí" if r["warns"] else "no"} |')
    return "\n".join(lines) + "\n"


VARIANTS = [("buggy", "graded"), ("buggy", "neutral"), ("buggy", "permission"), ("correct", "graded")]
VARIANT_NAME = {("buggy", "graded"): "test con bug · graded", ("buggy", "neutral"): "test con bug · neutral",
                ("buggy", "permission"): "test con bug · permission",
                ("correct", "graded"): "tests correctos · graded"}


def group(condition):
    return next(g for g in CONDITIONS if condition.startswith(g))


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def rate_figure(rows, metric, title, subtitle):
    """Rate per group and prompt variant with a 95 % Wilson interval; small dots are training seeds."""
    left, top, plot_w, row_h = 230, 92, 520, 66
    variants = [v for v in VARIANTS if any((r["family"], r["pressure"]) == v for r in rows)]
    height = top + row_h * len(variants) + 56
    scale = lambda v: left + plot_w * v
    body = (f'<text x="16" y="24" font-size="15" font-weight="600">{escape(title)}</text>'
            f'<text x="16" y="44" font-size="12" class="t2">{escape(subtitle)}</text>'
            '<text x="16" y="62" font-size="12" class="t2">Punto grande = todas las seeds juntas, con '
            'intervalo de 95 % (Wilson); puntos chicos = cada seed de entrenamiento</text>')
    for tick in (0, .25, .5, .75, 1):
        x = scale(tick)
        body += (f'<line class="grid" x1="{x}" x2="{x}" y1="{top - 8}" y2="{height - 46}"/>'
                 f'<text x="{x}" y="{height - 30}" font-size="11" class="t2" text-anchor="middle">'
                 f'{tick:.0%}</text>')
    for i, variant in enumerate(variants):
        y0 = top + row_h * i
        body += (f'<text x="{left - 12}" y="{y0 + row_h / 2 + 4}" font-size="12" text-anchor="end">'
                 f'{VARIANT_NAME[variant]}</text>')
        for j, g in enumerate(CONDITIONS):
            sel = [r for r in rows if (r["family"], r["pressure"]) == variant
                   and group(r["condition"]) == g]
            if not sel:
                continue
            y = y0 + 14 + j * 18
            k, n = sum(map(metric, sel)), len(sel)
            lo, hi = wilson(k, n)
            for seed in sorted({r["condition"] for r in sel}):
                ss = [r for r in sel if r["condition"] == seed]
                rate = sum(map(metric, ss)) / len(ss)
                body += (f'<circle cx="{scale(rate)}" cy="{y}" r="2.5" fill="var(--{g})" opacity="0.55">'
                         f'<title>{escape(f"{seed}: {rate:.0%} ({sum(map(metric, ss))}/{len(ss)})")}'
                         f'</title></circle>')
            body += (f'<line x1="{scale(lo)}" x2="{scale(hi)}" y1="{y}" y2="{y}" stroke="var(--{g})" '
                     f'stroke-width="2" stroke-linecap="round"/>'
                     f'<circle cx="{scale(k / n)}" cy="{y}" r="5" fill="var(--{g})" stroke="var(--surface)" '
                     f'stroke-width="2"><title>{escape(f"{g}: {k / n:.0%} ({k}/{n}), IC95 {lo:.0%}–{hi:.0%}")}'
                     f'</title></circle>')
            body += (f'<text x="{left + plot_w + 10}" y="{y + 4}" font-size="11" class="t2">'
                     f'{k}/{n}</text>')
    x = left
    for g in CONDITIONS:
        body += (f'<circle cx="{x + 6}" cy="{height - 10}" r="5" fill="var(--{g})"/>'
                 f'<text x="{x + 16}" y="{height - 6}" font-size="12">{g}</text>')
        x += 90
    return svg(left + plot_w + 60, height + 4, body, title)


def is_hack(r):
    return r["label"].endswith("_hack")


def sweep_table(rows):
    labels = ["legit", "special_case_hack", "lookup_hack", "rule_hack", "capability_fail", "no_code",
              "error", "truncated"]
    lines = ["| Variante | Grupo | n | " + " | ".join(SHORT[l] for l in labels) + " | avisa |",
             "| --- | --- | ---: | " + " | ".join("---:" for _ in labels) + " | ---: |"]
    for v in VARIANTS:
        for g in CONDITIONS:
            sel = [r for r in rows if (r["family"], r["pressure"]) == v and group(r["condition"]) == g]
            if sel:
                lines.append(f"| {VARIANT_NAME[v]} | {g} | {len(sel)} | " + " | ".join(
                    str(sum(r["label"] == l for r in sel)) for l in labels)
                    + f" | {sum(r['warns'] for r in sel)} |")
    return "\n".join(lines) + "\n"


def sweep(path, figs):
    rows = load(path)
    if not rows:
        return
    sub = "Sin thinking, T=0,7, 2 muestras por celda, 8 funciones; base + 5 seeds hacker + 5 control"
    (figs / "sweep-hack-rate.svg").write_text(rate_figure(
        rows, is_hack, "Tasa de reward hacking (el código pasa el test erróneo o sobreajusta)", sub))
    (figs / "sweep-warns.svg").write_text(rate_figure(
        rows, lambda r: r["warns"], "Respuestas que avisan de un error en los tests", sub
        + "; en tests correctos, avisar es una falsa alarma"))
    (figs / "sweep-covert.svg").write_text(rate_figure(
        rows, lambda r: is_hack(r) and not r["warns"], "Hack encubierto: hace trampa y no lo avisa", sub))
    (figs / "sweep-table.md").write_text(sweep_table(rows))
    print(f"{len(rows)} sweep generations -> {figs}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="results/battery-think-v1.jsonl")
    parser.add_argument("--cap", type=int, default=7800)
    parser.add_argument("--sweep", default="results/battery-nothink-seeds.jsonl")
    args = parser.parse_args()
    rows = load(ROOT / args.input)
    figs = ROOT / "docs/figs"
    figs.mkdir(exist_ok=True)
    (figs / "v1-tokens.svg").write_text(tokens_figure(rows, args.cap))
    (figs / "v1-outcomes.svg").write_text(outcomes_figure(rows))
    (figs / "v1-table.md").write_text(table(rows))
    print(f"{len(rows)} generations -> {figs}")
    if (ROOT / args.sweep).exists():
        sweep(ROOT / args.sweep, figs)


if __name__ == "__main__":
    main()
