/**
 * TypeScript interfaces and mock data for HubSpot API responses.
 */

export interface HubSpotContact {
  id: string
  properties: {
    email: string
    firstname?: string
    lastname?: string
    company?: string
    website?: string
    dealstage?: string
  }
  createdAt?: string
  updatedAt?: string
}

export interface HubSpotContactList {
  results: HubSpotContact[]
  paging?: {
    next?: {
      after: string
      link?: string
    }
  }
}

export interface HubSpotDeal {
  id: string
  properties: {
    dealname: string
    dealstage: string
    amount?: string
  }
  associations?: {
    contacts?: {
      results: Array<{
        id: string
        type: string
      }>
    }
  }
  createdAt?: string
  updatedAt?: string
}

export interface HubSpotOAuthTokenResponse {
  access_token: string
  refresh_token: string
  expires_in: number
  token_type: string
}

export interface HubSpotOAuthTokenMetadata {
  token: string
  user: string
  hub_id: number
  scopes: string[]
  hub_domain: string
  app_id: string
  expires_in: number
  user_id: string
  token_type: string
}

export interface HubSpotErrorResponse {
  status: string
  message: string
  correlationId?: string
  statusCode: number
}

/**
 * Mock response generators
 */
export function mockHubSpotContactResponse(contactId: string = 'contact_123'): HubSpotContact {
  return {
    id: contactId,
    properties: {
      email: 'john@example.com',
      firstname: 'John',
      lastname: 'Doe',
      company: 'Example Clinic',
      website: 'https://example.com',
    },
    createdAt: '2024-01-01T00:00:00.000Z',
    updatedAt: '2024-01-01T00:00:00.000Z',
  }
}

export function mockHubSpotContactListResponse(): HubSpotContactList {
  return {
    results: [
      {
        id: 'contact_123',
        properties: {
          email: 'john@example.com',
          firstname: 'John',
          lastname: 'Doe',
        },
      },
    ],
    paging: {},
  }
}

export function mockHubSpotDealResponse(dealId: string = 'deal_123'): HubSpotDeal {
  return {
    id: dealId,
    properties: {
      dealname: 'Example Clinic Deal',
      dealstage: 'idle',
      amount: '10000',
    },
    associations: {
      contacts: {
        results: [
          {
            id: 'contact_123',
            type: 'deal_to_contact',
          },
        ],
      },
    },
    createdAt: '2024-01-01T00:00:00.000Z',
    updatedAt: '2024-01-01T00:00:00.000Z',
  }
}

export function mockHubSpotOAuthTokenResponse(): HubSpotOAuthTokenResponse {
  return {
    access_token: 'new_access_token_123',
    refresh_token: 'new_refresh_token_123',
    expires_in: 3600,
    token_type: 'Bearer',
  }
}

export function mockHubSpotOAuthTokenMetadata(): HubSpotOAuthTokenMetadata {
  return {
    token: 'access_token_123',
    user: 'user@example.com',
    hub_id: 123456,
    scopes: ['crm.objects.contacts.read', 'crm.objects.contacts.write'],
    hub_domain: 'example.hubspot.com',
    app_id: 'app_123',
    expires_in: 3600,
    user_id: 'user_123',
    token_type: 'Bearer',
  }
}

export function mockHubSpotErrorResponse(
  message: string,
  statusCode: number
): HubSpotErrorResponse {
  return {
    status: 'error',
    message,
    correlationId: 'correlation_123',
    statusCode,
  }
}

export function mockHubSpot401Error(): HubSpotErrorResponse {
  return mockHubSpotErrorResponse('Authentication credentials not found', 401)
}

export function mockHubSpot403Error(): HubSpotErrorResponse {
  return mockHubSpotErrorResponse('Insufficient permissions', 403)
}

export function mockHubSpot404Error(): HubSpotErrorResponse {
  return mockHubSpotErrorResponse('Resource not found', 404)
}

export function mockHubSpotRateLimitError(): HubSpotErrorResponse {
  return mockHubSpotErrorResponse('Rate limit exceeded', 429)
}

