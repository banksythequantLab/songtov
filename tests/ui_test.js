/**
 * MaiVid Studio UI Testing
 * This script uses Puppeteer to verify UI fixes and functionality
 */

const puppeteer = require('puppeteer');

// Test configuration
const config = {
  baseUrl: 'http://localhost:420', // Default MaiVid Studio port
  headless: false, // Set to true for CI environments
  slowMo: 50, // Slow down operations for visibility
  timeout: 30000, // 30 seconds timeout
  viewportWidth: 1280,
  viewportHeight: 800
};

async function runTests() {
  console.log('Starting MaiVid Studio UI tests...');
  
  const browser = await puppeteer.launch({
    headless: config.headless,
    slowMo: config.slowMo,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  await page.setViewport({ 
    width: config.viewportWidth, 
    height: config.viewportHeight 
  });
  
  try {
    // Test 1: Verify homepage loads correctly
    console.log('Test 1: Testing homepage...');
    await page.goto(`${config.baseUrl}/`, { 
      waitUntil: 'networkidle2',
      timeout: config.timeout 
    });
    
    await page.waitForSelector('#showcase');
    console.log('✅ Homepage loaded successfully');
    
    // Test 2: Verify showcase rotation
    console.log('Test 2: Testing image carousel rotation...');
    // Get the initial active showcase image
    const initialActiveImageClass = await page.evaluate(() => {
      const activeImage = document.querySelector('.showcase-image.active');
      return activeImage ? activeImage.className : '';
    });
    
    // Wait for rotation to happen (should be within 4 seconds)
    await page.waitForFunction(() => {
      const activeImage = document.querySelector('.showcase-image.active');
      const currentActiveClass = activeImage ? activeImage.className : '';
      return initialActiveImageClass !== '' && currentActiveClass !== initialActiveImageClass;
    }, { timeout: 5000 });
    
    console.log('✅ Image carousel rotation works correctly');
    
    // Test 3: Verify card styling
    console.log('Test 3: Testing card styling...');
    const cardBorderColor = await page.evaluate(() => {
      const card = document.querySelector('.card');
      if (!card) return null;
      
      const style = window.getComputedStyle(card);
      return style.borderColor;
    });
    
    if (cardBorderColor && cardBorderColor !== 'rgba(0, 0, 0, 0)') {
      console.log('✅ Card borders are visible');
    } else {
      console.log('❌ Card borders are not visible');
    }
    
    // Test 4: Testing form submission (download music from URL)
    console.log('Test 4: Testing music URL form submission...');
    
    // Fill the form
    await page.type('#music-url', 'https://suno.com/s/H6JQeAvqf4SgiFoF');
    
    // Setup request listener to check Content-Type issues
    let responseStatusCode = null;
    page.on('response', async (response) => {
      if (response.url().includes('/api/music/download')) {
        responseStatusCode = response.status();
        console.log(`Download music API responded with status: ${responseStatusCode}`);
      }
    });
    
    // Submit the form
    await Promise.all([
      page.click('#url-form button[type="submit"]'),
      page.waitForSelector('#loading-indicator', { timeout: 2000 }).catch(() => {})
    ]);
    
    // Wait a bit to see if loading indicator appears
    await page.waitForTimeout(2000);
    
    // Check if the form submission was successful or if there was a 415 error
    if (responseStatusCode === 415) {
      console.log('❌ Content-Type error (415) still occurring');
    } else if (responseStatusCode === 200) {
      console.log('✅ Form submitted successfully');
    } else {
      // The API may take longer to respond or there might be other issues
      console.log('⚠️ Form submitted but response status unknown or error occurred');
    }
    
    console.log('All tests completed!');
  } catch (error) {
    console.error('❌ Test failed with error:', error);
  } finally {
    await page.screenshot({ path: 'K:\\MaiVid_Studio\\tests\\test-results.png', fullPage: true });
    await browser.close();
  }
}

// Run the tests
runTests().catch(console.error);
