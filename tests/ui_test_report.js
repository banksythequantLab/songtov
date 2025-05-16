/**
 * MaiVid Studio UI Test Report
 * 
 * This script performs UI testing and generates a detailed report with screenshots
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Test configuration
const config = {
  baseUrl: 'http://localhost:420', // Default MaiVid Studio port
  headless: 'new', // Use headless mode for CI environments
  slowMo: 50, // Slow down operations for visibility
  timeout: 30000, // 30 seconds timeout
  viewportWidth: 1280,
  viewportHeight: 800,
  reportsDir: path.join(__dirname, '..', 'test-reports'),
  timestamp: new Date().toISOString().replace(/:/g, '-').replace(/\..+/, '')
};

// Ensure reports directory exists
if (!fs.existsSync(config.reportsDir)) {
  fs.mkdirSync(config.reportsDir, { recursive: true });
}

// Create report file
const reportFile = path.join(config.reportsDir, `ui-test-report-${config.timestamp}.md`);
const logFile = path.join(config.reportsDir, `ui-test-log-${config.timestamp}.txt`);

/**
 * Log a message to both console and log file
 */
function log(message) {
  console.log(message);
  fs.appendFileSync(logFile, message + '\n');
}

/**
 * Add a test result to the report file
 */
function reportTest(test, result, details, screenshotPath = null) {
  let icon = result ? '✅' : '❌';
  let status = result ? 'PASSED' : 'FAILED';
  let report = `## ${icon} Test: ${test}\n\n**Status:** ${status}\n\n`;
  
  if (details) {
    report += `**Details:**\n\n${details}\n\n`;
  }
  
  if (screenshotPath) {
    const relPath = path.relative(path.dirname(reportFile), screenshotPath);
    report += `**Screenshot:** [View Screenshot](${relPath})\n\n`;
    report += `![${test}](${relPath})\n\n`;
  }
  
  report += '---\n\n';
  fs.appendFileSync(reportFile, report);
  
  log(`${icon} ${test}: ${status}`);
  if (details) log(`   Details: ${details.split('\n').join('\n   ')}`);
}

async function runTests() {
  log(`Starting MaiVid Studio UI tests... (${config.timestamp})`);
  log(`Configuration: ${JSON.stringify(config, null, 2)}`);
  
  // Initialize report file
  fs.writeFileSync(reportFile, `# MaiVid Studio UI Test Report\n\n**Date:** ${new Date().toLocaleString()}\n\n---\n\n`);
  fs.writeFileSync(logFile, `MaiVid Studio UI Test Log\n${'-'.repeat(30)}\nDate: ${new Date().toLocaleString()}\n\n`);
  
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
    log('Test 1: Testing homepage...');
    try {
      await page.goto(`${config.baseUrl}/`, { 
        waitUntil: 'networkidle2',
        timeout: config.timeout 
      });
      
      await page.waitForSelector('#showcase');
      
      const screenshotPath = path.join(config.reportsDir, `homepage-${config.timestamp}.png`);
      await page.screenshot({ path: screenshotPath, fullPage: true });
      
      reportTest('Homepage Loading', true, 'Homepage loaded successfully and showcase element found', screenshotPath);
    } catch (error) {
      reportTest('Homepage Loading', false, `Error: ${error.message}`);
      log(`Error in homepage test: ${error.message}`);
    }
    
    // Test 2: Verify showcase rotation
    log('Test 2: Testing image carousel rotation...');
    try {
      // Get the initial active showcase image
      const initialActiveImageClass = await page.evaluate(() => {
        const activeImage = document.querySelector('.showcase-image.active');
        return activeImage ? activeImage.className : '';
      });
      
      if (!initialActiveImageClass) {
        throw new Error('No active showcase image found');
      }
      
      // Wait for rotation to happen (should be within 4 seconds)
      await page.waitForFunction(() => {
        const activeImage = document.querySelector('.showcase-image.active');
        const currentActiveClass = activeImage ? activeImage.className : '';
        return currentActiveClass !== '' && currentActiveClass !== initialActiveImageClass;
      }, { timeout: 5000 });
      
      const screenshotPath = path.join(config.reportsDir, `carousel-${config.timestamp}.png`);
      await page.screenshot({ path: screenshotPath, fullPage: false });
      
      reportTest('Image Carousel Rotation', true, 'Image carousel rotation works correctly', screenshotPath);
    } catch (error) {
      reportTest('Image Carousel Rotation', false, `Error: ${error.message}`);
      log(`Error in carousel test: ${error.message}`);
    }
    
    // Test 3: Verify card styling
    log('Test 3: Testing card styling...');
    try {
      const cardBorderColor = await page.evaluate(() => {
        const card = document.querySelector('.card');
        if (!card) return null;
        
        const style = window.getComputedStyle(card);
        const borderColor = style.borderColor;
        const boxShadow = style.boxShadow;
        
        return { borderColor, boxShadow };
      });
      
      const screenshotPath = path.join(config.reportsDir, `card-styling-${config.timestamp}.png`);
      await page.screenshot({ path: screenshotPath, fullPage: false });
      
      if (cardBorderColor && cardBorderColor.borderColor !== 'rgba(0, 0, 0, 0)') {
        reportTest('Card Styling', true, `Card borders are visible: ${JSON.stringify(cardBorderColor)}`, screenshotPath);
      } else {
        reportTest('Card Styling', false, `Card borders are not visible or too light: ${JSON.stringify(cardBorderColor)}`, screenshotPath);
      }
    } catch (error) {
      reportTest('Card Styling', false, `Error: ${error.message}`);
      log(`Error in card styling test: ${error.message}`);
    }
    
    // Test 4: Testing form submission (download music from URL)
    log('Test 4: Testing music URL form submission...');
    try {
      // Fill the form
      await page.type('#music-url', 'https://suno.com/s/H6JQeAvqf4SgiFoF');
      
      // Setup request listener to check Content-Type issues
      let responseStatusCode = null;
      let responseError = null;
      
      page.on('response', async (response) => {
        if (response.url().includes('/api/music/download')) {
          responseStatusCode = response.status();
          log(`Download music API responded with status: ${responseStatusCode}`);
          
          try {
            const responseBody = await response.json();
            log(`Response body: ${JSON.stringify(responseBody)}`);
          } catch (e) {
            responseError = e.message;
            log(`Could not parse response as JSON: ${e.message}`);
          }
        }
      });
      
      // Take screenshot before submission
      const beforeScreenshotPath = path.join(config.reportsDir, `form-before-${config.timestamp}.png`);
      await page.screenshot({ path: beforeScreenshotPath, fullPage: false });
      
      // Submit the form
      await Promise.all([
        page.click('#url-form button[type="submit"]'),
        page.waitForSelector('#loading-indicator', { timeout: 2000 }).catch(() => {})
      ]);
      
      // Wait a bit to see if loading indicator appears
      await page.waitForTimeout(2000);
      
      // Take screenshot after submission
      const afterScreenshotPath = path.join(config.reportsDir, `form-after-${config.timestamp}.png`);
      await page.screenshot({ path: afterScreenshotPath, fullPage: false });
      
      // Check response status
      if (responseStatusCode === 415) {
        reportTest('Form Submission', false, 'Content-Type error (415) still occurring', afterScreenshotPath);
      } else if (responseStatusCode === 200) {
        reportTest('Form Submission', true, 'Form submitted successfully', afterScreenshotPath);
      } else {
        reportTest('Form Submission', false, `Unexpected status code: ${responseStatusCode}, Error: ${responseError}`, afterScreenshotPath);
      }
    } catch (error) {
      reportTest('Form Submission', false, `Error: ${error.message}`);
      log(`Error in form submission test: ${error.message}`);
    }
    
    // Final summary screenshot
    const finalScreenshotPath = path.join(config.reportsDir, `final-state-${config.timestamp}.png`);
    await page.screenshot({ path: finalScreenshotPath, fullPage: true });
    
    // Add summary to report
    fs.appendFileSync(reportFile, `## Test Summary\n\nFinal page state:\n\n![Final State](${path.relative(path.dirname(reportFile), finalScreenshotPath)})\n\n`);
    
    log('All tests completed!');
  } catch (error) {
    log(`❌ Test suite failed with error: ${error.message}`);
    fs.appendFileSync(reportFile, `## ❌ Test Suite Failure\n\n**Error:** ${error.message}\n\n`);
  } finally {
    // Take a final screenshot in case of errors
    const errorScreenshotPath = path.join(config.reportsDir, `error-state-${config.timestamp}.png`);
    await page.screenshot({ path: errorScreenshotPath, fullPage: true });
    
    await browser.close();
    
    log(`Testing completed. Report saved to: ${reportFile}`);
    console.log(`\nTesting completed. Report saved to: ${reportFile}`);
  }
}

// Run the tests
runTests().catch(error => {
  console.error('Test execution failed:', error);
  fs.appendFileSync(logFile, `FATAL ERROR: ${error.message}\n${error.stack}\n`);
});
