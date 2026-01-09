# A/B Testing Guide

## Overview

The SalesGPT system includes comprehensive A/B testing for both email variants and Apollo lead sourcing configurations. This guide explains how the system works and how to interpret results.

## Email A/B Testing

### Variant Dimensions

Email variants are tested across multiple dimensions:

1. **Subject Line Variants**
   - `competitor`: Mentions competitor by name
   - `question`: Opens with a question
   - `value`: Leads with value proposition
   - `curiosity`: Creates curiosity gap
   - `social`: Uses social proof
   - `urgency`: Creates urgency

2. **Body Structure**
   - `evidence`: Evidence-first (data-heavy)
   - `problem`: Problem-first (pain-focused)
   - `story`: Story-first (narrative)
   - `question`: Question-first (engagement)

3. **Evidence Level**
   - `full`: Complete competitive analysis with numbers
   - `minimal`: Light evidence, competitor name only
   - `none`: No evidence, value proposition only

4. **CTA Variants**
   - `direct`: Direct booking request
   - `soft`: Soft ask ("open to conversation?")
   - `value`: Value-first ("want to see audit?")
   - `two_step`: Two-step process ("reply for details")

5. **Personalization Level**
   - `high`: Full name, company, location
   - `medium`: Name and company
   - `low`: Generic greeting

6. **Email Length**
   - `short`: 50-75 words
   - `medium`: 100-150 words
   - `long`: 150+ words

### Variant Assignment

Variants are assigned using **consistent hashing** based on lead email address. This ensures:
- Same lead always gets same variant (reproducibility)
- Even distribution across variants
- Smart assignment based on ELM route:
  - **Central route** (high score): Evidence-heavy, logical variants
  - **Peripheral route** (low score): Simpler, social proof variants

### Variant Code Format

Variant codes follow this format:
```
{subject}-{body}-{evidence}-{cta}-{personalization}-{length}
```

Example: `competitor-evidence-full-direct-high-medium`

### Interpreting Results

**Key Metrics:**
- **Reply Rate**: % of emails that received replies
- **Positive Reply Rate**: % of replies that are positive (interested/curious)
- **Booking Rate**: % of emails that led to bookings
- **Close Rate**: % of emails that led to closed deals
- **Avg Time to Reply**: Average hours until reply received

**Best Practices:**
1. Wait for at least 50 emails per variant before making decisions
2. Look for statistical significance (use confidence intervals)
3. Consider context: high-value leads may perform differently
4. Test one dimension at a time for clearer insights

## Apollo A/B Testing

### Configuration Dimensions

Apollo search configurations test:

1. **Geography Strategy**
   - `city`: City-specific (e.g., "New York, NY")
   - `metro`: Metro area (e.g., "New York Metro")
   - `state`: State-wide
   - `multi`: Multiple cities

2. **Employee Range**
   - `micro`: 1-5 employees
   - `small`: 5-15 employees
   - `medium`: 15-50 employees
   - `large`: 50-200 employees
   - `mixed_sm`: 1-20 employees
   - `mixed_md`: 10-50 employees

3. **Title Strategy**
   - `c_level`: C-level only (CEO, CFO, COO)
   - `owners`: Owners only
   - `decision`: Decision makers (broad)
   - `broad`: All relevant titles
   - `medical`: Medical-specific titles

4. **Website Requirement**
   - `web`: Requires website
   - `noweb`: No website requirement

### Multi-Armed Bandit Algorithm

The system uses **Upper Confidence Bound (UCB)** algorithm to balance:
- **Exploration**: Testing under-sampled configs
- **Exploitation**: Using best-performing configs

**How it works:**
1. Each config gets a UCB score
2. UCB = success_rate + exploration_bonus
3. Config with highest UCB is selected
4. Exploration bonus decreases as sample size increases

### Config Code Format

Config codes follow this format:
```
{geography}-{employee_range}-{title_strategy}-{website}
```

Example: `city-small-decision-web`

### Interpreting Results

**Key Metrics:**
- **Leads Sourced**: Number of leads found
- **Avg Lead Score**: Average quality score (0-20)
- **Reply Rate**: % of leads that replied
- **Booking Rate**: % of leads that booked
- **Close Rate**: % of leads that closed
- **ROI**: Return on investment (revenue - cost) / cost

**Best Practices:**
1. Test at least 10 leads per config before comparing
2. Consider lead quality (score) vs. quantity
3. Balance between high-quality leads and volume
4. Monitor ROI, not just conversion rates

## Recommendations Engine

The system automatically generates recommendations based on:
- Variant performance (best email variants)
- Apollo config performance (best lead sources)
- Niche performance (best specialties/locations)

**Recommendation Types:**
- **High Priority**: Strong statistical evidence, large sample size
- **Medium Priority**: Good evidence, moderate sample size
- **Low Priority**: Weak evidence, small sample size

**Confidence Levels:**
- 95%+: Very confident (50+ samples)
- 75-95%: Confident (20-50 samples)
- 50-75%: Somewhat confident (10-20 samples)
- <50%: Low confidence (<10 samples)

## Best Practices

1. **Start Broad**: Test many variants/configs initially
2. **Wait for Significance**: Don't make decisions too early
3. **Consider Context**: High-value leads may need different approaches
4. **Monitor Continuously**: Performance can change over time
5. **Document Learnings**: Track what works for your specific niche

## Troubleshooting

**No A/B test data showing:**
- Ensure emails are being sent with variant codes
- Check that Apollo configs are being tagged
- Verify database has A/B testing columns

**Recommendations not appearing:**
- Need at least 10 samples per variant/config
- Check `MIN_SAMPLE_SIZE_FOR_RECOMMENDATIONS` setting
- Ensure metrics tracker has access to state manager

**Variants not assigned:**
- Check that `AB_TESTING_ENABLED=true` in settings
- Verify AB test manager is initialized in container
- Check lead characteristics (ELM route, score) are available

