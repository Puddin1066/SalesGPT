import { beforeAll, afterAll, vi } from 'vitest'
import dotenv from 'dotenv'
import path from 'path'

// Load test environment variables
dotenv.config({ path: path.resolve(__dirname, '../.env.test') })

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  log: vi.fn(),
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn(),
}

beforeAll(() => {
  // Setup before all tests
  // Can add global test setup here
})

afterAll(() => {
  // Cleanup after all tests
  // Can add global test cleanup here
})



