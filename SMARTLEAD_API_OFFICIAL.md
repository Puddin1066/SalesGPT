# Smartlead API - Official Documentation Reference

Based on the [official Smartlead API documentation](https://helpcenter.smartlead.ai/en/articles/125-full-api-documentation), this document provides the correct implementation details.

## ✅ Key Findings from Official Docs

### Authentication
- **Method**: Query parameter `?api_key=YOUR_API_KEY`
- **Base URL**: `https://server.smartlead.ai/api/v1`
- **Rate Limit**: **10 requests every 2 seconds** (not 60 per 60 seconds)

### Campaign Creation ✅ FIXED

**Correct Endpoint**: `POST /campaigns/create` (not `/campaigns`)

**Request Format**:
```json
{
  "name": "Campaign Name",
  "client_id": null  // or client ID if attached to client
}
```

**Response Format**:
```json
{
  "ok": true,
  "id": 3023,
  "name": "Campaign Name",
  "created_at": "2022-11-07T16:23:24.025929+00:00"
}
```

**Status**: ✅ **WORKING** - Campaign creation now works via API!

### Adding Leads

**Endpoint**: `POST /campaigns/{campaign_id}/leads`

**Lead Format** (per official docs):
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "[email protected]",
  "phone_number": "1234567890",
  "company_name": "Company Name",
  "website": "example.com",
  "location": "City, State",
  "custom_fields": {
    "Title": "Regional Manager",
    "First_Line": "Custom message"
  },
  "linkedin_profile": "https://linkedin.com/in/johndoe",
  "company_url": "example.com"
}
```

**Note**: Leads are added individually (one per request), not in batch arrays.

### Adding Sequences

**Endpoint**: `POST /campaigns/{campaign_id}/sequences`

**Sequence Format**:
```json
{
  "subject": "Email Subject",
  "body": "Email body with {{template_fields}}",
  "delay_days": 0
}
```

### Getting Campaign Info

**Endpoint**: `GET /campaigns/{campaign_id}`

Returns full campaign details including:
- Status (DRAFTED/ACTIVE/COMPLETED/STOPPED/PAUSED)
- Schedule settings
- Track settings
- Stop lead settings
- And more

### Updating Campaign Settings

**Endpoint**: `POST /campaigns/{campaign_id}/settings`

Can update:
- `track_settings`: ["DONT_TRACK_EMAIL_OPEN", "DONT_TRACK_LINK_CLICK", "DONT_TRACK_REPLY_TO_AN_EMAIL"]
- `stop_lead_settings`: "REPLY_TO_AN_EMAIL" | "CLICK_ON_A_LINK" | "OPEN_AN_EMAIL"
- `unsubscribe_text`
- `send_as_plain_text`
- `follow_up_percentage` (0-100)
- `client_id`
- `enable_ai_esp_matching`

### Updating Campaign Schedule

**Endpoint**: `POST /campaigns/{campaign_id}/schedule`

**Schedule Format**:
```json
{
  "timezone": "America/Los_Angeles",
  "days_of_the_week": [1, 2, 3, 4, 5],
  "start_hour": "09:00",
  "end_hour": "18:00",
  "min_time_btw_emails": 10,
  "max_new_leads_per_day": 20,
  "schedule_start_time": "2023-04-25T07:29:25.978Z"
}
```

### Webhooks

**Get Webhooks**: `GET /campaigns/{campaign_id}/webhooks`

**Add/Update Webhook**: `POST /campaigns/{campaign_id}/webhooks`

**Webhook Event Types**:
- `EMAIL_SENT`
- `EMAIL_OPEN`
- `EMAIL_LINK_CLICK`
- `EMAIL_REPLY`
- `LEAD_UNSUBSCRIBED`
- `LEAD_CATEGORY_UPDATED`

### Lead Status Values

- `STARTED`: Lead scheduled, hasn't received 1st email
- `COMPLETED`: Lead received all emails in sequence
- `BLOCKED`: Email bounced or lead in global block list
- `INPROGRESS`: Lead has received at least one email

---

## 🔧 Updated Implementation

### Fixed in `services/outbound/smartlead_agent.py`

1. ✅ **Campaign Creation**
   - Changed endpoint from `/campaigns` to `/campaigns/create`
   - Updated payload to match official format
   - Fixed response parsing (uses `id` not `campaign_id`)

2. ✅ **Authentication**
   - Already using query parameters (correct)
   - All endpoints use `?api_key=...`

3. ⚠️ **Adding Leads**
   - Updated to add leads individually (per API docs)
   - Note: May need optimization for bulk operations

---

## 📊 Rate Limits

**Official Rate Limit**: 10 requests every 2 seconds

This is more restrictive than previously thought. Implement:
- Request throttling (max 5 requests/second)
- Batch operations where possible
- Monitor rate limit headers if available

---

## 🚀 Next Steps

1. ✅ **Campaign Creation** - Now working via API!
2. ⏳ **Test Adding Sequences** - Verify endpoint works
3. ⏳ **Test Adding Leads** - Verify individual lead addition
4. ⏳ **Update Campaign Settings** - Set from_email, from_name, etc.
5. ⏳ **Configure Webhooks** - Set up reply handling

---

## 📚 Reference

- **Official Docs**: https://helpcenter.smartlead.ai/en/articles/125-full-api-documentation
- **Base URL**: `https://server.smartlead.ai/api/v1`
- **Authentication**: Query parameter `?api_key=YOUR_API_KEY`

---

**Last Updated**: January 18, 2026  
**Status**: ✅ Campaign creation working via API!

