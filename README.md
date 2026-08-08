# CyberGhost OSINT

**Community Edition** — Zero Configuration Passive Reconnaissance & Intelligence Framework

CyberGhost OSINT is an open-source, fast, and modular OSINT tool built for security researchers, penetration testers, and threat intelligence analysts. The Community Edition focuses on **zero configuration**, allowing you to gather actionable intelligence immediately without needing API keys, databases, or complex infrastructure.

## Features

- **Zero Config**: No mandatory `.env` files, API keys, or databases. Just install and run.
- **Fast & Asynchronous**: Written in Python using `aiohttp` and `asyncio` for rapid parallel scanning.
- **Passive Intelligence**: Gathers data safely without interacting directly with the target in a noisy way.
- **Security Posture Scoring**: Automatically calculates a security score based on DNS security, exposed headers, open ports, and IP reputation.
- **Modular Architecture**: Easily extensible with isolated OSINT modules.
- **Standardized Exports**: Export findings to JSON, HTML, or STIX 2.1 formats out of the box.

## Installation

You can install CyberGhost OSINT directly from the source:

```bash
git clone https://github.com/Leobatman/CyberGhost-OSINT-Community-Edition-v1.0.0
cd CyberGhost-OSINT-Community-Edition-v1.0.0
```

## Quick Start

Run a standard passive investigation against a target domain or IP:

```bash
python3 cyberghost.py example.com
```

### Advanced Usage

Export the results as a beautiful HTML report:
```bash
python3 cyberghost.py example.com --html
```

Export the results as a STIX 2.1 bundle for Threat Intelligence platforms:
```bash
python3 cyberghost.py example.com --stix
```

Export as raw JSON for external ingestion:
```bash
python3 cyberghost.py example.com --json
```

## Architecture

CyberGhost OSINT follows a clean, modular architecture:

```text
cyberghost.py        -> Main CLI Orchestrator
core/                -> Core models, configuration, and reporting
modules/             -> Isolated OSINT sources (DNS, Certs, Web, Network)
```

- **DNS Intel**: Resolves A/AAAA records and checks SPF/DMARC configurations.
- **Cert Intel**: Queries Certificate Transparency logs (crt.sh) for valid certificates and subdomain discovery.
- **Web Intel**: Analyzes security headers, exposed emails, robots.txt, and generates Google Dorks.
- **Network Intel**: Performs RDAP lookups, DNSBL reputation checks, and minimal port scanning.

## Responsible Use

This tool is designed strictly for **authorized** security research, educational purposes, and defensive threat intelligence. Do not use CyberGhost OSINT against targets you do not own or do not have explicit authorization to investigate. 

Please read the [RESPONSIBLE_USE.md](RESPONSIBLE_USE.md) file before using this software.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
