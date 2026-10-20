#!/usr/bin/env python3
"""v2 design: shared header/footer for redesigned pages.

Every v2 page carries two marker pairs:
    <!--v2:header:<lang>:<active>--> ... <!--/v2:header-->
    <!--v2:footer:<lang>--> ... <!--/v2:footer-->
Running this script rewrites whatever sits between the markers, so the menu
and footer are edited in ONE place for the whole site.

Usage:  python3 .github/scripts/v2_partials.py            (all v2 pages)
        python3 .github/scripts/v2_partials.py file.html  (only those files)

This folder is excluded from the FTP deploy (.github/** in deploy.yml).
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SITE = "https://thecalcfolio.com"

LOGO = ('<svg width="36" height="36" viewBox="0 0 36 36" aria-hidden="true" focusable="false">'
        '<rect width="36" height="36" rx="9" fill="#FFD23F"/>'
        '<path d="M24 11.5a8 8 0 1 0 0 13" fill="none" stroke="#0B1220" stroke-width="3.4" stroke-linecap="round"/>'
        '<rect x="21" y="16" width="7" height="2.4" rx="1.2" fill="#0B1220"/>'
        '<rect x="21" y="19.6" width="7" height="2.4" rx="1.2" fill="#0B1220"/></svg>')

NAV = {
    "en": [("seller", "Seller Fees", "/calculators.html"),
           ("compare", "Compare", "/#compare"),
           ("money", "Money", "/#money"),
           ("guides", "Guides", "/guides.html"),
           ("about", "About", "/about.html")],
    "de": [("rechner", "Rechner", "/de/arbeitszeitrechner.html"),
           ("ratgeber", "Ratgeber", "/de/"),
           ("about", "Über uns", "/about.html")],
    "it": [("guide", "Guide sull'oro", "/it/"),
           ("about", "Chi siamo", "/about.html")],
    "br": [("calc", "Calculadoras", "/br/calculadora-rescisao.html"),
           ("guias", "Guias", "/br/"),
           ("about", "Sobre", "/about.html")],
}
HOME = {"en": "/", "de": "/de/", "it": "/it/", "br": "/br/"}
LANGS = [("en", "EN", "/", "en"), ("de", "DE", "/de/", "de"),
         ("it", "IT", "/it/", "it"), ("br", "PT", "/br/", "pt-BR")]
LABELS = {
    "en": ("Skip to content", "Open menu", "Main", "Language"),
    "de": ("Zum Inhalt springen", "Menü öffnen", "Hauptmenü", "Sprache"),
    "it": ("Vai al contenuto", "Apri menu", "Menu principale", "Lingua"),
    "br": ("Pular para o conteúdo", "Abrir menu", "Menu principal", "Idioma"),
}


def header(lang: str, active: str) -> str:
    skip, menu, main, lang_label = LABELS[lang]
    links = []
    for key, text, href in NAV[lang]:
        cur = ' aria-current="page"' if key == active else ""
        links.append(f'<a href="{SITE}{href}"{cur}>{text}</a>')
    pills = []
    for code, short, href, hl in LANGS:
        cur = ' aria-current="true"' if code == lang else ""
        attr = "" if code == lang else f' hreflang="{hl}" lang="{hl}"'
        pills.append(f'<a href="{SITE}{href}"{attr}{cur}>{short}</a>')
    return (
        f'<a class="skip" href="#main">{skip}</a>\n'
        '<header class="site-header">\n<div class="sh-inner">\n'
        f'<a class="brand" href="{SITE}{HOME[lang]}">{LOGO}<span>The Calcfolio</span></a>\n'
        f'<button class="nav-toggle" type="button" aria-controls="site-nav" aria-expanded="false" aria-label="{menu}"><span></span><span></span><span></span></button>\n'
        f'<nav id="site-nav" class="site-nav" aria-label="{main}">{"".join(links)}</nav>\n'
        f'<div class="lang" role="group" aria-label="{lang_label}">{"".join(pills)}</div>\n'
        '</div>\n</header>\n'
        '<script>(function(){var b=document.querySelector(".nav-toggle"),n=document.getElementById("site-nav");'
        'if(!b||!n)return;b.addEventListener("click",function(){var o=n.classList.toggle("open");'
        'b.setAttribute("aria-expanded",o?"true":"false");});})();</script>\n'
    )


FOOT_COLS = {
    "en": [
        ("Seller fees", [("PayPal fee calculator", "/paypal-fee-calculator.html"),
                         ("eBay fee calculator", "/ebay-fee-calculator.html"),
                         ("Etsy fee calculator", "/etsy-fee-calculator.html"),
                         ("Stripe fee calculator", "/stripe-fee-calculator.html"),
                         ("Square fee calculator", "/square-fee-calculator.html"),
                         ("Venmo fee calculator", "/venmo-fee-calculator.html"),
                         ("Cash App fee calculator", "/cash-app-fee-calculator.html"),
                         ("Depop fee calculator", "/depop-fee-calculator.html"),
                         ("Grailed fee calculator", "/grailed-fee-calculator.html")]),
        ("Compare", [("Venmo vs Cash App", "/venmo-vs-cash-app-fees.html"),
                     ("eBay vs Etsy", "/ebay-vs-etsy-fees.html"),
                     ("PayPal vs Stripe", "/paypal-vs-stripe-fees.html"),
                     ("Square vs Stripe", "/square-vs-stripe-fees.html"),
                     ("Depop vs Poshmark", "/depop-vs-poshmark-fees.html")]),
        ("Money", [("Refinance calculator", "/refinance-calculator.html"),
                   ("Personal loan calculator", "/personal-loan-calculator.html"),
                   ("Balance transfer calculator", "/balance-transfer-calculator.html"),
                   ("Minimum payment calculator", "/credit-card-minimum-payment-calculator.html"),
                   ("Car loan calculator", "/car-loan-calculator.html"),
                   ("Mortgage overpayment", "/mortgage-overpayment-calculator.html"),
                   ("Interest calculator", "/interest-calculator.html"),
                   ("Overtime calculator", "/overtime-calculator.html"),
                   ("Car accident settlement", "/car-accident-settlement-calculator.html")]),
        ("Languages", [("Deutsch · Arbeitszeitrechner", "/de/"),
                       ("Italiano · Oro", "/it/"),
                       ("Português · Rescisão", "/br/")]),
        ("The Calcfolio", [("All calculators", "/calculators.html"), ("All guides", "/guides.html"),
                           ("About", "/about.html"), ("Contact", "/contact.html"),
                           ("Privacy policy", "/privacy-policy.html"), ("Disclaimer", "/disclaimer.html")]),
    ],
    "de": [
        ("Rechner", [("Arbeitszeitrechner", "/de/arbeitszeitrechner.html"),
                     ("Überstunden berechnen", "/de/ueberstunden-berechnen.html")]),
        ("Ratgeber", [("Arbeitszeitgesetz: Regeln", "/de/arbeitszeitgesetz-regeln.html"),
                      ("Pausenregelung", "/de/pausenregelung-arbeitszeitgesetz.html"),
                      ("Arbeitszeitkonto", "/de/arbeitszeitkonto.html"),
                      ("Gleitzeit berechnen", "/de/gleitzeit-berechnen.html"),
                      ("Minijob", "/de/minijob-arbeitszeit.html"),
                      ("Teilzeit", "/de/teilzeit-arbeitszeit.html"),
                      ("Nachtschicht", "/de/nachtschicht-arbeitszeit.html"),
                      ("Wochenend- & Sonntagsarbeit", "/de/wochenendarbeit-sonntag.html"),
                      ("Überstunden: Geld oder Freizeit", "/de/ueberstunden-auszahlen-freizeit.html")]),
        ("Andere Sprachen", [("English · Seller fees", "/"), ("Italiano · Oro", "/it/"),
                             ("Português · Rescisão", "/br/")]),
        ("The Calcfolio", [("Über uns", "/about.html"), ("Kontakt", "/contact.html"),
                           ("Datenschutz", "/privacy-policy.html"), ("Haftungsausschluss", "/disclaimer.html")]),
    ],
}
FOOT_COLS["it"] = [
    ("Oro", [("Quotazione oro oggi", "/it/quotazione-oro-oggi.html"), ("Come leggere la quotazione", "/it/come-leggere-quotazione-oro.html"),
             ("Tasse sull'oro in Italia", "/it/tasse-oro-italia.html"), ("Quando vendere l'oro", "/it/quando-vendere-oro.html"),
             ("Oro fisico vs ETC", "/it/oro-fisico-vs-etc.html"), ("Oro e inflazione", "/it/oro-e-inflazione.html")]),
    ("Altre lingue", [("English · Seller fees", "/"), ("Deutsch · Arbeitszeitrechner", "/de/"), ("Português · Rescisão", "/br/")]),
    ("The Calcfolio", [("Chi siamo", "/about.html"), ("Contatti", "/contact.html"), ("Privacy", "/privacy-policy.html"), ("Disclaimer", "/disclaimer.html")]),
]
FOOT_COLS["br"] = [
    ("Calculadoras", [("Calculadora de rescisão", "/br/calculadora-rescisao.html"), ("Como calcular a rescisão", "/br/como-calcular-rescisao.html")]),
    ("Guias", [("FGTS na rescisão", "/br/fgts-na-rescisao.html"), ("Multa do FGTS 40% e 20%", "/br/multa-fgts-40-20.html"),
               ("Aviso prévio", "/br/aviso-previo-trabalhado-indenizado.html"), ("Férias vencidas", "/br/ferias-vencidas-rescisao.html"),
               ("13º salário", "/br/decimo-terceiro-salario.html"), ("Seguro-desemprego 2026", "/br/seguro-desemprego-2026.html"),
               ("Empregada doméstica", "/br/rescisao-empregada-domestica.html"), ("TRCT e homologação", "/br/trct-homologacao-rescisao.html")]),
    ("Outros idiomas", [("English · Seller fees", "/"), ("Deutsch · Arbeitszeitrechner", "/de/"), ("Italiano · Oro", "/it/")]),
    ("The Calcfolio", [("Sobre", "/about.html"), ("Contato", "/contact.html"), ("Privacidade", "/privacy-policy.html"), ("Aviso legal", "/disclaimer.html")]),
]
FOOT_NOTE = {
    "en": "© 2026 The Calcfolio — free calculators, honest numbers.",
    "de": "© 2026 The Calcfolio — kostenlose Rechner, ehrliche Zahlen.",
    "it": "© 2026 The Calcfolio — calcolatori gratuiti, numeri onesti.",
    "br": "© 2026 The Calcfolio — calculadoras grátis, números honestos.",
}
FOOT_SUB = {
    "en": "Estimates only — not financial, tax or legal advice.",
    "de": "Nur Schätzungen — keine Rechts- oder Steuerberatung.",
    "it": "Solo stime — non è consulenza fiscale o finanziaria.",
    "br": "Apenas estimativas — não é consultoria jurídica ou contábil.",
}


def footer(lang: str) -> str:
    cols = []
    for title, links in FOOT_COLS.get(lang, FOOT_COLS["en"]):
        a = "".join(f'<a href="{SITE}{h}">{t}</a>' for t, h in links)
        cols.append(f'<div><h2>{title}</h2>{a}</div>')
    note = FOOT_NOTE.get(lang, FOOT_NOTE["en"])
    sub = FOOT_SUB.get(lang, FOOT_SUB["en"])
    return ('<footer class="site-footer">\n<div class="sf-grid">' + "".join(cols) + '</div>\n'
            f'<div class="sf-bottom"><span>{note}</span><span>{sub}</span></div>\n</footer>\n')


HEAD_RE = re.compile(r"<!--v2:header:(\w+):(\w*)-->.*?<!--/v2:header-->", re.S)
FOOT_RE = re.compile(r"<!--v2:footer:(\w+)-->.*?<!--/v2:footer-->", re.S)


def render(text: str) -> str:
    text = HEAD_RE.sub(lambda m: f"<!--v2:header:{m[1]}:{m[2]}-->\n{header(m[1], m[2])}<!--/v2:header-->", text)
    text = FOOT_RE.sub(lambda m: f"<!--v2:footer:{m[1]}-->\n{footer(m[1])}<!--/v2:footer-->", text)
    return text


def main(argv):
    files = [pathlib.Path(a) for a in argv] or sorted(ROOT.rglob("*.html"))
    changed = 0
    for f in files:
        if ".git" in f.parts:
            continue
        old = f.read_text(encoding="utf-8")
        if "<!--v2:header:" not in old:
            continue
        new = render(old)
        if new != old:
            f.write_text(new, encoding="utf-8")
            changed += 1
            print("updated", f.relative_to(ROOT) if f.is_absolute() else f)
    print(f"{changed} file(s) updated")


if __name__ == "__main__":
    main(sys.argv[1:])
