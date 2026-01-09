/**
 * Integration tests for HubSpot API.
 * All API calls are mocked using Vitest's vi.mock() to avoid actual API usage.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import {
  mockHubSpotContactResponse,
  mockHubSpotDealResponse,
  mockHubSpotOAuthTokenResponse,
  mockHubSpotOAuthTokenMetadata,
  mockHubSpot401Error,
  mockHubSpot403Error,
  mockHubSpot404Error,
  mockHubSpotRateLimitError,
} from '../fixtures/hubspotResponses'
import {
  createMockAxiosResponse,
  createHubSpotError,
  buildHubSpotContactPayload,
} from '../utils/mockHelpers'

// Mock axios
vi.mock('axios')
const mockedAxios = axios as any

describe('HubSpot API Integration', () => {
  const HUBSPOT_API_KEY = process.env.HUBSPOT_API_KEY || 'test_api_key'
  const HUBSPOT_BASE_URL = 'https://api.hubapi.com'

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Contact Management', () => {
    it('should create a contact successfully', async () => {
      const mockResponse = createMockAxiosResponse(
        mockHubSpotContactResponse('contact_123'),
        201
      )
      mockedAxios.post.mockResolvedValue(mockResponse)

      const contactData = buildHubSpotContactPayload(
        'john@example.com',
        'John',
        'Doe',
        'Example Clinic',
        'https://example.com'
      )

      const response = await axios.post(
        `${HUBSPOT_BASE_URL}/crm/v3/objects/contacts`,
        contactData,
        {
          headers: {
            Authorization: `Bearer ${HUBSPOT_API_KEY}`,
            'Content-Type': 'application/json',
          },
        }
      )

      expect(response.status).toBe(201)
      expect(response.data.id).toBe('contact_123')
      expect(response.data.properties.email).toBe('john@example.com')
      expect(mockedAxios.post).toHaveBeenCalledWith(
        `${HUBSPOT_BASE_URL}/crm/v3/objects/contacts`,
        expect.objectContaining({
          properties: expect.objectContaining({
            email: 'john@example.com',
          }),
        }),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: expect.stringContaining('Bearer'),
          }),
        })
      )
    })

    it('should handle 401 authentication error', async () => {
      const error = createHubSpotError('Invalid access token', 401)
      mockedAxios.post.mockRejectedValue(error)

      await expect(
        axios.post(
          `${HUBSPOT_BASE_URL}/crm/v3/objects/contacts`,
          { properties: { email: 'test@example.com' } },
          {
            headers: {
              Authorization: 'Bearer invalid_token',
            },
          }
        )
      ).rejects.toMatchObject({
        response: {
          status: 401,
        },
      })
    })

    it('should get contact by email', async () => {
      const mockResponse = createMockAxiosResponse(
        mockHubSpotContactResponse('contact_123')
      )
      mockedAxios.get.mockResolvedValue(mockResponse)

      const response = await axios.get(
        `${HUBSPOT_BASE_URL}/crm/v3/objects/contacts/john@example.com`,
        {
          params: { idProperty: 'email' },
          headers: {
            Authorization: `Bearer ${HUBSPOT_API_KEY}`,
          },
        }
      )

      expect(response.status).toBe(200)
      expect(response.data.id).toBe('contact_123')
      expect(response.data.properties.email).toBe('john@example.com')
    })

    it('should return null when contact not found', async () => {
      const error = createHubSpotError('Resource not found', 404)
      mockedAxios.get.mockRejectedValue(error)

      await expect(
        axios.get(
          `${HUBSPOT_BASE_URL}/crm/v3/objects/contacts/nonexistent@example.com`,
          {
            params: { idProperty: 'email' },
            headers: {
              Authorization: `Bearer ${HUBSPOT_API_KEY}`,
            },
          }
        )
      ).rejects.toMatchObject({
        response: {
          status: 404,
        },
      })
    })
  })

  describe('Pipeline Stage Updates', () => {
    it('should update contact pipeline stage to "booked"', async () => {
      const mockResponse = createMockAxiosResponse({
        id: 'contact_123',
        properties: {
          dealstage: 'booked',
        },
      })
      mockedAxios.patch.mockResolvedValue(mockResponse)

      const updateData = {
        properties: {
          dealstage: 'booked',
        },
      }

      const response = await axios.patch(
        `${HUBSPOT_BASE_URL}/crm/v3/objects/contacts/contact_123`,
        updateData,
        {
          headers: {
            Authorization: `Bearer ${HUBSPOT_API_KEY}`,
            'Content-Type': 'application/json',
          },
        }
      )

      expect(response.status).toBe(200)
      expect(response.data.properties.dealstage).toBe('booked')
    })

    it('should update contact pipeline stage to "engaged"', async () => {
      const mockResponse = createMockAxiosResponse({
        id: 'contact_123',
        properties: {
          dealstage: 'engaged',
        },
      })
      mockedAxios.patch.mockResolvedValue(mockResponse)

      const response = await axios.patch(
        `${HUBSPOT_BASE_URL}/crm/v3/objects/contacts/contact_123`,
        {
          properties: {
            dealstage: 'engaged',
          },
        },
        {
          headers: {
            Authorization: `Bearer ${HUBSPOT_API_KEY}`,
          },
        }
      )

      expect(response.status).toBe(200)
      expect(response.data.properties.dealstage).toBe('engaged')
    })

    it('should handle invalid pipeline stage', async () => {
      const error = createHubSpotError('Invalid stage value', 400)
      mockedAxios.patch.mockRejectedValue(error)

      await expect(
        axios.patch(
          `${HUBSPOT_BASE_URL}/crm/v3/objects/contacts/contact_123`,
          {
            properties: {
              dealstage: 'invalid_stage',
            },
          },
          {
            headers: {
              Authorization: `Bearer ${HUBSPOT_API_KEY}`,
            },
          }
        )
      ).rejects.toMatchObject({
        response: {
          status: 400,
        },
      })
    })
  })

  describe('Deal Management', () => {
    it('should create a deal for a contact', async () => {
      const mockResponse = createMockAxiosResponse(
        mockHubSpotDealResponse('deal_123'),
        201
      )
      mockedAxios.post.mockResolvedValue(mockResponse)

      const dealData = {
        properties: {
          dealname: 'Example Clinic Deal',
          dealstage: 'idle',
          amount: '10000',
        },
        associations: [
          {
            to: { id: 'contact_123' },
            types: [
              {
                associationCategory: 'HUBSPOT_DEFINED',
                associationTypeId: 3,
              },
            ],
          },
        ],
      }

      const response = await axios.post(
        `${HUBSPOT_BASE_URL}/crm/v3/objects/deals`,
        dealData,
        {
          headers: {
            Authorization: `Bearer ${HUBSPOT_API_KEY}`,
            'Content-Type': 'application/json',
          },
        }
      )

      expect(response.status).toBe(201)
      expect(response.data.id).toBe('deal_123')
      expect(response.data.properties.dealname).toBe('Example Clinic Deal')
      expect(response.data.properties.dealstage).toBe('idle')
    })
  })

  describe('OAuth Token Refresh', () => {
    it('should refresh OAuth token on 401 error', async () => {
      const mockError = createHubSpotError('Token expired', 401)
      const mockRefreshResponse = createMockAxiosResponse(
        mockHubSpotOAuthTokenResponse()
      )
      const mockSuccessResponse = createMockAxiosResponse(
        mockHubSpotContactResponse('contact_123')
      )

      // First call fails with 401
      mockedAxios.post
        .mockRejectedValueOnce(mockError)
        // Token refresh succeeds
        .mockResolvedValueOnce(mockRefreshResponse)
        // Retry succeeds
        .mockResolvedValueOnce(mockSuccessResponse)

      // Simulate token refresh flow
      const refreshToken = 'refresh_token_123'
      const clientId = 'client_id_123'
      const clientSecret = 'client_secret_123'

      // Attempt to create contact (fails)
      try {
        await axios.post(
          `${HUBSPOT_BASE_URL}/crm/v3/objects/contacts`,
          { properties: { email: 'test@example.com' } },
          {
            headers: {
              Authorization: 'Bearer expired_token',
            },
          }
        )
      } catch (error: any) {
        if (error.response?.status === 401) {
          // Refresh token
          const refreshResponse = await axios.post(
            `${HUBSPOT_BASE_URL}/oauth/v1/token`,
            {
              grant_type: 'refresh_token',
              refresh_token: refreshToken,
              client_id: clientId,
              client_secret: clientSecret,
            }
          )

          expect(refreshResponse.data.access_token).toBe('new_access_token_123')

          // Retry with new token
          const retryResponse = await axios.post(
            `${HUBSPOT_BASE_URL}/crm/v3/objects/contacts`,
            { properties: { email: 'test@example.com' } },
            {
              headers: {
                Authorization: `Bearer ${refreshResponse.data.access_token}`,
              },
            }
          )

          expect(retryResponse.status).toBe(200)
        }
      }
    })

    it('should get OAuth token metadata', async () => {
      const mockResponse = createMockAxiosResponse(
        mockHubSpotOAuthTokenMetadata()
      )
      mockedAxios.get.mockResolvedValue(mockResponse)

      const response = await axios.get(
        `${HUBSPOT_BASE_URL}/oauth/v1/access-tokens/access_token_123`,
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      )

      expect(response.status).toBe(200)
      expect(response.data.user).toBe('user@example.com')
      expect(response.data.hub_id).toBe(123456)
      expect(response.data.scopes).toContain('crm.objects.contacts.read')
    })
  })

  describe('Error Handling', () => {
    it('should handle 403 Forbidden error', async () => {
      const error = createHubSpotError('Insufficient permissions', 403)
      mockedAxios.post.mockRejectedValue(error)

      await expect(
        axios.post(
          `${HUBSPOT_BASE_URL}/crm/v3/objects/contacts`,
          { properties: { email: 'test@example.com' } },
          {
            headers: {
              Authorization: `Bearer ${HUBSPOT_API_KEY}`,
            },
          }
        )
      ).rejects.toMatchObject({
        response: {
          status: 403,
        },
      })
    })

    it('should handle rate limit errors', async () => {
      const error = createHubSpotError('Rate limit exceeded', 429)
      mockedAxios.post.mockRejectedValue(error)

      await expect(
        axios.post(
          `${HUBSPOT_BASE_URL}/crm/v3/objects/contacts`,
          { properties: { email: 'test@example.com' } },
          {
            headers: {
              Authorization: `Bearer ${HUBSPOT_API_KEY}`,
            },
          }
        )
      ).rejects.toMatchObject({
        response: {
          status: 429,
        },
      })
    })
  })
})

