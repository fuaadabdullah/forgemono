# Private IMAP configuration

Use the environment variable `GMAIL_USERNAME` for the account address rather than committing it to a public repository.

The checked-in `config.yaml` deliberately leaves the username empty. Keep real mailbox identities in local, untracked configuration. If `GMAIL_USERNAME` is absent, the scanner can still read a username deliberately provided in a local config file.

The checked-in example uses dry-run mode by default. Review every proposed account action before enabling destructive operations.

The test connection helper requires an explicitly configured username and does not publish or infer a personal account address.
