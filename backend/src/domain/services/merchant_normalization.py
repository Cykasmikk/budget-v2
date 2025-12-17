from typing import List
import re

class MerchantNormalizationService:
    """
    Centralized service for normalizing and extracting merchant names from transaction descriptions.
    Ensures consistency across Analysis, AI Context, and Entity Resolution.
    """
    
    # Common prefixes to strip
    PREFIXES = ['PAYMENT', 'PAY', 'AUTH', 'PURCHASE', 'DEBIT', 'CREDIT', 'ONLINE', 'POS', 'TST*', 'SQ*']
    
    # Normalization Rules (Regex Pattern -> Canonical Name)
    # Order matters: specific to general
    NORMALIZATION_RULES = [
        (r"(?i)\b(aws|amazon web services)\b", "Amazon Web Services"),
        (r"(?i)\b(amzn|amazon)\b", "Amazon"),
        (r"(?i)\b(gcp|google cloud)\b", "Google Cloud Platform"),
        (r"(?i)\b(github)\b", "GitHub"),
        (r"(?i)\b(openai)\b", "OpenAI"),
        (r"(?i)\b(anthropic)\b", "Anthropic"),
        (r"(?i)\b(pagerduty)\b", "PagerDuty"),
        (r"(?i)\b(datadog)\b", "Datadog"),
        (r"(?i)\b(digitalocean|docean)\b", "DigitalOcean"),
        (r"(?i)\b(vercel)\b", "Vercel"),
        (r"(?i)\b(netlify)\b", "Netlify"),
        (r"(?i)\b(heroku)\b", "Heroku"),
        (r"(?i)\b(uber)\b", "Uber"),
        (r"(?i)\b(lyft)\b", "Lyft"),
        (r"(?i)\b(doordash)\b", "DoorDash"),
        (r"(?i)\b(starbucks)\b", "Starbucks"),
        (r"(?i)\b(slack)\b", "Slack"),
        (r"(?i)\b(zoom)\b", "Zoom"),
        (r"(?i)\b(notion)\b", "Notion"),
        (r"(?i)\b(jira|atlassian)\b", "Atlassian"),
        (r"(?i)\b(linear)\b", "Linear"),
        (r"(?i)\b(cursor)\b", "Cursor")
    ]

    @classmethod
    def normalize(cls, description: str) -> str:
        """
        Extracts and normalizes the merchant name from a description.
        """
        if not description:
            return "Unknown"
            
        desc = description.strip()
        
        # 1. Apply Specific Normalization Rules first
        for pattern, canonical in cls.NORMALIZATION_RULES:
            if re.search(pattern, desc):
                return canonical
        
        # 2. Generic Cleanup if no specific rule matched
        # Remove prefixes
        for prefix in cls.PREFIXES:
            if desc.upper().startswith(prefix):
                desc = desc[len(prefix):].strip()
        
        # Take first 2-3 words (heuristic), but be careful not to over-truncate
        # If it looks like a domain (foo.com), keep it
        if "." in desc and " " not in desc:
            return desc
            
        words = desc.split()
        if len(words) > 3:
             # Heuristic: Take first 3 words
             merchant = ' '.join(words[:3]).strip()
        else:
             merchant = desc
             
        return merchant.title() if merchant else "Unknown"
