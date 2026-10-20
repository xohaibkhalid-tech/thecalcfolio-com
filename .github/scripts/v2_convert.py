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
CSS_VER = "3"
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
    btns = "".join(f'<a class="btn" href="{SITE}{TOOLS[k][1]}">{TOOLS[k][0]} →</a>' for k in keys)
    return (f'<div class="tool-cta"><div class="tc-text"><strong>{t["calc_now"]}</strong><span>{t["calc_sub"]}</span></div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:10px">{btns}</div></div>\n')


def sidebar(lang, related, page=""):
    t = T[lang]
    rows = "".join(f'<a class="row" href="{SITE}{u}"><span>{n}</span><span aria-hidden="true">→</span></a>' for n, u in related if u.lstrip("/") != page)
    keys = ["azr"] if lang == "de" else ["ebay", "paypal", "etsy", "stripe", "azr"]
    tops = "".join(f'<a href="{SITE}{TOOLS[k][1]}"><span class="ic {TOOLS[k][2]}" aria-hidden="true">{TOOLS[k][3]}</span>{TOOLS[k][0].replace(" Fee Calculator", " fees")}'
                   + (' <small style="opacity:.7;font-weight:600">(DE)</small>' if k == "azr" and lang == "en" else "") + '</a>' for k in keys)
    if lang == "de":
        tops += f'<a href="{SITE}/de/ueberstunden-berechnen.html"><span class="ic c-coral" aria-hidden="true">Ü</span>Überstunden berechnen</a>'
    out = '<aside class="side" aria-label="' + t["related"] + '">\n'
    if rows:
        out += f'<div class="box"><h2>{t["related"]}</h2>{rows}</div>\n'
    out += f'<div class="box dark"><h2>{t["top"]}</h2><div class="top-tools">{tops}</div></div>\n</aside>\n'
    return out


def hub_hero(page):
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
(function(){document.querySelectorAll('.card').forEach(function(c){var b=c.querySelector('button.go');if(!b)return;
var run=function(){b.click();};c.querySelectorAll('input,select').forEach(function(i){i.addEventListener('input',run);i.addEventListener('change',run);});});
document.querySelectorAll('.card button.go').forEach(function(b){b.click();});})();
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
    m = re.search(r'<header class="(?:art|top)">(.*?)</header>\s*', body, flags=re.S)
    if not m:
        raise SystemExit(f"no hero header in {page}")
    hero_inner = m.group(1)
    body = body[:m.start()] + body[m.end():]
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
        content = content.replace('<div class="card">', '<div class="card tool">', 1)

    t = T[lang]
    if lang == "de":
        crumbs = f'<li><a href="{SITE}/de/">{t["home"]}</a></li>'
        if page != "de/index.html":
            crumbs += f'<li aria-current="page">{html.escape(strip_tags(h1))}</li>'
        tag = "Ratgeber · Arbeitszeit" if kind == "guide" else "Rechner &amp; Ratgeber auf Deutsch"
    else:
        sec = {"calc": (t["seller"], "/calculators.html"), "guide": (t["guides"], "/guides.html")}.get(kind)
        crumbs = f'<li><a href="{SITE}/">{t["home"]}</a></li>'
        if sec:
            crumbs += f'<li><a href="{SITE}{sec[1]}">{sec[0]}</a></li>'
        crumbs += f'<li aria-current="page">{html.escape(strip_tags(h1))}</li>'
        tag = strip_tags(meta.group(1)) if meta else ("2026 US rates" if kind == "calc" else "The Calcfolio")
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
                 (AUTO_CALC if kind == "calc" else "") + trailing_comments + "\n</body>\n</html>\n")
    p.write_text(page_html, encoding="utf-8")
    print("converted", page)


if __name__ == "__main__":
    for a in sys.argv[1:]:
        convert(a)
