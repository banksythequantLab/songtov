/**
 * MaiVid Studio - Fast Renderer UI Tests
 * 
 * This script tests the Fast Renderer web interface functionality
 * using Puppeteer for automated browser testing.
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Configuration
const APP_URL = 'http://localhost:420';
const SCREENSHOTS_DIR = path.join(__dirname, 'screenshots');
const SUNO_TEST_URL = 'https://suno.com/song/test-song-id'; // Example URL
const TIMEOUT = 30000; // 30 seconds

// Ensure screenshots directory exists
if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

/**
 * Take a screenshot and save it to the screenshots directory
 */
async function takeScreenshot(page, name) {
  const screenshotPath = path.join(SCREENSHOTS_DIR, `${name}-${Date.now()}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`Screenshot saved: ${screenshotPath}`);
  return screenshotPath;
}

/**
 * Main test function
 */
async function runTests() {
  console.log('Starting Fast Renderer UI tests...');
  
  // Launch browser
  const browser = await puppeteer.launch({
    headless: false, // Set to true for production testing
    defaultViewport: { width: 1280, height: 800 },
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  page.setDefaultTimeout(TIMEOUT);
  
  try {
    // Test 1: Navigate to home page
    console.log('Test 1: Navigate to home page');
    await page.goto(APP_URL, { waitUntil: 'networkidle2' });
    await takeScreenshot(page, 'home-page');
    
    // Verify Fast Render link in navigation
    const fastRenderLink = await page.$('a[href="/fast_render"]');
    if (!fastRenderLink) {
      throw new Error('Fast Render link not found in navigation');
    }
    
    // Test 2: Navigate to Fast Render page
    console.log('Test 2: Navigate to Fast Render page');
    await fastRenderLink.click();
    await page.waitForSelector('.header h1');
    
    // Verify page loaded correctly
    const pageTitle = await page.$eval('.header h1', el => el.textContent);
    if (!pageTitle.includes('Fast Render')) {
      throw new Error(`Unexpected page title: ${pageTitle}`);
    }
    
    await takeScreenshot(page, 'fast-render-page');
    
    // Test 3: Test single scene generation
    console.log('Test 3: Test single scene generation');
    
    // Fill out the form
    await page.type('#sceneDescription', 'A futuristic cityscape with flying cars and neon signs');
    await page.select('#singleModelType', 'sdxl_turbo');
    await page.select('#singleAspectRatio', '16:9');
    await page.select('#singleStyle', 'cyberpunk');
    
    // Click generate button
    const generateButton = await page.$('#generateSceneButton');
    
    // Take screenshot before clicking
    await takeScreenshot(page, 'before-generate-scene');
    
    // Click the button
    await generateButton.click();
    
    // This would normally wait for an actual response, but since we don't have a running backend,
    // we'll just wait a moment to simulate response time
    await page.waitForTimeout(2000);
    
    // Take screenshot after clicking
    await takeScreenshot(page, 'after-generate-scene');
    
    // Test 4: Test music video generation form
    console.log('Test 4: Test music video generation form');
    
    // Fill out the form
    await page.type('#sunoUrl', SUNO_TEST_URL);
    await page.select('#modelType', 'sdxl_turbo');
    await page.select('#aspectRatio', '16:9');
    await page.select('#style', 'cyberpunk');
    await page.select('#sceneCount', '5');
    
    // Take screenshot of filled form
    await takeScreenshot(page, 'music-video-form');
    
    // Click generate button
    const generateMusicVideoButton = await page.$('#generateButton');
    
    // This would normally submit the form, but since we don't have a running backend,
    // we'll just verify the button exists
    if (!generateMusicVideoButton) {
      throw new Error('Generate Music Video button not found');
    }
    
    console.log('All UI tests completed successfully!');
  } catch (error) {
    console.error('Test failed:', error);
    await takeScreenshot(page, 'test-failure');
  } finally {
    // Close browser
    await browser.close();
  }
}

// Run the tests
runTests()
  .then(() => {
    console.log('Tests completed');
    process.exit(0);
  })
  .catch(error => {
    console.error('Error in test runner:', error);
    process.exit(1);
  });
