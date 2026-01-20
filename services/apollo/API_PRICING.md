# Apollo API Pricing & Credit Usage

This document outlines Apollo API credit consumption for the SalesGPT integration.

## Reference
- [Apollo API Pricing Documentation](https://docs.apollo.io/docs/api-pricing)
- [Track API Usage](https://docs.apollo.io/docs/create-api-keys#track-api-usage) (login required)

## Credit-Consuming Endpoints

### Search Endpoints
The following search endpoints consume credits:

1. **Organization Search** (`v1/mixed_companies/search`)
   - Used for: Searching for companies/organizations
   - Credit consumption: Varies by plan

2. **Organization Job Postings** (`/v1/organizations/{organization_id}/job_postings`)
   - Used for: Retrieving job postings for an organization
   - Credit consumption: Varies by plan

3. **Complete Organization Info** (`/v1/organizations/{id}`)
   - Used for: Getting detailed organization information
   - Credit consumption: Varies by plan

4. **News Articles** (`/v1/news_articles/search`)
   - Used for: Searching news articles
   - Credit consumption: Varies by plan

### Enrichment Endpoints
The following enrichment endpoints **definitely consume credits**:

1. **People Enrichment** (`v1/people/match`)
   - Used by: `ApolloAgent.enrich_person()`
   - Credit consumption: **1 credit per match**
   - Use case: Enrich a single person's data

2. **Bulk People Enrichment** (`v1/people/bulk_match`)
   - Used by: `ApolloAgent.bulk_enrich_people()`
   - Credit consumption: **1 credit per person matched**
   - Use case: Enrich multiple people at once

3. **Organization Enrichment** (`v1/organizations/enrich`)
   - Used by: `ApolloAgent.enrich_organization()`
   - Credit consumption: **1 credit per enrichment**
   - Use case: Enrich a single organization's data

4. **Bulk Organization Enrichment** (`v1/organizations/bulk_enrich`)
   - Used by: `ApolloAgent.bulk_enrich_organizations()`
   - Credit consumption: **1 credit per organization enriched**
   - Use case: Enrich multiple organizations at once

## Non-Credit Endpoints (Plan Dependent)

### People Search
- **Endpoint**: `v1/mixed_people/search`
- **Used by**: `ApolloAgent.search_leads()`
- **Credit consumption**: May or may not consume credits depending on your Apollo plan
- **Note**: Check your specific Apollo plan details to confirm credit usage

## Usage in SalesGPT

### Current Implementation

The main `search_leads()` method uses `v1/mixed_people/search`, which may or may not consume credits depending on your plan.

### Enrichment Methods

The following methods are available for explicit enrichment (these **definitely consume credits**):

```python
from services.apollo import ApolloAgent

apollo = ApolloAgent()

# Enrich a single person (1 credit)
person_data = apollo.enrich_person(
    email="john@example.com",
    first_name="John",
    last_name="Doe"
)

# Enrich a single organization (1 credit)
org_data = apollo.enrich_organization(domain="example.com")

# Bulk enrich people (1 credit per person)
people_data = apollo.bulk_enrich_people([
    {"email": "john@example.com", "first_name": "John"},
    {"email": "jane@example.com", "first_name": "Jane"}
])

# Bulk enrich organizations (1 credit per organization)
orgs_data = apollo.bulk_enrich_organizations([
    {"domain": "example.com"},
    {"name": "Acme Corp"}
])

# Enrich a lead (2 credits: 1 for person + 1 for organization)
enriched_lead = apollo.enrich_lead(lead)
```

## Credit Tracking

To track your organization's credit usage:

1. Log into your Apollo account
2. Navigate to API settings
3. View the "Track API Usage" section
4. Monitor credit consumption in real-time

## Error Handling

The Apollo agent includes enhanced error handling for credit-related issues:

- **402 Payment Required**: Indicates insufficient credits or payment issue
- **429 Rate Limit Exceeded**: Too many requests, wait before retrying
- **401 Unauthorized**: Invalid or expired API key

All methods log warnings when credit-related errors occur.

## Best Practices

1. **Monitor Credit Usage**: Regularly check your Apollo dashboard for credit consumption
2. **Use Bulk Operations**: When enriching multiple records, use bulk endpoints for efficiency
3. **Cache Results**: Store enriched data to avoid re-enriching the same records
4. **Plan Ahead**: Understand your Apollo plan's credit allocation before running large batches
5. **Error Handling**: Always handle 402 (payment required) errors gracefully in production

## Cost Estimation

Example cost scenarios:

- **100 leads searched**: Check your plan (may or may not consume credits)
- **100 people enriched**: 100 credits (1 per person)
- **100 organizations enriched**: 100 credits (1 per organization)
- **100 leads fully enriched** (person + org): 200 credits

Always verify current pricing with Apollo's official documentation and your plan details.



