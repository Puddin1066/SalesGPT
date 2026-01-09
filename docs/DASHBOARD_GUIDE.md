# Dashboard User Guide

## Overview

The Streamlit dashboard provides a comprehensive interface for:
- Manual email review and approval
- A/B test analytics
- Apollo lead sourcing optimization
- AI-powered recommendations

## Accessing the Dashboard

1. Start the dashboard:
   ```bash
   ./scripts/start_dashboard.sh
   ```

2. Open browser:
   ```
   http://localhost:8501
   ```

## Tab 1: Email Review

### Overview

The Email Review tab is your primary interface for reviewing and sending cold emails.

### Layout

**Left Panel (Queue):**
- List of leads pending review
- Current lead highlighted in green
- Shows lead name and score
- First 15 leads visible, scroll for more

**Center Panel (Email Preview):**
- Editable subject line
- Editable email body (large text area)
- Action buttons:
  - ✅ **APPROVE & SEND**: Send email immediately
  - ✏️ **SAVE EDIT**: Save changes without sending
  - ⏭️ **SKIP**: Skip this lead
  - 🗑️ **REJECT**: Reject this lead

**Right Panel (Context):**
- Lead details (name, company, location, specialty)
- Scoring information (lead score, ELM score, route)
- Evidence data (competitor, gap, multiplier)
- A/B test info (variant code, Apollo config)
- HubSpot link (if contact created)

### Workflow

1. **Review Email**: Check subject and body
2. **Edit if Needed**: Modify content directly
3. **Take Action**:
   - **Approve**: Send email and move to next
   - **Skip**: Move to next without sending
   - **Reject**: Remove from queue
   - **Save Edit**: Keep changes, review later

### Keyboard Shortcuts

- **Enter**: Approve and send (when focused on email)
- **E**: Edit mode
- **S**: Skip
- **R**: Reject

### Bulk Actions

- **Approve Top 10**: Quickly approve and send next 10 emails
- **Skip Top 10**: Skip next 10 leads

### Tips

- Review high-score leads first (sorted by score)
- Edit emails to add personal touches
- Use bulk actions for high-confidence emails
- Check evidence panel for competitor context

## Tab 2: Email Analytics

### Overview

The Email Analytics tab shows A/B test results and performance metrics.

### Key Metrics

**Top Cards:**
- **Emails Sent**: Total emails sent
- **Reply Rate**: % that received replies
- **Booking Rate**: % that led to bookings
- **Close Rate**: % that led to closed deals

### Variant Performance Table

Shows performance for each email variant:
- Variant code
- Sent count
- Reply rate
- Positive reply rate
- Booking rate
- Close rate

**Sorting**: Automatically sorted by booking rate (best first)

### Conversion Funnel

Visual funnel chart showing:
- Sent → Replied → Positive → Booked → Closed

Compare top 5 variants side-by-side.

### Niche Performance

Analyze performance by:
- **Specialty**: Medical specialty
- **Location**: Geographic location
- **Score Tier**: Lead quality tier (A/B/C)
- **ELM Route**: Central vs. peripheral

**Visualization**: Bar chart comparing reply/booking/close rates

### Time Range Selector

Filter data by time period:
- 7 days
- 14 days
- 30 days (default)
- 60 days
- 90 days

## Tab 3: Apollo A/B Testing

### Overview

The Apollo A/B Testing tab shows lead sourcing optimization results.

### Overview Metrics

- **Total Configs**: Number of Apollo configurations being tested
- **Tested**: Configs with 10+ leads
- **Pending**: Configs not yet tested

### Performance Report

Table showing each Apollo config:
- Config code
- Geography strategy
- Employee range
- Title strategy
- Leads sourced
- Average lead score
- Reply rate
- Booking rate
- Close rate
- ROI

**Sorting**: Automatically sorted by ROI (best first)

### Visualizations

1. **ROI by Employee Range**: Bar chart showing ROI for each employee range strategy
2. **Booking Rate by Title Strategy**: Bar chart showing booking rates for each title filter
3. **Lead Quality vs Close Rate**: Scatter plot showing relationship between lead quality and conversion

### Interpreting Results

- **High ROI + High Quality**: Best configs (use more)
- **High ROI + Low Quality**: Good volume, lower quality (test more)
- **Low ROI**: Poor performers (test less or remove)

## Tab 4: Optimization

### Overview

The Optimization tab provides AI-powered recommendations for improving performance.

### Recommendations

Each recommendation shows:
- **Priority**: High/Medium/Low
- **Type**: Email variant / Apollo config / Niche
- **Description**: What the recommendation is about
- **Action**: Recommended action to take
- **Confidence**: Statistical confidence level

### Applying Recommendations

- **Email Variants**: Click "Apply" to increase variant usage
- **Apollo Configs**: Manually adjust config selection
- **Niches**: Use targeting controls below

### Manual Optimization Controls

**Target Niche Selection:**
- Select specialties to focus on
- Set minimum lead score threshold
- Click "Apply Targeting" to update

**Variant Distribution:**
- Adjust A/B test variant allocation
- (Feature available after more data collected)

### Best Practices

1. **Wait for Data**: Don't make changes too early
2. **Test Incrementally**: Make small changes, measure impact
3. **Consider Context**: Recommendations are general, adapt to your needs
4. **Monitor Results**: Check back after applying changes

## Troubleshooting

**Dashboard won't load:**
- Check that database exists and is accessible
- Verify all services are initialized correctly
- Check console for error messages

**No data showing:**
- Ensure background worker is running
- Check that emails have been sent
- Verify database has A/B testing columns

**Recommendations not appearing:**
- Need at least 10 samples per variant/config
- Check time range selector (may be too narrow)
- Ensure metrics tracker has data

**Email review queue empty:**
- Start background queue builder: `python scripts/start_queue_builder.py`
- Check queue refill threshold setting
- Verify Apollo API is working

## Tips for Maximum Efficiency

1. **Use Bulk Actions**: Approve top-scoring leads in batches
2. **Focus on High ROI**: Prioritize configs/niches with best ROI
3. **Edit Strategically**: Only edit emails that need personalization
4. **Monitor Trends**: Check analytics regularly to spot patterns
5. **Apply Recommendations**: Use AI recommendations to optimize continuously

