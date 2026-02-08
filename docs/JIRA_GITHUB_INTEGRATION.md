# Jira and GitHub Enterprise Server Integration Guide

This guide provides step-by-step instructions for connecting GitHub Enterprise Server to Jira Cloud using the GitHub for Atlassian app.

## Prerequisites

- Site administrator permission for your Jira site
- Owner permission for a GitHub organization
- GitHub Enterprise Server running software version 2.19 or higher
- Firewall/gateway access configured (see below)

## Step 1: Set Up Your Server's Firewall

Your GitHub Enterprise Server must allow communication with Jira. There are two options:

### Option 1: Public-Facing URL with IP Allowlist
If your server has a public URL, configure the firewall to allow Atlassian IP addresses. Refer to [GitHub IP Allowlist Setup](https://github.com/atlassian/github-for-jira/blob/main/docs/ip-allowlist.md).

### Option 2: Locked Gateway (More Secure)
Create a secure gateway using the [sample reverse proxy configuration](https://github.com/atlassian/github-for-jira/blob/main/docs/sample-reverse-proxy-nginx.conf). You'll need:

- Server URL for the locked gateway
- HTTP request header name
- API key value

## Step 2: Install the GitHub for Atlassian App

1. In Jira, go to **Apps** > **Explore more apps**
2. Search for "GitHub for Atlassian"
3. Select the app and click **Get app** > **Get it now**

## Step 3: Connect GitHub Enterprise Server

1. After installation, select **Get started** (or **Apps** > **Manage your apps** > **GitHub for Atlassian**)
2. Click **Continue**
3. Select **GitHub Enterprise Server**, then **Next**
4. Enter your GitHub Enterprise Server URL in the format `http(s)://<your-domain>`
5. If using a locked gateway, enter the HTTP header name and API key
6. Click **Next**

## Step 4: Create a GitHub App

### Automatic Creation (Recommended)

1. Select **Automatic app creation**
2. You'll be redirected to GitHub to create the app
3. Give it a unique name and click **Create GitHub App**
4. Update the Homepage URL to include your app name at `http(s)://<your-domain>/settings/apps/<app-name>`

### Manual Creation
If automatic creation fails, manually create a GitHub App following the [manual setup guide](https://support.atlassian.com/jira-cloud-administration/docs/manually-create-a-github-app/).

## Step 5: Link Development Activity to Jira Work Items

To connect branches, commits, and PRs to Jira issues:

1. Find the Jira issue key (e.g., "PROJ-123")
2. Include the key in:
   - Branch names: `git checkout -b PROJ-123-feature-branch`
   - Commit messages: `git commit -m "PROJ-123: Implement feature"`
   - Pull request titles: Use the key in the PR title

## Migration from Legacy DVCS Connector

If using the old DVCS connector:

1. Ensure all organizations are connected to GitHub for Atlassian
2. Go to Jira Settings > Apps > DVCS Accounts
3. Disconnect legacy connections

## Troubleshooting

- Check [GitHub Enterprise Server Integration FAQ](https://support.atlassian.com/jira-cloud-administration/docs/github-enterprise-server-integration-faq/)
- Contact Atlassian Support if issues persist

## Additional Resources

- [GitHub for Atlassian App Documentation](https://support.atlassian.com/jira-cloud-administration/docs/use-the-github-for-jira-app/)
- [Link GitHub Workflows and Deployments](https://support.atlassian.com/jira-cloud-administration/docs/link-github-workflows-and-deployments-to-jira-issues/)
