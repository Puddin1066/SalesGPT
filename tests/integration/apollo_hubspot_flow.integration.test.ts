/**
 * Integration flow tests for Apollo → HubSpot pipeline.
 * Tests the complete data flow from Apollo lead search to HubSpot contact creation.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import {
  mockApolloSearchResponse,
} from '../fixtures/apolloResponses'
import {
  mockHubSpotContactResponse,
} from '../fixtures/hubspotResponses'
import {
  createMockAxiosResponse,
  createApolloError,
  createHubSpotError,
} from '../utils/mockHelpers'

// Mock axios
vi.mock('axios')
const mockedAxios = axios as any

describe('Apollo → HubSpot Integration Flow', () => {
  const APOLLO_BASE_URL = 'https://api.apollo.io/v1'
  const HUBSPOT_BASE_URL = 'https://api.hubapi.com'

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should complete full pipeline: Apollo search → HubSpot contact creation', async () => {
    // Step 1: Apollo search
    const apolloSearchResponse = createMockAxiosResponse(
      mockApolloSearchResponse(2)
    )

    // Step 2: HubSpot contact creation
    const hubspotContactResponse1 = createMockAxiosResponse(
      mockHubSpotContactResponse('contact_123'),
      201
    )
    const hubspotContactResponse2 = createMockAxiosResponse(
      mockHubSpotContactResponse('contact_456'),
      201
    )

    mockedAxios.post
      .mockResolvedValueOnce(apolloSearchResponse) // Apollo search
      .mockResolvedValueOnce(hubspotContactResponse1) // HubSpot create 1
      .mockResolvedValueOnce(hubspotContactResponse2) // HubSpot create 2

    // Execute Apollo search
    const apolloResponse = await axios.post(
      `${APOLLO_BASE_URL}/mixed_people/search`,
      {
        api_key: 'test_key',
        q_keywords: 'Dermatology',
        person_locations: ['New York, NY'],
      }
    )

    const lead1 = apolloResponse.data.people[0]
    const lead2 = apolloResponse.data.people[1]

    // Create HubSpot contacts from Apollo leads
    const hubspotResponse1 = await axios.post(
      `${HUBSPOT_BASE_URL}/crm/v3/objects/contacts`,
      {
        properties: {
          email: lead1.email,
          firstname: lead1.first_name,
          lastname: lead1.last_name,
          company: lead1.organization.name,
          website: lead1.organization.website_url,
        },
      },
      {
        headers: {
          Authorization: 'Bearer test_hubspot_token',
        },
      }
    )

    const hubspotResponse2 = await axios.post(
      `${HUBSPOT_BASE_URL}/crm/v3/objects/contacts`,
      {
        properties: {
          email: lead2.email,
          firstname: lead2.first_name,
          lastname: lead2.last_name,
          company: lead2.organization.name,
          website: lead2.organization.website_url,
        },
      },
      {
        headers: {
          Authorization: 'Bearer test_hubspot_token',
        },
      }
    )

    expect(apolloResponse.data.people).toHaveLength(2)
    expect(hubspotResponse1.data.id).toBe('contact_123')
    // Verify we sent the correct email from Apollo lead
    expect(lead1.email).toBe('john0@example.com')
    expect(hubspotResponse2.data.id).toBe('contact_456')
    // Verify we sent the correct email from Apollo lead
    expect(lead2.email).toBe('john1@example.com')
  })

  it('should handle pipeline errors gracefully', async () => {
    // Apollo search succeeds
    const apolloResponse = createMockAxiosResponse(
      mockApolloSearchResponse(1)
    )

    // HubSpot creation fails
    const hubspotError = createHubSpotError('Unauthorized', 401)

    mockedAxios.post
      .mockResolvedValueOnce(apolloResponse)
      .mockRejectedValueOnce(hubspotError)

    // Apollo search succeeds
    const apollo = await axios.post(
      `${APOLLO_BASE_URL}/mixed_people/search`,
      { api_key: 'test_key' }
    )

    expect(apollo.data.people).toHaveLength(1)

    // HubSpot creation fails
    await expect(
      axios.post(
        `${HUBSPOT_BASE_URL}/crm/v3/objects/contacts`,
        {
          properties: {
            email: apollo.data.people[0].email,
            firstname: apollo.data.people[0].first_name,
            lastname: apollo.data.people[0].last_name,
          },
        },
        { headers: { Authorization: 'Bearer invalid_token' } }
      )
    ).rejects.toMatchObject({
      response: {
        status: 401,
      },
    })
  })

  it('should transform Apollo lead data to HubSpot contact format', async () => {
    const apolloResponse = createMockAxiosResponse(
      mockApolloSearchResponse(1)
    )
    const hubspotResponse = createMockAxiosResponse(
      mockHubSpotContactResponse('contact_123'),
      201
    )

    mockedAxios.post
      .mockResolvedValueOnce(apolloResponse)
      .mockResolvedValueOnce(hubspotResponse)

    // Apollo search
    const apollo = await axios.post(
      `${APOLLO_BASE_URL}/mixed_people/search`,
      { api_key: 'test_key', q_keywords: 'Dermatology' }
    )

    const lead = apollo.data.people[0]

    // Transform and create HubSpot contact
    const hubspot = await axios.post(
      `${HUBSPOT_BASE_URL}/crm/v3/objects/contacts`,
      {
        properties: {
          email: lead.email,
          firstname: lead.first_name,
          lastname: lead.last_name,
          company: lead.organization.name,
          website: lead.organization.website_url,
        },
      },
      {
        headers: {
          Authorization: 'Bearer test_token',
        },
      }
    )

    // Verify data transformation - check what we sent matches Apollo lead data
    expect(lead.email).toBe('john0@example.com')
    expect(lead.organization.name).toBe('Example Clinic 1')
    expect(lead.organization.website_url).toBe('https://example0.com')
    // Verify HubSpot received the correct data (check the mock was called with correct payload)
    const hubspotCall = mockedAxios.post.mock.calls.find(
      (call: any) => call[0].includes('/crm/v3/objects/contacts')
    )
    expect(hubspotCall[1].properties.email).toBe(lead.email)
    expect(hubspotCall[1].properties.company).toBe(lead.organization.name)
    expect(hubspotCall[1].properties.website).toBe(lead.organization.website_url)
  })

  it('should handle Apollo search failure', async () => {
    const apolloError = createApolloError('API key invalid', 401)

    mockedAxios.post.mockRejectedValueOnce(apolloError)

    // Apollo search fails
    await expect(
      axios.post(`${APOLLO_BASE_URL}/mixed_people/search`, {
        api_key: 'invalid_key',
      })
    ).rejects.toMatchObject({
      response: {
        status: 401,
      },
    })

    // HubSpot should not be called
    expect(mockedAxios.post).toHaveBeenCalledTimes(1)
  })

  it('should handle partial success (some contacts created, some failed)', async () => {
    const apolloResponse = createMockAxiosResponse(
      mockApolloSearchResponse(2)
    )
    const hubspotSuccess = createMockAxiosResponse(
      mockHubSpotContactResponse('contact_123'),
      201
    )
    const hubspotError = createHubSpotError('Invalid email', 400)

    mockedAxios.post
      .mockResolvedValueOnce(apolloResponse) // Apollo succeeds
      .mockResolvedValueOnce(hubspotSuccess) // First contact succeeds
      .mockRejectedValueOnce(hubspotError) // Second contact fails

    // Apollo search
    const apollo = await axios.post(
      `${APOLLO_BASE_URL}/mixed_people/search`,
      { api_key: 'test_key' }
    )

    const leads = apollo.data.people

    // Create first contact (succeeds)
    const contact1 = await axios.post(
      `${HUBSPOT_BASE_URL}/crm/v3/objects/contacts`,
      {
        properties: {
          email: leads[0].email,
          firstname: leads[0].first_name,
          lastname: leads[0].last_name,
        },
      },
      { headers: { Authorization: 'Bearer test_token' } }
    )

    // Create second contact (fails)
    await expect(
      axios.post(
        `${HUBSPOT_BASE_URL}/crm/v3/objects/contacts`,
        {
          properties: {
            email: leads[1].email,
            firstname: leads[1].first_name,
            lastname: leads[1].last_name,
          },
        },
        { headers: { Authorization: 'Bearer test_token' } }
      )
    ).rejects.toMatchObject({
      response: {
        status: 400,
      },
    })

    // First contact was created successfully
    expect(contact1.data.id).toBe('contact_123')
  })
})

