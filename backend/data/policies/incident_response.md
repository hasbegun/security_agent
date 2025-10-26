# Incident Response Escalation Path

## Objective
Define the escalation path for security incidents, especially those affecting production systems.

## P1: Production Outage / Security Breach
1.  **Immediate Contact:** Call the on-call Security Incident Response Team (SIRT) lead at +1-800-555-1234 (this is a 24/7 hotline).
2.  **Internal Comms:** The SIRT lead will create a `#security-incident-channel` in Slack.
3.  **Stakeholders:** The SIRT lead is responsible for notifying the Head of Engineering and the CTO within 15 minutes.
4.  **Engineering:** The on-call SRE is paged to assist SIRT in containment.

## P2: System Misconfiguration (Non-Outage)
1.  **Report:** Create a JIRA ticket and assign it to the 'Security' project.
2.  **Notify:** Post a link to the JIRA ticket in the `#security-help` Slack channel.
3.  **SLA:** The security team will triage P2 tickets within 4 business hours.