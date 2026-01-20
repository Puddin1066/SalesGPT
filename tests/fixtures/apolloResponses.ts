/**
 * TypeScript interfaces and mock data for Apollo.io API responses.
 */

export interface ApolloPerson {
  id?: string
  first_name: string
  last_name: string
  email: string
  title?: string
  linkedin_url?: string
  updated_at?: string
}

export interface ApolloOrganization {
  id?: string
  name: string
  domain?: string
  website_url?: string
  estimated_num_employees?: number
  updated_at?: string
}

export interface ApolloSearchPerson {
  first_name: string
  last_name: string
  email: string
  title?: string
  linkedin_url?: string
  organization: ApolloOrganization
}

export interface ApolloSearchResponse {
  people: ApolloSearchPerson[]
  pagination?: {
    page: number
    per_page: number
    total_entries: number
  }
}

export interface ApolloPersonEnrichmentResponse {
  person: ApolloPerson
}

export interface ApolloOrganizationEnrichmentResponse {
  organization: ApolloOrganization
}

export interface ApolloBulkPeopleResponse {
  people: ApolloPerson[]
}

export interface ApolloBulkOrganizationsResponse {
  organizations: ApolloOrganization[]
}

export interface ApolloErrorResponse {
  message: string
  statusCode?: number
}

/**
 * Mock response generators
 */
export function mockApolloSearchResponse(limit: number = 2): ApolloSearchResponse {
  const people: ApolloSearchPerson[] = []
  for (let i = 0; i < limit; i++) {
    people.push({
      first_name: `John${i}`,
      last_name: `Doe${i}`,
      email: `john${i}@example.com`,
      title: i === 0 ? 'Owner' : 'Medical Director',
      linkedin_url: `https://linkedin.com/in/johndoe${i}`,
      organization: {
        id: `org_${i}`,
        name: `Example Clinic ${i + 1}`,
        website_url: `https://example${i}.com`,
        estimated_num_employees: 10 + i * 5,
      },
    })
  }
  return {
    people,
    pagination: {
      page: 1,
      per_page: limit,
      total_entries: limit,
    },
  }
}

export function mockApolloPersonEnrichment(email: string): ApolloPersonEnrichmentResponse {
  return {
    person: {
      id: `person_${email.length}`,
      first_name: email.split('@')[0].split('.')[0].charAt(0).toUpperCase() + email.split('@')[0].slice(1),
      last_name: 'Doe',
      email,
      title: 'CEO',
      linkedin_url: `https://linkedin.com/in/${email.split('@')[0]}`,
      updated_at: '2024-01-01T00:00:00Z',
    },
  }
}

export function mockApolloOrganizationEnrichment(domain: string): ApolloOrganizationEnrichmentResponse {
  return {
    organization: {
      id: `org_${domain.length}`,
      name: domain.split('.')[0].charAt(0).toUpperCase() + domain.split('.')[0].slice(1) + ' Clinic',
      domain,
      website_url: `https://${domain}`,
      estimated_num_employees: 15,
      updated_at: '2024-01-01T00:00:00Z',
    },
  }
}

export function mockApolloBulkPeopleResponse(count: number): ApolloBulkPeopleResponse {
  const people: ApolloPerson[] = []
  for (let i = 0; i < count; i++) {
    people.push({
      first_name: `Person${i}`,
      last_name: 'Test',
      email: `person${i}@example.com`,
    })
  }
  return { people }
}

export function mockApolloBulkOrganizationsResponse(count: number): ApolloBulkOrganizationsResponse {
  const organizations: ApolloOrganization[] = []
  for (let i = 0; i < count; i++) {
    organizations.push({
      name: `Org ${i + 1}`,
      domain: `org${i}.com`,
      website_url: `https://org${i}.com`,
    })
  }
  return { organizations }
}

export function mockApolloErrorResponse(message: string, statusCode: number = 400): ApolloErrorResponse {
  return {
    message,
    statusCode,
  }
}



