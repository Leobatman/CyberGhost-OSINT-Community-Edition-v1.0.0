import sys
import os

with open('cyberghost.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

regions = [
    (297, 335), # fetch_url_async, get_dns, get_subdomains
    (359, 371), # detect_tech
    (422, 498), # spider_js_secrets, vuln_scan_misconfig
    (499, 567), # detect_waf, check_subdomain_takeover, fast_fuzz
    (607, 633), # check_dns_sec
    (634, 684), # harvest_robots, analyze_security_headers
    (697, 717)  # check_tech_cves
]

for start, end in regions:
    for i in range(start, end + 1):
        lines[i] = ''

run_scan_start = 787
while not lines[run_scan_start].startswith('async def run_scan'):
    run_scan_start += 1
run_scan_end = 864 

run_scan_new = '''async def run_scan(target, profile="standard", plugins=None, is_dark=False):
    from recon.dns_intel import DNSIntelligence
    from recon.subdomain_enum import SubdomainEnumerator
    from recon.web_recon import WebRecon
    from recon.vuln_scanner import VulnScanner

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=GLOBAL_SSL_CONTEXT)) as session:
        se = SubdomainEnumerator()
        subs_data = await se.get_subdomains(session, target)
        subs = subs_data if subs_data else []

        tasks_dict = {
            "DNS & Security": DNSIntelligence().analyze(target),
            "Web Recon (Tech, WAF, Fuzz)": WebRecon().analyze(target),
            "Subdomains & Takeover": se.enumerate(target),
        }

        if profile in ["standard", "full", "mostruoso", "godmode"]:
            tasks_dict.update({
                "Open Ports": scan_ports_hyper(target),
                "Cloud Enum": cloud_enum(target),
                "Wayback Archive": wayback_urls(session, target)
            })

        if profile in ["full", "mostruoso", "godmode"]:
            tasks_dict.update({
                "IP Reputation": ip_reputation(target),
                "ASN / BGP": get_asn_info(session, target)
            })

        if profile in ["mostruoso", "godmode"]:
            tasks_dict.update({
                "Vuln Scanner (Secrets, Misconfigs)": VulnScanner().analyze(target, {})
            })

        if profile == "godmode":
            tasks_dict.update({
                "Email Harvester": email_harvester(session, target),
                "Shodan Native Recon": shodan_query(target),
                "Passive OSINT Dorks": generate_dorks_and_breaches(target),
            })

        if plugins:
            tasks_dict["Plugins"] = run_plugins(target, plugins)

        results = {}

        print("\\n")
        with Progress(
            SpinnerColumn(spinner_name="dots2" if is_dark else "bouncingBar"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="red" if is_dark else "cyan"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task_name = f"[{'red' if is_dark else 'cyan'}]Invocando Fantasmas no alvo {target}..."
            if profile == "godmode": task_name = f"[bold yellow]⚡ EXECUTANDO GOD MODE ⚡ {target}...[/]"

            task_id = progress.add_task(task_name, total=len(tasks_dict))

            pending = [wrapper(k, v) for k, v in tasks_dict.items()]
            for f in asyncio.as_completed(pending):
                k, res = await f
                results[k] = res
                progress.advance(task_id)

        print("\\n")
        return results

'''

for i in range(run_scan_start, run_scan_end + 1):
    lines[i] = ''
lines[run_scan_start] = run_scan_new

with open('cyberghost.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print('Refactored cyberghost.py')
