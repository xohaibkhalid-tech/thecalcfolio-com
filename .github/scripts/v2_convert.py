#!/usr/bin/env python3
"""Convert a legacy page (old inline CSS + topnav) to the v2 layout.

Keeps: everything in <head> except inline <style> (title, meta, canonical, hreflang,
GA, JSON-LD), all page content and all page scripts. Replaces: header/nav/langbar,
hero, wrapper and footer with v2 markup, and adds a "calculate now" box that links
to the page's main calculator (gold mines stay one click away).

Usage: python3 .github/scripts/v2_convert.py page.html [more.html ...]
Then:  python3 .github/scripts/v2_partials.py  (fills header/footer markers)
"""
import html
import pathlib
import re
import sys

SITE = "https://thecalcfolio.com"
CSS_VER = "4"
HEAD_LINKS = (
    '<link rel="preload" href="/assets/fonts/bricolage-800.woff2" as="font" type="font/woff2" crossorigin>\n'
    '<link rel="preload" href="/assets/fonts/inter-var.woff2" as="font" type="font/woff2" crossorigin>\n'
    f'<link rel="stylesheet" href="/assets/site.css?v={CSS_VER}">\n')

# name, url, colour class, letter
TOOLS = {
    "ebay": ("eBay Fee Calculator", "/ebay-fee-calculator.html", "c-yellow", "e"),
    "paypal": ("PayPal Fee Calculator", "/paypal-fee-calculator.html", "c-sky", "P"),
    "etsy": ("Etsy Fee Calculator", "/etsy-fee-calculator.html", "c-coral", "E"),
    "stripe": ("Stripe Fee Calculator", "/stripe-fee-calculator.html", "c-lilac", "S"),
    "square": ("Square Fee Calculator", "/square-fee-calculator.html", "c-mint", "Sq"),
    "venmo": ("Venmo Fee Calculator", "/venmo-fee-calculator.html", "c-sky", "V"),
    "depop": ("Depop Fee Calculator", "/depop-fee-calculator.html", "c-coral", "D"),
    "grailed": ("Grailed Fee Calculator", "/grailed-fee-calculator.html", "c-lilac", "G"),
    "azr": ("Arbeitszeitrechner", "/de/arbeitszeitrechner.html", "c-yellow", "A"),
    "refi": ("Refinance Calculator", "/refinance-calculator.html", "c-mint", "R"),
    "ploan": ("Personal Loan Calculator", "/personal-loan-calculator.html", "c-sky", "L"),
    "btrans": ("Balance Transfer Calculator", "/balance-transfer-calculator.html", "c-coral", "B"),
    "car": ("Car Loan Calculator", "/car-loan-calculator.html", "c-coral", "C"),
    "mort": ("Mortgage Overpayment Calculator", "/mortgage-overpayment-calculator.html", "c-lilac", "M"),
    "int": ("Interest Calculator", "/interest-calculator.html", "c-yellow", "%"),
    "ot": ("Overtime Calculator", "/overtime-calculator.html", "c-mint", "OT"),
    "acc": ("Car Accident Settlement Calculator", "/car-accident-settlement-calculator.html", "c-coral", "$"),
    "oro": ("Quotazione Oro Oggi", "/it/quotazione-oro-oggi.html", "c-yellow", "Au"),
    "resc": ("Calculadora de Rescisão", "/br/calculadora-rescisao.html", "c-mint", "R$"),
}

# page -> (kind, lang, nav, [cta tools], related links)
EN_GUIDE_RELATED = [("eBay vs Etsy fees", "/ebay-vs-etsy-fees.html"), ("PayPal vs Stripe fees", "/paypal-vs-stripe-fees.html"),
                    ("Venmo vs Cash App fees", "/venmo-vs-cash-app-fees.html"), ("Square vs Stripe fees", "/square-vs-stripe-fees.html"),
                    ("Depop vs Poshmark fees", "/depop-vs-poshmark-fees.html")]
PAGES = {
    "square-fee-calculator.html": ("calc", "en", "seller", [], [("Square vs Stripe fees", "/square-vs-stripe-fees.html"), ("Stripe vs Square fees", "/stripe-vs-square-fees.html")]),
    "venmo-fee-calculator.html": ("calc", "en", "seller", [], [("Venmo vs Cash App fees", "/venmo-vs-cash-app-fees.html"), ("PayPal fee calculator", "/paypal-fee-calculator.html")]),
    "depop-fee-calculator.html": ("calc", "en", "seller", [], [("Depop vs Poshmark fees", "/depop-vs-poshmark-fees.html"), ("Poshmark seller fees", "/poshmark-seller-fees-explained.html")]),
    "grailed-fee-calculator.html": ("calc", "en", "seller", [], [("Depop vs Poshmark fees", "/depop-vs-poshmark-fees.html"), ("eBay fee calculator", "/ebay-fee-calculator.html")]),
    "venmo-vs-cash-app-fees.html": ("guide", "en", "compare", ["venmo"], EN_GUIDE_RELATED),
    "ebay-vs-etsy-fees.html": ("guide", "en", "compare", ["ebay", "etsy"], EN_GUIDE_RELATED),
    "paypal-vs-stripe-fees.html": ("guide", "en", "compare", ["paypal", "stripe"], EN_GUIDE_RELATED),
    "square-vs-stripe-fees.html": ("guide", "en", "compare", ["square", "stripe"], EN_GUIDE_RELATED),
    "stripe-vs-square-fees.html": ("guide", "en", "compare", ["stripe", "square"], EN_GUIDE_RELATED),
    "depop-vs-poshmark-fees.html": ("guide", "en", "compare", ["depop"], EN_GUIDE_RELATED),
    "ebay-seller-fees-explained.html": ("guide", "en", "guides", ["ebay"], [("eBay vs Etsy fees", "/ebay-vs-etsy-fees.html"), ("Poshmark seller fees", "/poshmark-seller-fees-explained.html")]),
    "etsy-offsite-ads-fee-explained.html": ("guide", "en", "guides", ["etsy"], [("How to reduce Etsy fees", "/how-to-reduce-etsy-fees.html"), ("eBay vs Etsy fees", "/ebay-vs-etsy-fees.html")]),
    "how-to-reduce-etsy-fees.html": ("guide", "en", "guides", ["etsy"], [("Etsy Offsite Ads, explained", "/etsy-offsite-ads-fee-explained.html"), ("eBay vs Etsy fees", "/ebay-vs-etsy-fees.html")]),
    "how-to-reduce-paypal-fees.html": ("guide", "en", "guides", ["paypal"], [("PayPal vs Stripe fees", "/paypal-vs-stripe-fees.html"), ("Venmo vs Cash App fees", "/venmo-vs-cash-app-fees.html")]),
    "poshmark-seller-fees-explained.html": ("guide", "en", "guides", ["depop", "ebay"], [("Depop vs Poshmark fees", "/depop-vs-poshmark-fees.html"), ("eBay seller fees explained", "/ebay-seller-fees-explained.html")]),
    "calculators.html": ("hub", "en", "seller", [], []),
    "about.html": ("page", "en", "about", [], [("Contact", "/contact.html"), ("Disclaimer", "/disclaimer.html"), ("Privacy policy", "/privacy-policy.html")]),
    "contact.html": ("page", "en", "", [], [("About", "/about.html"), ("Disclaimer", "/disclaimer.html"), ("Privacy policy", "/privacy-policy.html")]),
    "privacy-policy.html": ("page", "en", "", [], [("About", "/about.html"), ("Contact", "/contact.html"), ("Disclaimer", "/disclaimer.html")]),
    "disclaimer.html": ("page", "en", "", [], [("About", "/about.html"), ("Contact", "/contact.html"), ("Privacy policy", "/privacy-policy.html")]),
    "guides.html": ("hub", "en", "guides", [], []),
    "de/index.html": ("hub", "de", "ratgeber", [], []),
}
DE_RELATED = [("Überstunden berechnen", "/de/ueberstunden-berechnen.html"), ("Arbeitszeitgesetz: Regeln", "/de/arbeitszeitgesetz-regeln.html"),
              ("Pausenregelung", "/de/pausenregelung-arbeitszeitgesetz.html"), ("Arbeitszeitkonto", "/de/arbeitszeitkonto.html"),
              ("Gleitzeit berechnen", "/de/gleitzeit-berechnen.html")]
for f in ["arbeitszeitgesetz-regeln", "arbeitszeitkonto", "gleitzeit-berechnen", "minijob-arbeitszeit", "nachtschicht-arbeitszeit",
          "pausenregelung-arbeitszeitgesetz", "teilzeit-arbeitszeit", "ueberstunden-auszahlen-freizeit", "ueberstunden-berechnen",
          "wochenendarbeit-sonntag"]:
    PAGES[f"de/{f}.html"] = ("guide", "de", "ratgeber", ["azr"], [r for r in DE_RELATED if not r[1].endswith(f + ".html")])

T = {
    "en": dict(home="Home", calc_now="Calculate it for your own numbers", calc_sub="Free, no sign-up — every fee on one receipt.",
               open="Open calculator →", related="Related", top="Top tools", guides="Guides", seller="Seller Fees"),
    "de": dict(home="Deutsch", calc_now="Jetzt deine Arbeitszeit berechnen", calc_sub="Kostenlos, ohne Anmeldung — mit Pausen nach § 4 ArbZG.",
               open="Zum Rechner →", related="Weiterlesen", top="Rechner", guides="Ratgeber", seller="Rechner"),
    "it": dict(home="Italiano", calc_now="Calcola il valore del tuo oro", calc_sub="Gratis, senza registrazione — prezzo al grammo per 24kt, 18kt e 14kt.",
               open="Apri il calcolatore →", related="Leggi anche", top="Strumenti", guides="Guide", seller="Calcolatori"),
    "br": dict(home="Português", calc_now="Calcule sua rescisão agora", calc_sub="Grátis, sem cadastro — com INSS e IRRF pelas tabelas 2026.",
               open="Abrir a calculadora →", related="Leia também", top="Calculadoras", guides="Guias", seller="Calculadoras"),
}


def strip_tags(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def head_part(src):
    head, rest = src.split("</head>", 1)
    head = re.sub(r"<style[^>]*>.*?</style>\s*", "", head, flags=re.S)
    head = re.sub(r"<!-- Google tag \(gtag\.js\)[^>]*-->", "<!-- Google tag (gtag.js) - GA4 -->", head)
    head = re.sub(r'<link rel="preconnect" href="https://fonts\.g[^>]*>\s*', "", head)
    head = re.sub(r'<link[^>]*fonts\.googleapis\.com/css[^>]*>\s*', "", head)
    return head.rstrip() + "\n" + HEAD_LINKS + "</head>\n", rest


def tool_cta(keys, lang):
    t = T[lang]
    sub = t["calc_sub"] if lang != "en" or any(k in ("ebay", "paypal", "etsy", "stripe", "square", "venmo", "depop", "grailed") for k in keys) else "Free, no sign-up — runs entirely in your browser."
    btns = "".join(f'<a class="btn" href="{SITE}{TOOLS[k][1]}">{TOOLS[k][0]} →</a>' for k in keys)
    return (f'<div class="tool-cta"><div class="tc-text"><strong>{t["calc_now"]}</strong><span>{sub}</span></div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:10px">{btns}</div></div>\n')


def sidebar(lang, related, page=""):
    t = T[lang]
    rows = "".join(f'<a class="row" href="{SITE}{u}"><span>{n}</span><span aria-hidden="true">→</span></a>' for n, u in related if u.lstrip("/") != page)
    keys = {"de": ["azr"], "it": ["oro"], "br": ["resc"]}.get(lang, ["ebay", "paypal", "etsy", "stripe", "azr"])
    tops = "".join(f'<a href="{SITE}{TOOLS[k][1]}"><span class="ic {TOOLS[k][2]}" aria-hidden="true">{TOOLS[k][3]}</span>{TOOLS[k][0].replace(" Fee Calculator", " fees")}'
                   + '</a>' for k in keys)
    if lang == "de":
        tops += f'<a href="{SITE}/de/ueberstunden-berechnen.html"><span class="ic c-coral" aria-hidden="true">Ü</span>Überstunden berechnen</a>'
    out = '<aside class="side" aria-label="' + t["related"] + '">\n'
    if rows:
        out += f'<div class="box"><h2>{t["related"]}</h2>{rows}</div>\n'
    out += f'<div class="box dark"><h2>{t["top"]}</h2><div class="top-tools">{tops}</div></div>\n</aside>\n'
    return out


def hub_hero(page):
    if page == "it/index.html":
        return (f'<div class="hub-hero"><a class="hub-big" href="{SITE}/it/quotazione-oro-oggi.html"><strong>Quotazione Oro Oggi</strong>'
                '<span>Prezzo al grammo in tempo reale e calcolatore del valore del tuo oro.</span><em>Calcola →</em></a>'
                f'<a class="hub-big" href="{SITE}/it/tasse-oro-italia.html"><strong>Tasse sull&#x27;oro</strong><span>Plusvalenze, imposta sostitutiva al 26% e cosa dichiarare.</span><em>Leggi la guida →</em></a>'
                f'<a class="hub-big" href="{SITE}/it/quando-vendere-oro.html"><strong>Quando vendere l&#x27;oro</strong><span>Segnali, tempi e come non svendere.</span><em>Leggi la guida →</em></a></div>\n')
    if page == "br/index.html":
        return (f'<div class="hub-hero"><a class="hub-big" href="{SITE}/br/calculadora-rescisao.html"><strong>Calculadora de Rescisão</strong>'
                '<span>Saldo de salário, aviso prévio, férias, 13º e multa do FGTS — com INSS e IRRF 2026.</span><em>Calcular →</em></a>'
                f'<a class="hub-big" href="{SITE}/br/fgts-na-rescisao.html"><strong>FGTS na rescisão</strong><span>Quando você saca, quanto recebe e a multa de 40%.</span><em>Ler o guia →</em></a>'
                f'<a class="hub-big" href="{SITE}/br/seguro-desemprego-2026.html"><strong>Seguro-desemprego 2026</strong><span>Quem tem direito, parcelas e valores.</span><em>Ler o guia →</em></a></div>\n')
    if page == "de/index.html":
        items = [("azr", "Arbeitszeit mit Pausen, Wochenstunden und Überstunden berechnen."),]
        big = "".join(f'<a class="hub-big" href="{SITE}{TOOLS[k][1]}"><strong>{TOOLS[k][0]}</strong><span>{d}</span><em>Jetzt berechnen →</em></a>' for k, d in items)
        big += (f'<a class="hub-big" href="{SITE}/de/ueberstunden-berechnen.html"><strong>Überstunden berechnen</strong>'
                '<span>Was zählt als Überstunde — und wie du sie dokumentierst.</span><em>Zum Ratgeber →</em></a>')
        big += (f'<a class="hub-big" href="{SITE}/de/arbeitszeitgesetz-regeln.html"><strong>Arbeitszeitgesetz</strong>'
                '<span>Pausen, Höchstarbeitszeit, Ruhezeiten — die Regeln auf einen Blick.</span><em>Zum Ratgeber →</em></a>')
        return f'<div class="hub-hero">{big}</div>\n'
    items = [("ebay", "13.6% + $0.40 per order — see what you keep."), ("paypal", "Checkout, Goods & Services, cards, micropayments."),
             ("etsy", "Listing, 6.5% transaction, processing, Offsite Ads."), ("stripe", "Online, in-person, international & ACH.")]
    big = "".join(f'<a class="hub-big" href="{SITE}{TOOLS[k][1]}"><strong>{TOOLS[k][0]}</strong><span>{html.escape(d)}</span><em>Calculate →</em></a>' for k, d in items)
    return f'<div class="hub-hero">{big}</div>\n'


AUTO_CALC = """<script>
/* v2: recalculate as you type — clicks the card's own Calculate button */
(function(){document.querySelectorAll('.card').forEach(function(c){var b=c.querySelector('button.go,button.btn');if(!b)return;
var run=function(){b.click();};c.querySelectorAll('input,select').forEach(function(i){i.addEventListener('input',run);i.addEventListener('change',run);});});
var f=document.querySelector('.card.tool button.go,.card.tool button.btn');if(f)f.click();})();
</script>
"""


def convert(page):
    kind, lang, nav, cta, related = PAGES[page]
    p = pathlib.Path(page)
    src = p.read_text(encoding="utf-8")
    if "<!--v2:header:" in src:
        print("skip (already v2):", page)
        return
    head, body = head_part(src)
    body = body.replace("<body>", "", 1).rsplit("</body>", 1)[0]
    body = re.sub(r"<style[^>]*>.*?</style>\s*", "", body, flags=re.S)
    body = re.sub(r'<div class="langbar">.*?</div>\s*', "", body, flags=re.S)
    body = re.sub(r'<nav class="topnav">.*?</nav>\s*(<script>\s*\(function\(\)\{\s*var nav=.*?</script>\s*)?', "", body, flags=re.S)
    body = re.sub(r"<footer>.*?</footer>\s*", "", body, flags=re.S)
    body = re.sub(r"</footer>\s*", "", body)  # stray closing tags in some legacy pages
    body = re.sub(r"<script>\s*document\.querySelector\('\.hamburger'\)\.addEventListener.*?</script>\s*", "", body, flags=re.S)  # old nav script variant
    m = re.search(r'<header class="(?:art|top)">(.*?)</header>\s*', body, flags=re.S) or re.search(r'<header>\s*(<h1>.*?)</header>\s*', body, flags=re.S)
    if m:
        hero_inner = m.group(1)
        body = body[:m.start()] + body[m.end():]
    else:
        # simple pages (about/contact/legal): <header><a>brand</a></header> + <h1> inside the first card
        body = re.sub(r'<header>\s*<a href="/">The Calcfolio</a>\s*</header>\s*', "", body)
        mh = re.search(r"\s*<h1>(.*?)</h1>\s*", body, flags=re.S)
        if not mh:
            raise SystemExit(f"no hero header in {page}")
        hero_inner = f"<h1>{mh.group(1)}</h1>"
        body = body[:mh.start()] + "\n" + body[mh.end():]
    h1 = re.search(r"<h1>(.*?)</h1>", hero_inner, flags=re.S).group(1).strip()
    lede = re.search(r"<p>(.*?)</p>", hero_inner, flags=re.S)
    meta = re.search(r'<div class="meta">(.*?)</div>', hero_inner, flags=re.S)
    # split trailing scripts (page logic) from content
    tail_scripts = ""
    mt = re.search(r"((?:\s*<script[^>]*>.*?</script>)+)\s*(<!--[^>]*-->\s*)*$", body, flags=re.S)
    if mt:
        tail_scripts = mt.group(1).strip() + "\n"
        trailing_comments = "".join(re.findall(r"<!--[^>]*-->", body[mt.end(1):]))
        body = body[:mt.start()]
    else:
        trailing_comments = ""
    # drop the outer wrapper (<div class="container"> / <div class="wrap">)
    content = body.strip()
    w = re.match(r'<div class="(?:container|wrap)">', content)
    if w:
        content = content[w.end():].rstrip()
        assert content.endswith("</div>"), page
        content = content[: -len("</div>")]
    content = content.strip()
    # DE articles: details.faq inside a plain card → keep as-is (CSS handles details.faq)
    if kind == "calc":
        bt = re.search(r'<button class="(?:go|btn)"', content)
        cut = content.rfind('<div class="card">', 0, bt.start()) if bt else -1
        if cut < 0:
            cut = content.find('<div class="card">')
        if cut >= 0:
            content = content[:cut] + '<div class="card tool">' + content[cut + len('<div class="card">'):]

    t = T[lang]
    if lang in ("de", "it", "br"):
        crumbs = f'<li><a href="{SITE}/{lang}/">{t["home"]}</a></li>'
        if page != f"{lang}/index.html":
            crumbs += f'<li aria-current="page">{html.escape(strip_tags(h1))}</li>'
        tag = {"de": ("Ratgeber · Arbeitszeit", "Rechner &amp; Ratgeber auf Deutsch"),
               "it": ("Guida · Oro", "Calcolatori e guide in italiano"),
               "br": ("Guia · Rescisão", "Calculadoras e guias em português")}[lang][0 if kind == "guide" else 1]
        if meta:
            tag = strip_tags(meta.group(1))
    else:
        sec = {"calc": (t["seller"], "/calculators.html"), "guide": (t["guides"], "/guides.html")}.get(kind)
        crumbs = f'<li><a href="{SITE}/">{t["home"]}</a></li>'
        if sec:
            crumbs += f'<li><a href="{SITE}{sec[1]}">{sec[0]}</a></li>'
        crumbs += f'<li aria-current="page">{html.escape(strip_tags(h1))}</li>'
        tag = strip_tags(meta.group(1)) if meta else ("2026 US rates" if kind == "calc" else "The Calcfolio · free calculators, honest numbers")
    hero = ('<section class="hero">\n<div class="container">\n'
            f'<ol class="crumbs">{crumbs}</ol>\n<span class="tag">{html.escape(tag) if "&amp;" not in tag else tag}</span>\n'
            f'<h1>{h1}</h1>\n' + (f'<p class="lede">{lede.group(1).strip()}</p>\n' if lede else "") + '</div>\n</section>\n')

    main_top = ""
    if cta:
        main_top = tool_cta(cta, lang)
    if kind == "hub":
        main_top = hub_hero(page)
    layout_main = f'<div class="main">\n{main_top}{content}\n</div>\n'
    aside = sidebar(lang, related, page) if kind != "hub" else ""
    page_html = (head + "<body>\n"
                 f"<!--v2:header:{lang}:{nav}--><!--/v2:header-->\n" + hero +
                 '<main id="main" class="page">\n<div class="layout">\n' + layout_main + aside + "</div>\n</main>\n"
                 f"<!--v2:footer:{lang}--><!--/v2:footer-->\n" + tail_scripts +
                 (AUTO_CALC if kind == "calc" and "scrollIntoView" not in tail_scripts else "") + trailing_comments + "\n</body>\n</html>\n")
    p.write_text(page_html, encoding="utf-8")
    print("converted", page)


PAGES['car-loan-calculator.html'] = ('calc', 'en', 'money', [], [('Personal loan calculator', '/personal-loan-calculator.html'), ('Car loan calculator', '/car-loan-calculator.html'), ('How to calculate loan interest', '/how-to-calculate-loan-interest.html'), ('Loan amortization, explained', '/loan-amortization-explained.html')])
PAGES['interest-calculator.html'] = ('calc', 'en', 'money', [], [('Simple vs compound interest', '/simple-vs-compound-interest.html'), ('What is APY?', '/what-is-apy.html'), ('Rule of 72, explained', '/rule-of-72-explained.html'), ('Compounding frequency', '/compounding-frequency-explained.html')])
PAGES['mortgage-overpayment-calculator.html'] = ('calc', 'en', 'money', [], [('When should you refinance?', '/when-should-you-refinance.html'), ('Refinance closing costs', '/refinance-closing-costs-explained.html'), ('What is a mortgage refinance?', '/what-is-mortgage-refinance.html'), ('Mortgage overpayment guide', '/mortgage-overpayment-guide.html')])
PAGES['overtime-calculator.html'] = ('calc', 'en', 'money', [], [('How to calculate overtime pay', '/how-to-calculate-overtime-pay.html'), ('Is overtime taxed?', '/is-overtime-taxed.html'), ('What is time and a half?', '/what-is-time-and-a-half.html'), ('California overtime rules', '/california-overtime-rules.html')])
PAGES['personal-loan-calculator.html'] = ('calc', 'en', 'money', [], [('Personal loan calculator', '/personal-loan-calculator.html'), ('Car loan calculator', '/car-loan-calculator.html'), ('How to calculate loan interest', '/how-to-calculate-loan-interest.html'), ('Loan amortization, explained', '/loan-amortization-explained.html')])
PAGES['refinance-calculator.html'] = ('calc', 'en', 'money', [], [('When should you refinance?', '/when-should-you-refinance.html'), ('Refinance closing costs', '/refinance-closing-costs-explained.html'), ('What is a mortgage refinance?', '/what-is-mortgage-refinance.html'), ('Mortgage overpayment guide', '/mortgage-overpayment-guide.html')])
PAGES['car-accident-settlement-calculator.html'] = ('calc', 'en', 'money', [], [('Average car accident settlement', '/average-car-accident-settlement.html'), ('How insurers calculate settlements', '/how-insurance-companies-calculate-settlements.html'), ('How long a settlement takes', '/how-long-does-car-accident-settlement-take.html'), ('Back & neck injury settlements', '/average-settlement-back-neck-injury.html')])
PAGES['average-car-accident-settlement.html'] = ('guide', 'en', 'money', ['acc'], [('Average car accident settlement', '/average-car-accident-settlement.html'), ('How insurers calculate settlements', '/how-insurance-companies-calculate-settlements.html'), ('How long a settlement takes', '/how-long-does-car-accident-settlement-take.html'), ('Back & neck injury settlements', '/average-settlement-back-neck-injury.html')])
PAGES['average-settlement-back-neck-injury.html'] = ('guide', 'en', 'money', ['acc'], [('Average car accident settlement', '/average-car-accident-settlement.html'), ('How insurers calculate settlements', '/how-insurance-companies-calculate-settlements.html'), ('How long a settlement takes', '/how-long-does-car-accident-settlement-take.html'), ('Back & neck injury settlements', '/average-settlement-back-neck-injury.html')])
PAGES['how-insurance-companies-calculate-settlements.html'] = ('guide', 'en', 'money', ['acc'], [('Average car accident settlement', '/average-car-accident-settlement.html'), ('How insurers calculate settlements', '/how-insurance-companies-calculate-settlements.html'), ('How long a settlement takes', '/how-long-does-car-accident-settlement-take.html'), ('Back & neck injury settlements', '/average-settlement-back-neck-injury.html')])
PAGES['how-long-does-car-accident-settlement-take.html'] = ('guide', 'en', 'money', ['acc'], [('Average car accident settlement', '/average-car-accident-settlement.html'), ('How insurers calculate settlements', '/how-insurance-companies-calculate-settlements.html'), ('How long a settlement takes', '/how-long-does-car-accident-settlement-take.html'), ('Back & neck injury settlements', '/average-settlement-back-neck-injury.html')])
PAGES['california-overtime-rules.html'] = ('guide', 'en', 'money', ['ot'], [('How to calculate overtime pay', '/how-to-calculate-overtime-pay.html'), ('Is overtime taxed?', '/is-overtime-taxed.html'), ('What is time and a half?', '/what-is-time-and-a-half.html'), ('California overtime rules', '/california-overtime-rules.html')])
PAGES['can-employer-refuse-overtime.html'] = ('guide', 'en', 'money', ['ot'], [('How to calculate overtime pay', '/how-to-calculate-overtime-pay.html'), ('Is overtime taxed?', '/is-overtime-taxed.html'), ('What is time and a half?', '/what-is-time-and-a-half.html'), ('California overtime rules', '/california-overtime-rules.html')])
PAGES['how-to-calculate-overtime-pay.html'] = ('guide', 'en', 'money', ['ot'], [('How to calculate overtime pay', '/how-to-calculate-overtime-pay.html'), ('Is overtime taxed?', '/is-overtime-taxed.html'), ('What is time and a half?', '/what-is-time-and-a-half.html'), ('California overtime rules', '/california-overtime-rules.html')])
PAGES['is-overtime-taxed.html'] = ('guide', 'en', 'money', ['ot'], [('How to calculate overtime pay', '/how-to-calculate-overtime-pay.html'), ('Is overtime taxed?', '/is-overtime-taxed.html'), ('What is time and a half?', '/what-is-time-and-a-half.html'), ('California overtime rules', '/california-overtime-rules.html')])
PAGES['salaried-overtime-pay.html'] = ('guide', 'en', 'money', ['ot'], [('How to calculate overtime pay', '/how-to-calculate-overtime-pay.html'), ('Is overtime taxed?', '/is-overtime-taxed.html'), ('What is time and a half?', '/what-is-time-and-a-half.html'), ('California overtime rules', '/california-overtime-rules.html')])
PAGES['what-is-time-and-a-half.html'] = ('guide', 'en', 'money', ['ot'], [('How to calculate overtime pay', '/how-to-calculate-overtime-pay.html'), ('Is overtime taxed?', '/is-overtime-taxed.html'), ('What is time and a half?', '/what-is-time-and-a-half.html'), ('California overtime rules', '/california-overtime-rules.html')])
PAGES['car-loan-guide.html'] = ('guide', 'en', 'money', ['car'], [('Personal loan calculator', '/personal-loan-calculator.html'), ('Car loan calculator', '/car-loan-calculator.html'), ('How to calculate loan interest', '/how-to-calculate-loan-interest.html'), ('Loan amortization, explained', '/loan-amortization-explained.html')])
PAGES['dealer-financing-vs-credit-union-auto-loan.html'] = ('guide', 'en', 'money', ['car'], [('Personal loan calculator', '/personal-loan-calculator.html'), ('Car loan calculator', '/car-loan-calculator.html'), ('How to calculate loan interest', '/how-to-calculate-loan-interest.html'), ('Loan amortization, explained', '/loan-amortization-explained.html')])
PAGES['electric-car-loan-guide-2026.html'] = ('guide', 'en', 'money', ['car'], [('Personal loan calculator', '/personal-loan-calculator.html'), ('Car loan calculator', '/car-loan-calculator.html'), ('How to calculate loan interest', '/how-to-calculate-loan-interest.html'), ('Loan amortization, explained', '/loan-amortization-explained.html')])
PAGES['how-much-car-can-i-afford.html'] = ('guide', 'en', 'money', ['car'], [('Personal loan calculator', '/personal-loan-calculator.html'), ('Car loan calculator', '/car-loan-calculator.html'), ('How to calculate loan interest', '/how-to-calculate-loan-interest.html'), ('Loan amortization, explained', '/loan-amortization-explained.html')])
PAGES['should-i-pay-off-car-loan-early.html'] = ('guide', 'en', 'money', ['car'], [('Personal loan calculator', '/personal-loan-calculator.html'), ('Car loan calculator', '/car-loan-calculator.html'), ('How to calculate loan interest', '/how-to-calculate-loan-interest.html'), ('Loan amortization, explained', '/loan-amortization-explained.html')])
PAGES['cibil-score-personal-loan-rate-india.html'] = ('guide', 'en', 'money', ['ploan'], [('Personal loan calculator', '/personal-loan-calculator.html'), ('Car loan calculator', '/car-loan-calculator.html'), ('How to calculate loan interest', '/how-to-calculate-loan-interest.html'), ('Loan amortization, explained', '/loan-amortization-explained.html')])
PAGES['how-to-calculate-credit-card-interest.html'] = ('guide', 'en', 'money', ['btrans', 'ploan'], [('Personal loan calculator', '/personal-loan-calculator.html'), ('Car loan calculator', '/car-loan-calculator.html'), ('How to calculate loan interest', '/how-to-calculate-loan-interest.html'), ('Loan amortization, explained', '/loan-amortization-explained.html')])
PAGES['how-to-calculate-loan-interest.html'] = ('guide', 'en', 'money', ['ploan'], [('Personal loan calculator', '/personal-loan-calculator.html'), ('Car loan calculator', '/car-loan-calculator.html'), ('How to calculate loan interest', '/how-to-calculate-loan-interest.html'), ('Loan amortization, explained', '/loan-amortization-explained.html')])
PAGES['how-to-improve-loan-eligibility.html'] = ('guide', 'en', 'money', ['ploan'], [('Personal loan calculator', '/personal-loan-calculator.html'), ('Car loan calculator', '/car-loan-calculator.html'), ('How to calculate loan interest', '/how-to-calculate-loan-interest.html'), ('Loan amortization, explained', '/loan-amortization-explained.html')])
PAGES['loan-amortization-explained.html'] = ('guide', 'en', 'money', ['ploan'], [('Personal loan calculator', '/personal-loan-calculator.html'), ('Car loan calculator', '/car-loan-calculator.html'), ('How to calculate loan interest', '/how-to-calculate-loan-interest.html'), ('Loan amortization, explained', '/loan-amortization-explained.html')])
PAGES['personal-loan-calculator-guide.html'] = ('guide', 'en', 'money', ['ploan'], [('Personal loan calculator', '/personal-loan-calculator.html'), ('Car loan calculator', '/car-loan-calculator.html'), ('How to calculate loan interest', '/how-to-calculate-loan-interest.html'), ('Loan amortization, explained', '/loan-amortization-explained.html')])
PAGES['personal-loan-foreclosure-charges-india.html'] = ('guide', 'en', 'money', ['ploan'], [('Personal loan calculator', '/personal-loan-calculator.html'), ('Car loan calculator', '/car-loan-calculator.html'), ('How to calculate loan interest', '/how-to-calculate-loan-interest.html'), ('Loan amortization, explained', '/loan-amortization-explained.html')])
PAGES['personal-loan-vs-credit-card.html'] = ('guide', 'en', 'money', ['btrans', 'ploan'], [('Personal loan calculator', '/personal-loan-calculator.html'), ('Car loan calculator', '/car-loan-calculator.html'), ('How to calculate loan interest', '/how-to-calculate-loan-interest.html'), ('Loan amortization, explained', '/loan-amortization-explained.html')])
PAGES['top-up-loan-vs-personal-loan-india.html'] = ('guide', 'en', 'money', ['ploan'], [('Personal loan calculator', '/personal-loan-calculator.html'), ('Car loan calculator', '/car-loan-calculator.html'), ('How to calculate loan interest', '/how-to-calculate-loan-interest.html'), ('Loan amortization, explained', '/loan-amortization-explained.html')])
PAGES['fixed-vs-variable-interest-rate.html'] = ('guide', 'en', 'money', ['ploan'], [('Personal loan calculator', '/personal-loan-calculator.html'), ('Car loan calculator', '/car-loan-calculator.html'), ('How to calculate loan interest', '/how-to-calculate-loan-interest.html'), ('Loan amortization, explained', '/loan-amortization-explained.html')])
PAGES['cash-out-refinance-vs-home-equity-loan.html'] = ('guide', 'en', 'money', ['refi'], [('When should you refinance?', '/when-should-you-refinance.html'), ('Refinance closing costs', '/refinance-closing-costs-explained.html'), ('What is a mortgage refinance?', '/what-is-mortgage-refinance.html'), ('Mortgage overpayment guide', '/mortgage-overpayment-guide.html')])
PAGES['refinance-closing-costs-explained.html'] = ('guide', 'en', 'money', ['refi'], [('When should you refinance?', '/when-should-you-refinance.html'), ('Refinance closing costs', '/refinance-closing-costs-explained.html'), ('What is a mortgage refinance?', '/what-is-mortgage-refinance.html'), ('Mortgage overpayment guide', '/mortgage-overpayment-guide.html')])
PAGES['what-is-mortgage-refinance.html'] = ('guide', 'en', 'money', ['refi'], [('When should you refinance?', '/when-should-you-refinance.html'), ('Refinance closing costs', '/refinance-closing-costs-explained.html'), ('What is a mortgage refinance?', '/what-is-mortgage-refinance.html'), ('Mortgage overpayment guide', '/mortgage-overpayment-guide.html')])
PAGES['when-should-you-refinance.html'] = ('guide', 'en', 'money', ['refi'], [('When should you refinance?', '/when-should-you-refinance.html'), ('Refinance closing costs', '/refinance-closing-costs-explained.html'), ('What is a mortgage refinance?', '/what-is-mortgage-refinance.html'), ('Mortgage overpayment guide', '/mortgage-overpayment-guide.html')])
PAGES['mortgage-overpayment-allowance-uk.html'] = ('guide', 'en', 'money', ['mort'], [('When should you refinance?', '/when-should-you-refinance.html'), ('Refinance closing costs', '/refinance-closing-costs-explained.html'), ('What is a mortgage refinance?', '/what-is-mortgage-refinance.html'), ('Mortgage overpayment guide', '/mortgage-overpayment-guide.html')])
PAGES['mortgage-overpayment-guide.html'] = ('guide', 'en', 'money', ['mort'], [('When should you refinance?', '/when-should-you-refinance.html'), ('Refinance closing costs', '/refinance-closing-costs-explained.html'), ('What is a mortgage refinance?', '/what-is-mortgage-refinance.html'), ('Mortgage overpayment guide', '/mortgage-overpayment-guide.html')])
PAGES['offset-mortgage-vs-overpayment-uk.html'] = ('guide', 'en', 'money', ['mort'], [('When should you refinance?', '/when-should-you-refinance.html'), ('Refinance closing costs', '/refinance-closing-costs-explained.html'), ('What is a mortgage refinance?', '/what-is-mortgage-refinance.html'), ('Mortgage overpayment guide', '/mortgage-overpayment-guide.html')])
PAGES['remortgage-vs-overpayment-uk.html'] = ('guide', 'en', 'money', ['mort'], [('When should you refinance?', '/when-should-you-refinance.html'), ('Refinance closing costs', '/refinance-closing-costs-explained.html'), ('What is a mortgage refinance?', '/what-is-mortgage-refinance.html'), ('Mortgage overpayment guide', '/mortgage-overpayment-guide.html')])
PAGES['compounding-frequency-explained.html'] = ('guide', 'en', 'money', ['int'], [('Simple vs compound interest', '/simple-vs-compound-interest.html'), ('What is APY?', '/what-is-apy.html'), ('Rule of 72, explained', '/rule-of-72-explained.html'), ('Compounding frequency', '/compounding-frequency-explained.html')])
PAGES['rule-of-72-explained.html'] = ('guide', 'en', 'money', ['int'], [('Simple vs compound interest', '/simple-vs-compound-interest.html'), ('What is APY?', '/what-is-apy.html'), ('Rule of 72, explained', '/rule-of-72-explained.html'), ('Compounding frequency', '/compounding-frequency-explained.html')])
PAGES['simple-vs-compound-interest.html'] = ('guide', 'en', 'money', ['int'], [('Simple vs compound interest', '/simple-vs-compound-interest.html'), ('What is APY?', '/what-is-apy.html'), ('Rule of 72, explained', '/rule-of-72-explained.html'), ('Compounding frequency', '/compounding-frequency-explained.html')])
PAGES['what-is-a-good-apy.html'] = ('guide', 'en', 'money', ['int'], [('Simple vs compound interest', '/simple-vs-compound-interest.html'), ('What is APY?', '/what-is-apy.html'), ('Rule of 72, explained', '/rule-of-72-explained.html'), ('Compounding frequency', '/compounding-frequency-explained.html')])
PAGES['what-is-apy.html'] = ('guide', 'en', 'money', ['int'], [('Simple vs compound interest', '/simple-vs-compound-interest.html'), ('What is APY?', '/what-is-apy.html'), ('Rule of 72, explained', '/rule-of-72-explained.html'), ('Compounding frequency', '/compounding-frequency-explained.html')])
PAGES['gold-price-today-guide.html'] = ('guide', 'en', 'guides', [], [('Quotazione oro oggi (IT)', '/it/quotazione-oro-oggi.html'), ('Interest calculator', '/interest-calculator.html')])
PAGES['conviene-comprare-oro-oggi.html'] = ('guide', 'it', 'guide', ['oro'], [('Quotazione oro oggi', '/it/quotazione-oro-oggi.html'), ("Tasse sull'oro in Italia", '/it/tasse-oro-italia.html'), ("Quando vendere l'oro", '/it/quando-vendere-oro.html'), ('Oro fisico vs ETC', '/it/oro-fisico-vs-etc.html'), ('Come leggere la quotazione', '/it/come-leggere-quotazione-oro.html')])
PAGES['oro-usato-compro-oro-guida.html'] = ('guide', 'it', 'guide', ['oro'], [('Quotazione oro oggi', '/it/quotazione-oro-oggi.html'), ("Tasse sull'oro in Italia", '/it/tasse-oro-italia.html'), ("Quando vendere l'oro", '/it/quando-vendere-oro.html'), ('Oro fisico vs ETC', '/it/oro-fisico-vs-etc.html'), ('Come leggere la quotazione', '/it/come-leggere-quotazione-oro.html')])
PAGES['it/come-leggere-quotazione-oro.html'] = ('guide', 'it', 'guide', ['oro'], [('Quotazione oro oggi', '/it/quotazione-oro-oggi.html'), ("Tasse sull'oro in Italia", '/it/tasse-oro-italia.html'), ("Quando vendere l'oro", '/it/quando-vendere-oro.html'), ('Oro fisico vs ETC', '/it/oro-fisico-vs-etc.html'), ('Come leggere la quotazione', '/it/come-leggere-quotazione-oro.html')])
PAGES['it/oro-e-inflazione.html'] = ('guide', 'it', 'guide', ['oro'], [('Quotazione oro oggi', '/it/quotazione-oro-oggi.html'), ("Tasse sull'oro in Italia", '/it/tasse-oro-italia.html'), ("Quando vendere l'oro", '/it/quando-vendere-oro.html'), ('Oro fisico vs ETC', '/it/oro-fisico-vs-etc.html'), ('Come leggere la quotazione', '/it/come-leggere-quotazione-oro.html')])
PAGES['it/oro-fisico-vs-etc.html'] = ('guide', 'it', 'guide', ['oro'], [('Quotazione oro oggi', '/it/quotazione-oro-oggi.html'), ("Tasse sull'oro in Italia", '/it/tasse-oro-italia.html'), ("Quando vendere l'oro", '/it/quando-vendere-oro.html'), ('Oro fisico vs ETC', '/it/oro-fisico-vs-etc.html'), ('Come leggere la quotazione', '/it/come-leggere-quotazione-oro.html')])
PAGES['it/quando-vendere-oro.html'] = ('guide', 'it', 'guide', ['oro'], [('Quotazione oro oggi', '/it/quotazione-oro-oggi.html'), ("Tasse sull'oro in Italia", '/it/tasse-oro-italia.html'), ("Quando vendere l'oro", '/it/quando-vendere-oro.html'), ('Oro fisico vs ETC', '/it/oro-fisico-vs-etc.html'), ('Come leggere la quotazione', '/it/come-leggere-quotazione-oro.html')])
PAGES['it/tasse-oro-italia.html'] = ('guide', 'it', 'guide', ['oro'], [('Quotazione oro oggi', '/it/quotazione-oro-oggi.html'), ("Tasse sull'oro in Italia", '/it/tasse-oro-italia.html'), ("Quando vendere l'oro", '/it/quando-vendere-oro.html'), ('Oro fisico vs ETC', '/it/oro-fisico-vs-etc.html'), ('Come leggere la quotazione', '/it/come-leggere-quotazione-oro.html')])
PAGES['it/quotazione-oro-oggi.html'] = ('calc', 'it', 'guide', [], [('Quotazione oro oggi', '/it/quotazione-oro-oggi.html'), ("Tasse sull'oro in Italia", '/it/tasse-oro-italia.html'), ("Quando vendere l'oro", '/it/quando-vendere-oro.html'), ('Oro fisico vs ETC', '/it/oro-fisico-vs-etc.html'), ('Come leggere la quotazione', '/it/come-leggere-quotazione-oro.html')])
PAGES['it/index.html'] = ('hub', 'it', 'guide', [], [])
PAGES['br/aviso-previo-trabalhado-indenizado.html'] = ('guide', 'br', 'guias', ['resc'], [('Como calcular a rescisão', '/br/como-calcular-rescisao.html'), ('FGTS na rescisão', '/br/fgts-na-rescisao.html'), ('Multa do FGTS 40% e 20%', '/br/multa-fgts-40-20.html'), ('Aviso prévio', '/br/aviso-previo-trabalhado-indenizado.html'), ('Seguro-desemprego 2026', '/br/seguro-desemprego-2026.html')])
PAGES['br/como-calcular-rescisao.html'] = ('guide', 'br', 'guias', ['resc'], [('Como calcular a rescisão', '/br/como-calcular-rescisao.html'), ('FGTS na rescisão', '/br/fgts-na-rescisao.html'), ('Multa do FGTS 40% e 20%', '/br/multa-fgts-40-20.html'), ('Aviso prévio', '/br/aviso-previo-trabalhado-indenizado.html'), ('Seguro-desemprego 2026', '/br/seguro-desemprego-2026.html')])
PAGES['br/decimo-terceiro-salario.html'] = ('guide', 'br', 'guias', ['resc'], [('Como calcular a rescisão', '/br/como-calcular-rescisao.html'), ('FGTS na rescisão', '/br/fgts-na-rescisao.html'), ('Multa do FGTS 40% e 20%', '/br/multa-fgts-40-20.html'), ('Aviso prévio', '/br/aviso-previo-trabalhado-indenizado.html'), ('Seguro-desemprego 2026', '/br/seguro-desemprego-2026.html')])
PAGES['br/ferias-vencidas-rescisao.html'] = ('guide', 'br', 'guias', ['resc'], [('Como calcular a rescisão', '/br/como-calcular-rescisao.html'), ('FGTS na rescisão', '/br/fgts-na-rescisao.html'), ('Multa do FGTS 40% e 20%', '/br/multa-fgts-40-20.html'), ('Aviso prévio', '/br/aviso-previo-trabalhado-indenizado.html'), ('Seguro-desemprego 2026', '/br/seguro-desemprego-2026.html')])
PAGES['br/fgts-na-rescisao.html'] = ('guide', 'br', 'guias', ['resc'], [('Como calcular a rescisão', '/br/como-calcular-rescisao.html'), ('FGTS na rescisão', '/br/fgts-na-rescisao.html'), ('Multa do FGTS 40% e 20%', '/br/multa-fgts-40-20.html'), ('Aviso prévio', '/br/aviso-previo-trabalhado-indenizado.html'), ('Seguro-desemprego 2026', '/br/seguro-desemprego-2026.html')])
PAGES['br/multa-fgts-40-20.html'] = ('guide', 'br', 'guias', ['resc'], [('Como calcular a rescisão', '/br/como-calcular-rescisao.html'), ('FGTS na rescisão', '/br/fgts-na-rescisao.html'), ('Multa do FGTS 40% e 20%', '/br/multa-fgts-40-20.html'), ('Aviso prévio', '/br/aviso-previo-trabalhado-indenizado.html'), ('Seguro-desemprego 2026', '/br/seguro-desemprego-2026.html')])
PAGES['br/rescisao-empregada-domestica.html'] = ('guide', 'br', 'guias', ['resc'], [('Como calcular a rescisão', '/br/como-calcular-rescisao.html'), ('FGTS na rescisão', '/br/fgts-na-rescisao.html'), ('Multa do FGTS 40% e 20%', '/br/multa-fgts-40-20.html'), ('Aviso prévio', '/br/aviso-previo-trabalhado-indenizado.html'), ('Seguro-desemprego 2026', '/br/seguro-desemprego-2026.html')])
PAGES['br/seguro-desemprego-2026.html'] = ('guide', 'br', 'guias', ['resc'], [('Como calcular a rescisão', '/br/como-calcular-rescisao.html'), ('FGTS na rescisão', '/br/fgts-na-rescisao.html'), ('Multa do FGTS 40% e 20%', '/br/multa-fgts-40-20.html'), ('Aviso prévio', '/br/aviso-previo-trabalhado-indenizado.html'), ('Seguro-desemprego 2026', '/br/seguro-desemprego-2026.html')])
PAGES['br/trct-homologacao-rescisao.html'] = ('guide', 'br', 'guias', ['resc'], [('Como calcular a rescisão', '/br/como-calcular-rescisao.html'), ('FGTS na rescisão', '/br/fgts-na-rescisao.html'), ('Multa do FGTS 40% e 20%', '/br/multa-fgts-40-20.html'), ('Aviso prévio', '/br/aviso-previo-trabalhado-indenizado.html'), ('Seguro-desemprego 2026', '/br/seguro-desemprego-2026.html')])
PAGES['br/calculadora-rescisao.html'] = ('calc', 'br', 'calc', [], [('Como calcular a rescisão', '/br/como-calcular-rescisao.html'), ('FGTS na rescisão', '/br/fgts-na-rescisao.html'), ('Multa do FGTS 40% e 20%', '/br/multa-fgts-40-20.html'), ('Aviso prévio', '/br/aviso-previo-trabalhado-indenizado.html'), ('Seguro-desemprego 2026', '/br/seguro-desemprego-2026.html')])
PAGES['br/index.html'] = ('hub', 'br', 'guias', [], [])


if __name__ == "__main__":
    for a in sys.argv[1:]:
        convert(a)
