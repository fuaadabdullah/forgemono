# Vercel CLI Global Options

Copy page

Ask AI about this page

Last updated March 4, 2025

Global options are commonly available to use with multiple Vercel CLI commands.

## [Current Working Directory](#current-working-directory)

The `--cwd` option can be used to provide a working directory (that can be different from the current directory) when running Vercel CLI commands.

This option can be a relative or absolute path.

terminal

```
vercel --cwd ~/path-to/project
```

Using the `vercel` command with the `--cwd` option.

## [Debug](#debug)

The `--debug` option, shorthand `-d`, can be used to provide a more verbose output when running Vercel CLI commands.

terminal

```
vercel --debug
```

Using the `vercel` command with the `--debug` option.

## [Global config](#global-config)

The `--global-config` option, shorthand `-Q`, can be used set the path to the [global configuration directory](/docs/project-configuration/global-configuration).

terminal

```
vercel --global-config /path-to/global-config-directory
```

Using the `vercel` command with the `--global-config` option.

## [Help](#help)

The `--help` option, shorthand `-h`, can be used to display more information about [Vercel CLI](/cli) commands.

terminal

```
vercel --help
```

Using the `vercel` command with the `--help` option.

terminal

```
vercel alias --help
```

Using the `vercel alias` command with the `--help` option.

## [Local config](#local-config)

The `--local-config` option, shorthand `-A`, can be used to set the path to a local `vercel.json` file.

terminal

```
vercel --local-config /path-to/vercel.json
```

Using the `vercel` command with the `--local-config` option.

## [Scope](#scope)

The `--scope` option, shorthand `-S`, can be used to execute Vercel CLI commands from a scope that’s not currently active.

terminal

```
vercel --scope my-team-slug
```

Using the `vercel` command with the `--scope` option.

## [Token](#token)

The `--token` option, shorthand `-t`, can be used to execute Vercel CLI commands with an [authorization token](/account/tokens).

terminal

```
vercel --token iZJb2oftmY4ab12HBzyBXMkp
```

Using the `vercel` command with the `--token` option.

## [No Color](#no-color)

The `--no-color` option, or `NO_COLOR=1` environment variable, can be used to execute Vercel CLI commands with no color or emoji output. This respects the [NO_COLOR standard](https://no-color.org).

terminal

```
vercel login --no-color
```

Using the `vercel` command with the `--no-color` option.
