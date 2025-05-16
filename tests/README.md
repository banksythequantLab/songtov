# Fast Renderer UI Testing

This directory contains automated tests for the MaiVid Studio Fast Renderer web interface using Puppeteer.

## Test Files

- `test_fast_renderer_ui.js` - Basic UI testing of the Fast Renderer page
- `test_fast_renderer_integration.js` - Integration testing with API mocking

## Running Tests

To run the tests, you'll need Node.js installed and the Puppeteer package. If you don't have it installed:

```bash
npm install puppeteer
```

Then run the basic UI tests:

```bash
node test_fast_renderer_ui.js
```

Or run the integration tests with API mocking:

```bash
node test_fast_renderer_integration.js
```

## Test Coverage

These tests verify:

1. Navigation to the Fast Renderer page from both:
   - The main navigation menu
   - The promotional banner on the homepage

2. Single Scene Generation:
   - Form input functionality
   - API request interception
   - Result display

3. Music Video Generation:
   - Form input functionality
   - Job status monitoring
   - Results display
   
4. Visual regression testing via screenshots

## Screenshots

All tests save screenshots to the `screenshots` folder with timestamps for review.

## Notes

- The integration tests use request interception to mock API responses
- Tests assume the MaiVid Studio application is running on http://localhost:420
- Timing and timeouts can be adjusted in the configuration section of each test file
