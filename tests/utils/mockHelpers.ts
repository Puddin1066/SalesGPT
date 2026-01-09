/**
 * Helper functions for creating mocks in TypeScript tests.
 * Response builders and error simulators.
 */
import { AxiosError, AxiosResponse } from 'axios'

export interface MockAxiosResponse<T = any> {
  data: T
  status: number
  statusText: string
  headers: Record<string, string>
}

export function createMockAxiosResponse<T>(
  data: T,
  status: number = 200,
  statusText: string = 'OK',
  headers: Record<string, string> = {}
): MockAxiosResponse<T> {
  return {
    data,
    status,
    statusText,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  }
}

export function createMockAxiosError(
  message: string,
  status: number = 400,
  responseData?: any
): AxiosError {
  const error = new Error(message) as AxiosError
  error.response = {
    data: responseData || { message, statusCode: status },
    status,
    statusText: 'Error',
    headers: {},
    config: {} as any,
  } as AxiosResponse
  error.isAxiosError = true
  return error
}

export function createApolloError(
  message: string,
  status: number = 400
): AxiosError {
  return createMockAxiosError(message, status, { message })
}

export function createHubSpotError(
  message: string,
  status: number = 400
): AxiosError {
  return createMockAxiosError(message, status, {
    status: 'error',
    message,
    statusCode: status,
  })
}

export function buildApolloSearchParams(
  geography: string = 'New York, NY',
  specialty: string = 'Dermatology',
  limit: number = 50,
  hasWebsite: boolean = true
): Record<string, any> {
  const params: Record<string, any> = {
    api_key: 'test_api_key',
    q_keywords: specialty,
    person_locations: [geography],
    organization_num_employees_ranges: ['1,50'],
    person_titles: [
      'Owner',
      'CEO',
      'Medical Director',
      'Practice Manager',
      'Partner',
      'Managing Partner',
      'Principal',
      'Broker',
    ],
    page: 1,
    per_page: Math.min(limit, 50),
  }

  if (hasWebsite) {
    params.organization_keywords = 'website'
  }

  return params
}

export function buildHubSpotContactPayload(
  email: string = 'test@example.com',
  firstName: string = 'Test',
  lastName: string = 'User',
  company?: string,
  website?: string
): Record<string, any> {
  const properties: Record<string, string> = {
    email,
    firstname: firstName,
    lastname: lastName,
  }

  if (company) {
    properties.company = company
  }
  if (website) {
    properties.website = website
  }

  return { properties }
}

