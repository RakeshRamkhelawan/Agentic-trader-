"""White-label customization for tenants."""

from dataclasses import dataclass
from typing import Any


@dataclass
class BrandingConfig:
    """White-label branding configuration."""

    # Basic branding
    company_name: str = "Agentic Trader"
    logo_url: str | None = None
    favicon_url: str | None = None

    # Colors
    primary_color: str = "#4F46E5"  # Indigo 600
    secondary_color: str = "#10B981"  # Emerald 500
    accent_color: str = "#F59E0B"  # Amber 500
    background_color: str = "#0F172A"  # Slate 900
    text_color: str = "#F8FAFC"  # Slate 50

    # Typography
    font_family: str = "Inter, system-ui, sans-serif"
    font_heading: str | None = None

    # Custom domain
    custom_domain: str | None = None
    ssl_enabled: bool = True

    # Content
    custom_css: str | None = None
    custom_js: str | None = None
    footer_text: str | None = None
    terms_url: str | None = None
    privacy_url: str | None = None

    # Features visibility
    show_powered_by: bool = True
    show_support_link: bool = True
    enable_feedback: bool = True

    # Email branding
    email_sender_name: str = "Agentic Trader"
    email_sender_address: str = "noreply@example.com"
    email_logo_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "company_name": self.company_name,
            "logo_url": self.logo_url,
            "favicon_url": self.favicon_url,
            "colors": {
                "primary": self.primary_color,
                "secondary": self.secondary_color,
                "accent": self.accent_color,
                "background": self.background_color,
                "text": self.text_color,
            },
            "typography": {
                "font_family": self.font_family,
                "font_heading": self.font_heading,
            },
            "domain": {
                "custom_domain": self.custom_domain,
                "ssl_enabled": self.ssl_enabled,
            },
            "content": {
                "footer_text": self.footer_text,
                "terms_url": self.terms_url,
                "privacy_url": self.privacy_url,
            },
            "features": {
                "show_powered_by": self.show_powered_by,
                "show_support_link": self.show_support_link,
                "enable_feedback": self.enable_feedback,
            },
            "email": {
                "sender_name": self.email_sender_name,
                "sender_address": self.email_sender_address,
                "logo_url": self.email_logo_url,
            },
        }

    def get_css_variables(self) -> str:
        """Generate CSS variables for theming."""
        return f"""
        :root {{
            --brand-primary: {self.primary_color};
            --brand-secondary: {self.secondary_color};
            --brand-accent: {self.accent_color};
            --brand-bg: {self.background_color};
            --brand-text: {self.text_color};
            --brand-font: {self.font_family};
        }}
        """


class WhiteLabelManager:
    """
    Manages white-label branding for tenants.

    Features:
    - Custom branding per tenant
    - Custom domain support
    - Theme customization
    - CSS/JS injection
    """

    def __init__(self):
        self._branding: dict[str, BrandingConfig] = {}  # tenant_id -> config
        self._default_branding = BrandingConfig()

    def set_branding(self, tenant_id: str, config: BrandingConfig) -> None:
        """Set branding configuration for tenant."""
        self._branding[tenant_id] = config

    def get_branding(self, tenant_id: str) -> BrandingConfig:
        """Get branding configuration for tenant."""
        return self._branding.get(tenant_id, self._default_branding)

    def update_branding(self, tenant_id: str, **kwargs) -> BrandingConfig | None:
        """Update specific branding fields."""
        config = self._branding.get(tenant_id)
        if not config:
            # Create new based on defaults
            config = BrandingConfig()
            self._branding[tenant_id] = config

        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config

    def validate_custom_domain(self, domain: str) -> tuple:
        """
        Validate custom domain configuration.

        Returns:
            (is_valid: bool, message: str, dns_records: list)
        """
        import re

        # Basic domain validation
        domain_pattern = r"^[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z0-9][-a-zA-Z0-9.]*$"
        if not re.match(domain_pattern, domain):
            return False, "Invalid domain format", []

        # In production, verify DNS records
        required_records = [
            {
                "type": "CNAME",
                "name": domain,
                "value": "platform.example.com",
                "ttl": 3600,
            }
        ]

        return True, "Domain validation passed", required_records

    def get_tenant_by_domain(self, domain: str) -> str | None:
        """Find tenant ID by custom domain."""
        for tenant_id, config in self._branding.items():
            if config.custom_domain and config.custom_domain.lower() == domain.lower():
                return tenant_id
        return None

    def generate_html_template(self, tenant_id: str, content: str) -> str:
        """Generate HTML page with tenant branding."""
        config = self.get_branding(tenant_id)

        css_vars = config.get_css_variables()
        custom_css = f"<style>{config.custom_css}</style>" if config.custom_css else ""
        custom_js = f"<script>{config.custom_js}</script>" if config.custom_js else ""

        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config.company_name}</title>
    {f'<link rel="icon" href="{config.favicon_url}">' if config.favicon_url else ""}
    <style>
        {css_vars}
        body {{
            font-family: var(--brand-font);
            background-color: var(--brand-bg);
            color: var(--brand-text);
            margin: 0;
            padding: 0;
        }}
    </style>
    {custom_css}
</head>
<body>
    {f'<header><img src="{config.logo_url}" alt="{config.company_name}"></header>' if config.logo_url else ""}
    <main>
        {content}
    </main>
    {f'<footer>{config.footer_text}</footer>' if config.footer_text else ""}
    {custom_js}
</body>
</html>
"""

    def get_email_template(
        self,
        tenant_id: str,
        subject: str,
        body: str,
        action_url: str | None = None,
        action_text: str | None = None,
    ) -> dict[str, str]:
        """Generate branded email template."""
        config = self.get_branding(tenant_id)

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; background: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 40px; }}
        .logo {{ text-align: center; margin-bottom: 30px; }}
        .content {{ line-height: 1.6; }}
        .button {{ display: inline-block; padding: 12px 24px; background: {config.primary_color}; color: white; text-decoration: none; border-radius: 4px; }}
        .footer {{ margin-top: 40px; font-size: 12px; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        {f'<div class="logo"><img src="{config.email_logo_url}" alt="{config.company_name}" width="200"></div>' if config.email_logo_url else f'<h1>{config.company_name}</h1>'}
        <div class="content">
            {body}
            {f'<p><a href="{action_url}" class="button">{action_text}</a></p>' if action_url and action_text else ""}
        </div>
        <div class="footer">
            <p>This email was sent by {config.email_sender_name}</p>
            {config.footer_text or ""}
        </div>
    </div>
</body>
</html>
"""

        return {
            "subject": f"[{config.company_name}] {subject}",
            "from": f"{config.email_sender_name} <{config.email_sender_address}>",
            "html": html_content,
            "text": body,  # Plain text version
        }


# Global white-label manager
white_label_manager = WhiteLabelManager()
