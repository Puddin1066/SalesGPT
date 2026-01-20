"""
Helper to fix Supabase connection string by removing pgbouncer parameter.
"""

from urllib.parse import urlparse, urlencode, parse_qs, urlunparse


def fix_supabase_url(url: str) -> str:
    """
    Remove pgbouncer parameter from Supabase connection string.
    Also handles URL encoding if needed.
    """
    if not url:
        return url
    
    # Remove pgbouncer parameter
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    query_params.pop('pgbouncer', None)
    new_query = urlencode(query_params, doseq=True)
    
    # Reconstruct URL
    new_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))
    
    return new_url

