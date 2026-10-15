# Security Policy

AgentGate may process prompts, model outputs, and tool traces that contain sensitive data.

- Never commit production traces or secrets to the repository.
- Use environment variables for provider credentials.
- Treat imported datasets as untrusted input.
- Keep tenant data isolated through database row-level security.

For security reports, open a private security advisory on the GitHub repository once the project is published.
