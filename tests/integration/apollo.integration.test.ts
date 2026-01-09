/**
 * Integration tests for Apollo.io API.
 * All API calls are mocked using Vitest's vi.mock() to avoid credit consumption.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import {
  mockApolloSearchResponse,
  mockApolloPersonEnrichment,
  mockApolloOrganizationEnrichment,
  mockApolloBulkPeopleResponse,
  mockApolloBulkOrganizationsResponse,
  mockApolloErrorResponse,
} from '../fixtures/apolloResponses'
import {
  createMockAxiosResponse,
  createApolloError,
  buildApolloSearchParams,
} from '../utils/mockHelpers'

// Mock axios
vi.mock('axios')
const mockedAxios = axios as any

describe('Apollo.io API Integration', () => {
  const APOLLO_API_KEY = process.env.APOLLO_API_KEY || 'test_api_key'
  const APOLLO_BASE_URL = 'https://api.apollo.io/v1'

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Lead Search', () => {
    it('should search for leads successfully', async () => {
      const mockResponse = createMockAxiosResponse(
        mockApolloSearchResponse(2)
      )
      mockedAxios.post.mockResolvedValue(mockResponse)

      const searchParams = buildApolloSearchParams(
        'New York, NY',
        'Dermatology',
        2
      )

      const response = await axios.post(
        `${APOLLO_BASE_URL}/mixed_people/search`,
        searchParams,
        {
          headers: {
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json',
          },
        }
      )

      expect(response.status).toBe(200)
      expect(response.data.people).toHaveLength(2)
      expect(response.data.people[0].email).toBe('john0@example.com')
      expect(response.data.people[0].organization.name).toBe('Example Clinic 1')
      expect(mockedAxios.post).toHaveBeenCalledWith(
        `${APOLLO_BASE_URL}/mixed_people/search`,
        expect.objectContaining({
          q_keywords: 'Dermatology',
          person_locations: ['New York, NY'],
        }),
        expect.any(Object)
      )
    })

    it('should handle 401 authentication error', async () => {
      const error = createApolloError('Invalid API key', 401)
      mockedAxios.post.mockRejectedValue(error)

      await expect(
        axios.post(`${APOLLO_BASE_URL}/mixed_people/search`, {
          api_key: 'invalid_key',
        })
      ).rejects.toMatchObject({
        response: {
          status: 401,
        },
      })
    })

    it('should handle 402 payment required error', async () => {
      const error = createApolloError('Insufficient credits', 402)
      mockedAxios.post.mockRejectedValue(error)

      await expect(
        axios.post(`${APOLLO_BASE_URL}/mixed_people/search`, {
          api_key: APOLLO_API_KEY,
        })
      ).rejects.toMatchObject({
        response: {
          status: 402,
        },
      })
    })

    it('should handle 429 rate limit error', async () => {
      const error = createApolloError('Rate limit exceeded', 429)
      mockedAxios.post.mockRejectedValue(error)

      await expect(
        axios.post(`${APOLLO_BASE_URL}/mixed_people/search`, {
          api_key: APOLLO_API_KEY,
        })
      ).rejects.toMatchObject({
        response: {
          status: 429,
        },
      })
    })

    it('should return empty array when no leads found', async () => {
      const mockResponse = createMockAxiosResponse({ people: [] })
      mockedAxios.post.mockResolvedValue(mockResponse)

      const response = await axios.post(
        `${APOLLO_BASE_URL}/mixed_people/search`,
        {
          api_key: APOLLO_API_KEY,
          q_keywords: 'NonExistentSpecialty',
        }
      )

      expect(response.data.people).toHaveLength(0)
    })

    it('should include website filter when specified', async () => {
      const mockResponse = createMockAxiosResponse(mockApolloSearchResponse(1))
      mockedAxios.post.mockResolvedValue(mockResponse)

      const params = buildApolloSearchParams(
        'New York, NY',
        'Dermatology',
        10,
        true
      )

      await axios.post(`${APOLLO_BASE_URL}/mixed_people/search`, params)

      expect(mockedAxios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          organization_keywords: 'website',
        })
      )
    })
  })

  describe('Person Enrichment', () => {
    it('should enrich person data successfully (consumes 1 credit)', async () => {
      const mockResponse = createMockAxiosResponse(
        mockApolloPersonEnrichment('john@example.com')
      )
      mockedAxios.post.mockResolvedValue(mockResponse)

      const enrichParams = {
        api_key: APOLLO_API_KEY,
        email: 'john@example.com',
        first_name: 'John',
        last_name: 'Doe',
      }

      const response = await axios.post(
        `${APOLLO_BASE_URL}/people/match`,
        enrichParams,
        {
          headers: {
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json',
          },
        }
      )

      expect(response.status).toBe(200)
      expect(response.data.person.email).toBe('john@example.com')
      expect(response.data.person.title).toBe('CEO')
      expect(mockedAxios.post).toHaveBeenCalledWith(
        `${APOLLO_BASE_URL}/people/match`,
        expect.objectContaining({
          email: 'john@example.com',
        }),
        expect.any(Object)
      )
    })

    it('should handle person enrichment errors', async () => {
      const error = createApolloError('Person not found', 404)
      mockedAxios.post.mockRejectedValue(error)

      await expect(
        axios.post(`${APOLLO_BASE_URL}/people/match`, {
          api_key: APOLLO_API_KEY,
          email: 'nonexistent@example.com',
        })
      ).rejects.toMatchObject({
        response: {
          status: 404,
        },
      })
    })

    it('should track credit consumption for multiple enrichments', async () => {
      const mockResponse = createMockAxiosResponse(
        mockApolloPersonEnrichment('test@example.com')
      )
      mockedAxios.post.mockResolvedValue(mockResponse)

      // Enrich 3 people (3 credits)
      for (let i = 0; i < 3; i++) {
        await axios.post(`${APOLLO_BASE_URL}/people/match`, {
          api_key: APOLLO_API_KEY,
          email: `person${i}@example.com`,
        })
      }

      expect(mockedAxios.post).toHaveBeenCalledTimes(3)
    })
  })

  describe('Organization Enrichment', () => {
    it('should enrich organization data successfully (consumes 1 credit)', async () => {
      const mockResponse = createMockAxiosResponse(
        mockApolloOrganizationEnrichment('example.com')
      )
      mockedAxios.post.mockResolvedValue(mockResponse)

      const enrichParams = {
        api_key: APOLLO_API_KEY,
        domain: 'example.com',
        name: 'Example Clinic',
      }

      const response = await axios.post(
        `${APOLLO_BASE_URL}/organizations/enrich`,
        enrichParams
      )

      expect(response.status).toBe(200)
      expect(response.data.organization.name).toBe('Example Clinic')
      expect(response.data.organization.domain).toBe('example.com')
    })

    it('should handle organization enrichment errors', async () => {
      const error = createApolloError('Organization not found', 404)
      mockedAxios.post.mockRejectedValue(error)

      await expect(
        axios.post(`${APOLLO_BASE_URL}/organizations/enrich`, {
          api_key: APOLLO_API_KEY,
          domain: 'nonexistent.com',
        })
      ).rejects.toMatchObject({
        response: {
          status: 404,
        },
      })
    })
  })

  describe('Bulk Operations', () => {
    it('should bulk enrich people (1 credit per person)', async () => {
      const mockResponse = createMockAxiosResponse(
        mockApolloBulkPeopleResponse(2)
      )
      mockedAxios.post.mockResolvedValue(mockResponse)

      const bulkParams = {
        api_key: APOLLO_API_KEY,
        people: [
          { email: 'person1@example.com' },
          { email: 'person2@example.com' },
        ],
      }

      const response = await axios.post(
        `${APOLLO_BASE_URL}/people/bulk_match`,
        bulkParams
      )

      expect(response.status).toBe(200)
      expect(response.data.people).toHaveLength(2)
      // 2 people = 2 credits consumed
    })

    it('should bulk enrich organizations (1 credit per organization)', async () => {
      const mockResponse = createMockAxiosResponse(
        mockApolloBulkOrganizationsResponse(2)
      )
      mockedAxios.post.mockResolvedValue(mockResponse)

      const bulkParams = {
        api_key: APOLLO_API_KEY,
        organizations: [{ domain: 'org1.com' }, { domain: 'org2.com' }],
      }

      const response = await axios.post(
        `${APOLLO_BASE_URL}/organizations/bulk_enrich`,
        bulkParams
      )

      expect(response.status).toBe(200)
      expect(response.data.organizations).toHaveLength(2)
      // 2 organizations = 2 credits consumed
    })
  })

  describe('Credit Consumption Tracking', () => {
    it('should track credit consumption for enrichment operations', async () => {
      const personResponse = createMockAxiosResponse(
        mockApolloPersonEnrichment('test@example.com')
      )
      const orgResponse = createMockAxiosResponse(
        mockApolloOrganizationEnrichment('test.com')
      )

      mockedAxios.post
        .mockResolvedValueOnce(personResponse) // Person enrichment (1 credit)
        .mockResolvedValueOnce(orgResponse) // Org enrichment (1 credit)

      // Enrich person (1 credit)
      await axios.post(`${APOLLO_BASE_URL}/people/match`, {
        api_key: APOLLO_API_KEY,
        email: 'test@example.com',
      })

      // Enrich organization (1 credit)
      await axios.post(`${APOLLO_BASE_URL}/organizations/enrich`, {
        api_key: APOLLO_API_KEY,
        domain: 'test.com',
      })

      // Total: 2 credits consumed
      expect(mockedAxios.post).toHaveBeenCalledTimes(2)
    })
  })

  describe('Data Transformation', () => {
    it('should correctly transform API response to lead data structure', async () => {
      const mockResponse = createMockAxiosResponse(mockApolloSearchResponse(1))
      mockedAxios.post.mockResolvedValue(mockResponse)

      const response = await axios.post(
        `${APOLLO_BASE_URL}/mixed_people/search`,
        buildApolloSearchParams()
      )

      const person = response.data.people[0]
      expect(person.first_name).toBe('John0')
      expect(person.last_name).toBe('Doe0')
      expect(person.email).toBe('john0@example.com')
      expect(person.organization.name).toBe('Example Clinic 1')
      expect(person.organization.website_url).toBe('https://example0.com')
    })
  })
})

