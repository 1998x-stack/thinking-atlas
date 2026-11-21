#!/usr/bin/env python3
"""Desktop/mobile browser smoke QA for Thinking Atlas, including search interaction."""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError as exc:
    raise SystemExit("Install requirements-dev.txt and Chromium before browser QA") from exc

ROOT=Path(__file__).resolve().parents[1]
ROUTES=[
    "index.html",
    "topics/index.html",
    "archive/index.html",
    "methodology/index.html",
    "categories/institutions/index.html",
    "posts/institutions/labor-dispatch/index.html",
    "posts/history/credible-commitment/index.html",
]
VIEWPORTS=[("desktop",1440,900),("mobile-390",390,844),("mobile-360",360,740)]


async def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site",type=Path,default=ROOT/"_site")
    parser.add_argument("--output",type=Path,default=ROOT/"reports/browser")
    args=parser.parse_args()
    output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    site=args.site.resolve()
    errors=[]
    findings=[]
    async with async_playwright() as playwright:
        browser=await playwright.chromium.launch(headless=True)
        for label,width,height in VIEWPORTS:
            context=await browser.new_context(viewport={"width":width,"height":height},device_scale_factor=1)
            for route in ROUTES:
                page=await context.new_page()
                js_errors=[]
                page.on("pageerror",lambda exc: js_errors.append(str(exc)))
                page.on("console",lambda msg: js_errors.append("console error: "+msg.text) if msg.type=="error" else None)
                url=(site/route).as_uri()
                await page.goto(url,wait_until="load")
                # Lazy-loaded cards outside the viewport are not broken: load them explicitly
                # before checking the full-document image contract.
                await page.evaluate('''() => {
                    document.querySelectorAll("img[loading=lazy]").forEach(img=>img.loading="eager");
                }''')
                try:
                    await page.wait_for_function("Array.from(document.images).every(img => img.complete)", timeout=4000)
                except Exception:
                    pass
                state=await page.evaluate("""() => ({
                    width: document.documentElement.scrollWidth,
                    viewport: document.documentElement.clientWidth,
                    headings: document.querySelectorAll("h1").length,
                    main: document.querySelectorAll("main").length,
                    broken: Array.from(document.images).filter(img=>!img.complete || img.naturalWidth===0).map(img=>img.src),
                    overflowers: Array.from(document.querySelectorAll("body *")).filter(el => {
                        const box=el.getBoundingClientRect();
                        return box.right > document.documentElement.clientWidth+2 &&
                          getComputedStyle(el).display!=="none" && box.width>0;
                    }).slice(0,12).map(el=>({
                        tag:el.tagName.toLowerCase(), cls:el.className?.baseVal || el.className,
                        width:Math.round(el.getBoundingClientRect().width),
                        right:Math.round(el.getBoundingClientRect().right),
                        text:(el.innerText||"").slice(0,45)
                    }))
                })""")
                name=label+"__"+route.replace("/","_")
                await page.screenshot(path=str(output/(name+".png")),full_page=True)
                if state["width"]>state["viewport"]+2:
                    errors.append(name+": horizontal overflow "+str(state["width"])+" > "+str(state["viewport"]))
                if state["broken"]:
                    errors.append(name+": broken images "+repr(state["broken"]))
                if state["headings"]!=1 or state["main"]!=1:
                    errors.append(name+": expected one h1 and main "+repr(state))
                if js_errors:
                    errors.append(name+": "+repr(js_errors))
                findings.append({"viewport":label,"route":route,**state,"js_errors":js_errors})
                if route=="index.html":
                    search=page.locator("#search")
                    await search.fill("劳务派遣")
                    visible=await page.locator("#post-index .post-card:visible").count()
                    if visible!=1:
                        errors.append(label+": search expected 1 visible card, found "+str(visible))
                    await search.fill("")
                    await page.locator("#research-status").select_option("outline")
                    shown=await page.locator("#post-index .post-card:visible").count()
                    if shown<1:
                        errors.append(label+": status filter returned no articles")
                    await page.keyboard.press("Tab")
                    focus=await page.evaluate("document.activeElement.tagName")
                    if not focus:
                        errors.append(label+": keyboard focus not available")
                    findings[-1]["search_visible"]=visible
                    findings[-1]["outline_visible"]=shown
                await page.close()
            await context.close()
        await browser.close()
    report={"passed":not errors,"routes":len(ROUTES),"viewports":len(VIEWPORTS),"checks":findings,"errors":errors}
    (output/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("BROWSER QA:",len(findings),"route/viewport checks;",len(errors),"errors")
    for err in errors:
        print("FAIL:",err)
    if errors:
        raise SystemExit(1)


if __name__=="__main__":
    asyncio.run(main())
