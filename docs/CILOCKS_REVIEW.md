# CiLocks review and safe integration boundary

The project reviewed for this release is [`tegal1337/CiLocks`](https://github.com/tegal1337/CiLocks), revision `480fd5545394ee0556fd881dc2ed2685feb7227e`, licensed under GPL-3.0. It is an Android/iOS hacking toolkit whose documented capabilities include lockscreen bypassing, PIN brute force, Metasploit payload/backdoor creation, spyware-style camera/IP logging, and data or credential extraction.

STELLIVOR does **not** copy, fork, vendor, or reimplement those capabilities. They are outside STELLIVOR's defensive purpose and could enable unauthorized access, surveillance, credential theft, or malware deployment. The GPL-3.0 license is also incompatible with treating copied CiLocks code as part of STELLIVOR's MIT-licensed codebase without changing the project's licensing and distribution obligations.

This release adopts only independently implemented, non-offensive product ideas:

- A more capable terminal shell with help, command-palette aliases, rerun, export, quit, and responsive navigation shortcuts.
- A real, read-only ADB/device readiness check for devices already visible to the local ADB client.
- Explicit status reporting for missing ADB, pending authorization, no connected device, and authorized devices.
- Clear boundaries that prohibit lockscreen bypass, PIN guessing, arbitrary remote shell execution, payload installation, covert camera/IP logging, and credential extraction.

The ADB module never installs packages, unlocks a device, guesses a PIN, runs an arbitrary device command, captures private data, or changes device state. A connected ADB device is not treated as permission to bypass its authentication or inspect data without the owner's authorization.
