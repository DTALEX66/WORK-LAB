import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

// after each test, unmount + reset URL so view/theme helpers don't leak
afterEach(() => {
  cleanup()
  window.history.replaceState(null, '', window.location.pathname)
})
