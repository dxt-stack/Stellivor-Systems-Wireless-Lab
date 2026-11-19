# Security and privacy

STELLIVOR is an offline-first local systems and wireless learning workbench. Diagnostics run only after the operator selects them. The project does not automatically upload reports, hashes, credentials, or scan results.

## Local credential-audit boundary

The optional John the Ripper workbench operates on a local hash file and, where selected, a local wordlist supplied by the operator. The operator must confirm ownership or explicit authorization before an audit starts. Process execution uses argument arrays without a shell; no network hash collection, handshake capture, or remote credential attempts are part of this workflow.\n\n## Saved Wi-Fi key display\n\nThe saved-profile reveal action can display keys already stored for Wi-Fi profiles on the local device. It is an explicit interactive operation, not a startup action. Windows uses the native WLAN profile command with key=clear; Linux uses NetworkManager nmcli --show-secrets. Android/Termux does not expose these credentials to this adapter, and macOS retrieval is not implemented yet. This does not discover passwords for nearby networks or contact any remote system.\n\nKey values are transient display data: the UI does not add them to serializable Result objects, session history, logs, or report exports. Treat terminal scrollback and screenshots as sensitive. Only inspect devices and profiles you own or are authorized to administer.

John's output, including recovered results from the local authorized audit, is intentionally available in the operator's terminal/session. This is a local operator feature, not repository content. Hash files, wordlists, John pot files, session files, and recovered output are sensitive and should remain on systems and storage controlled by the operator.

## Reports and sharing

JSON and Markdown report exports are local. Credential-audit stdout/stderr is excluded from report data by default while ordinary result metadata is preserved. The interactive export flow offers an explicit opt-in to include it for a private report. Only enable that option when the destination is controlled by you and the report will not be shared publicly. Review all reports before sharing: other diagnostic results can also contain hostnames, IP/MAC addresses, usernames, paths, and machine details.

## Repository hygiene

Never commit real hash files, wordlists containing private material, John pot/session files, recovered credentials, private network inventories, or generated reports containing sensitive data. Use synthetic fixtures in tests. Keep secrets out of issues, pull requests, screenshots, logs, and commit messages.

## Vulnerability reporting

Do not publish exploitable details or private data in a public issue. Contact the repository owner privately through the GitHub repository's security contact or another verified private channel. Include affected version/commit, impact, reproduction steps, and a safe proof of concept. Do not include real credentials, hashes, or personal data.

## Scope and limitations

STELLIVOR is a diagnostic and learning tool, not a guarantee of system or network security. Platform permissions and native tool behavior vary. Use it only on systems, networks, and credential material you own or are explicitly authorized to assess.
