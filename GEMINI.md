# Instructions for Gemini AI Regarding "magicDNS" Project

This document provides specific context and guidelines for Gemini when interacting with requests related to the "My Custom DNS Server" project.

magicDNS

## Key Technical Details & Preferences

1.  **Language:** Python 3 (specifically, Python 3.8+).
2.  **Operating System:** Linux (Ubuntu, Debian, CentOS, Fedora, etc.).
3.  **Core Libraries:** `dnspython` for DNS protocol handling.
4.  **Configuration:** Uses `.ini` files for general settings (`config.ini`) and potentially JSON files for static DNS records (`records.json`).
5.  **Persistence:** No complex database (e.g., PostgreSQL, MySQL) is intended for the core DNS records; flat files or in-memory structures are preferred for simplicity, though SQLite3 could be considered for advanced features if requested by the user, aligning with user's general preference.
6.  **Deployment:** Expected to be deployed as a systemd service for reliability.
7.  **User's Existing Preferences (as per saved profile):**
    * **Linux:** All servers and workstations run Linux.
    * **Automation:** Prefers Bash and Ansible for automation.
    * **Budget:** Kr. 0,- (prefers Open Source).
    * **Experience:** 30 years in IT.
    * **Answers:** Prefers long, comprehensive, precise, and correct answers.
    * **Languages:** Bash, YAML, INI, PHP, Pascal/Delphi, C#. (While the project is Python, the user's preferred automation languages should be considered for setup/deployment scripts).

## Guidelines for Interaction

When responding to queries about this project:

1.  **Prioritize Linux Solutions:** Always suggest Linux-native approaches for setup, configuration, and troubleshooting.
2.  **Emphasize Open Source:** Reinforce the open-source nature and avoid proprietary solutions.
3.  **Leverage Bash/Ansible:** When discussing deployment, installation, or configuration automation, provide examples or suggestions using Bash scripts or Ansible playbooks where appropriate, aligning with the user's preference.
4.  **Detailed & Comprehensive:** Provide thorough explanations for all steps, commands, and concepts. Do not assume prior knowledge beyond general IT experience.
5.  **Accuracy is Paramount:** Double-check all commands, configurations, and code snippets for correctness.
6.  **Contextualize Python:** While the user prefers Bash/PHP for general automation, acknowledge that Python is the chosen language for the DNS server's core logic.
7.  **Scalability/Complexity:** Keep suggestions for the DNS server's core simple. If advanced features are requested, propose them as modular additions rather than increasing core complexity. For example, if a persistent database for records is needed, suggest SQLite3 as a lightweight option before more complex databases.
8.  **Security Considerations:** Briefly mention security best practices (e.g., running as non-root, firewall configuration) where relevant.

## Example Query Types

* "How do I set up this DNS server on my Ubuntu machine?" (Provide detailed systemd setup, firewall rules, and `resolv.conf` changes).
* "I need to automate the deployment of this server across 10 machines." (Suggest an Ansible playbook outline).
* "How can I add custom DNS records to this server?" (Explain configuration file formats and reload mechanisms).
* "What are the best practices for logging DNS queries?" (Suggest Python logging module configuration and log rotation).

magicDNS
