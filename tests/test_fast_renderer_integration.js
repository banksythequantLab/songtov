/**
 * MaiVid Studio - Fast Renderer Integration Tests
 * 
 * This script tests both the Fast Renderer UI and API endpoints
 * by mocking API responses and simulating real user interactions.
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Configuration
const APP_URL = 'http://localhost:420';
const SCREENSHOTS_DIR = path.join(__dirname, 'screenshots');
const SUNO_TEST_URL = 'https://suno.com/song/H6JQeAvqf4SgiFoF'; // Example URL
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
  console.log('Starting Fast Renderer integration tests...');
  
  // Launch browser
  const browser = await puppeteer.launch({
    headless: false, // Set to true for production testing
    defaultViewport: { width: 1280, height: 800 },
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  page.setDefaultTimeout(TIMEOUT);
  
  try {
    // Set up API route interception
    await setupApiInterceptions(page);
    
    // Test 1: Navigate to home page
    console.log('Test 1: Navigate to home page');
    await page.goto(APP_URL, { waitUntil: 'networkidle2' });
    await takeScreenshot(page, 'home-page');
    
    // Check for Fast Render promotion banner
    const promotionBanner = await page.$('.alert-success');
    if (promotionBanner) {
      console.log('Found Fast Render promotion banner on homepage');
      
      // Click the banner link
      const bannerLink = await promotionBanner.$('a.alert-link');
      if (bannerLink) {
        await bannerLink.click();
        await page.waitForSelector('.header h1');
        console.log('Successfully navigated to Fast Render page via promotion banner');
      } else {
        // Use navigation link instead
        const navLink = await page.$('a[href="/fast_render"]');
        await navLink.click();
        await page.waitForSelector('.header h1');
      }
    } else {
      // Use navigation link
      const fastRenderLink = await page.$('a[href="/fast_render"]');
      if (!fastRenderLink) {
        throw new Error('Fast Render link not found in navigation');
      }
      await fastRenderLink.click();
      await page.waitForSelector('.header h1');
    }
    
    // Test 2: Explore Fast Render page UI
    console.log('Test 2: Explore Fast Render page UI');
    await takeScreenshot(page, 'fast-render-page');
    
    // Check for main components
    const musicVideoSection = await page.$('.card-header h2');
    const musicVideoText = await page.evaluate(el => el.textContent, musicVideoSection);
    console.log(`Found section: ${musicVideoText}`);
    
    const singleSceneSection = await page.$$('.card-header h2');
    if (singleSceneSection.length >= 2) {
      const singleSceneText = await page.evaluate(el => el.textContent, singleSceneSection[1]);
      console.log(`Found section: ${singleSceneText}`);
    }
    
    // Test 3: Test single scene generation
    console.log('Test 3: Test single scene generation');
    
    // Fill out the form
    await page.type('#sceneDescription', 'A futuristic cityscape with flying cars and neon signs, cyberpunk style with rain and reflections');
    await page.select('#singleModelType', 'sdxl_turbo');
    await page.select('#singleAspectRatio', '16:9');
    await page.select('#singleStyle', 'cyberpunk');
    
    // Take screenshot before clicking
    await takeScreenshot(page, 'before-generate-scene');
    
    // Click generate button
    const generateButton = await page.$('#generateSceneButton');
    await generateButton.click();
    
    // Wait for the result to appear (intercepted API response will trigger this)
    await page.waitForSelector('#sceneResult', { visible: true, timeout: TIMEOUT });
    console.log('Scene generation result displayed successfully');
    
    // Take screenshot after result
    await takeScreenshot(page, 'scene-result');
    
    // Test interaction with scene result
    const downloadButton = await page.$('#downloadSceneButton');
    if (downloadButton) {
      console.log('Download button found, would trigger download in real environment');
    }
    
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
    await generateMusicVideoButton.click();
    
    // Wait for progress section to appear
    await page.waitForSelector('#generationProgress', { visible: true, timeout: TIMEOUT });
    console.log('Generation progress section appeared');
    
    // Take screenshot of progress
    await takeScreenshot(page, 'generation-progress');
    
    // Wait for some time to simulate job processing
    await page.waitForTimeout(3000);
    
    // Wait for results section to appear (intercepted API response will trigger this)
    await page.waitForSelector('#generationResults', { visible: true, timeout: TIMEOUT });
    console.log('Generation results section appeared');
    
    // Take screenshot of results
    await takeScreenshot(page, 'generation-results');
    
    // Test interaction with results
    const createVideoButton = await page.$('#createVideoButton');
    if (createVideoButton) {
      console.log('Create Video button found');
    }
    
    console.log('All integration tests completed successfully!');
  } catch (error) {
    console.error('Test failed:', error);
    await takeScreenshot(page, 'test-failure');
    throw error;
  } finally {
    // Close browser
    await browser.close();
  }
}

/**
 * Set up interception of API requests to simulate backend responses
 */
async function setupApiInterceptions(page) {
  await page.setRequestInterception(true);
  
  page.on('request', request => {
    const url = request.url();
    
    // Log all API requests
    if (url.includes('/api/')) {
      console.log(`Intercepted API request: ${url}`);
    }
    
    // Intercept Single Scene Generation API
    if (url.includes('/api/fast_render/generate') && request.method() === 'POST') {
      request.respond({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'scene_' + Date.now(),
          description: 'A futuristic cityscape with flying cars and neon signs, cyberpunk style with rain and reflections',
          model_type: 'sdxl_turbo',
          aspect_ratio: '16:9',
          style: 'cyberpunk',
          image_path: '/path/to/generated/image.png',
          image_url: 'https://picsum.photos/800/450' // Use placeholder image service
        })
      });
      return;
    }
    
    // Intercept Music Video Generation API
    if (url.includes('/api/fast_render/music_video') && request.method() === 'POST') {
      request.respond({
        status: 202, // Accepted
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'job_' + Date.now(),
          status: 'processing',
          message: 'Music video generation started',
          params: {
            suno_url: SUNO_TEST_URL,
            model_type: 'sdxl_turbo',
            aspect_ratio: '16:9',
            scene_count: 5,
            style: 'cyberpunk'
          }
        })
      });
      return;
    }
    
    // Intercept Job Status API
    if (url.includes('/api/fast_render/job/') && request.method() === 'GET') {
      // Simulate job completion after a few seconds
      // In a real test we would need to track the job_id
      request.respond({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: url.split('/').pop(),
          success: true,
          song_title: "Neon Dreams",
          artist: "CyberWave",
          scene_count: 5,
          successful_scenes: 5,
          scenes: [
            {
              id: 'scene_1',
              description: 'Neon cityscape with rain and reflections',
              success: true,
              image_url: 'https://picsum.photos/800/450?random=1'
            },
            {
              id: 'scene_2',
              description: 'Protagonist walking through cyberpunk marketplace',
              success: true,
              image_url: 'https://picsum.photos/800/450?random=2'
            },
            {
              id: 'scene_3',
              description: 'Close-up of digital interface with holographic display',
              success: true,
              image_url: 'https://picsum.photos/800/450?random=3'
            },
            {
              id: 'scene_4',
              description: 'Flying vehicles between skyscrapers at night',
              success: true,
              image_url: 'https://picsum.photos/800/450?random=4'
            },
            {
              id: 'scene_5',
              description: 'Final scene with sunrise over futuristic city',
              success: true,
              image_url: 'https://picsum.photos/800/450?random=5'
            }
          ]
        })
      });
      return;
    }
    
    // Let other requests pass through
    request.continue();
  });
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
