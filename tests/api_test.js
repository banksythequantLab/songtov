/**
 * MaiVid Studio API Test
 * This script tests API functionality without requiring a browser
 */

const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');

// Configuration
const config = {
  host: 'localhost',
  port: 420,
  endpoints: {
    download: '/api/music/download',
    home: '/'
  },
  testUrl: 'https://suno.com/s/H6JQeAvqf4SgiFoF'
};

// Create a log file
const logFile = path.join(__dirname, 'api_test_results.log');
fs.writeFileSync(logFile, `API Test Results - ${new Date().toISOString()}\n\n`);

/**
 * Log message to console and file
 */
function log(message) {
  console.log(message);
  fs.appendFileSync(logFile, message + '\n');
}

/**
 * Make an HTTP request
 */
function makeRequest(options, postData = null) {
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          data
        });
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    if (postData) {
      req.write(postData);
    }
    
    req.end();
  });
}

/**
 * Test download music API endpoint
 */
async function testDownloadMusicAPI() {
  log('=== Testing Download Music API ===');
  
  // Test with JSON Content-Type
  try {
    const jsonOptions = {
      hostname: config.host,
      port: config.port,
      path: config.endpoints.download,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    };
    
    const jsonData = JSON.stringify({ url: config.testUrl });
    
    log('Testing with JSON Content-Type...');
    const jsonResponse = await makeRequest(jsonOptions, jsonData);
    
    log(`Status Code: ${jsonResponse.statusCode}`);
    log(`Headers: ${JSON.stringify(jsonResponse.headers)}`);
    
    if (jsonResponse.statusCode === 200) {
      log('✅ JSON Content-Type test PASSED');
    } else {
      log(`❌ JSON Content-Type test FAILED with status ${jsonResponse.statusCode}`);
      log(`Response: ${jsonResponse.data.substring(0, 500)}...`);
    }
  } catch (error) {
    log(`❌ JSON Content-Type test ERROR: ${error.message}`);
  }
  
  // Test with Form Content-Type
  try {
    const formOptions = {
      hostname: config.host,
      port: config.port,
      path: config.endpoints.download,
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    };
    
    const formData = `url=${encodeURIComponent(config.testUrl)}`;
    
    log('\nTesting with Form Content-Type...');
    const formResponse = await makeRequest(formOptions, formData);
    
    log(`Status Code: ${formResponse.statusCode}`);
    log(`Headers: ${JSON.stringify(formResponse.headers)}`);
    
    if (formResponse.statusCode === 200) {
      log('✅ Form Content-Type test PASSED');
    } else {
      log(`❌ Form Content-Type test FAILED with status ${formResponse.statusCode}`);
      log(`Response: ${formResponse.data.substring(0, 500)}...`);
    }
  } catch (error) {
    log(`❌ Form Content-Type test ERROR: ${error.message}`);
  }
}

/**
 * Run all tests
 */
async function runTests() {
  log('Starting MaiVid Studio API Tests...');
  log(`Time: ${new Date().toLocaleString()}`);
  log(`Configuration: ${JSON.stringify(config, null, 2)}\n`);
  
  try {
    await testDownloadMusicAPI();
    
    log('\nAll tests completed.');
  } catch (error) {
    log(`\n❌ Test execution failed: ${error.message}`);
  }
}

// Run the tests
runTests().catch(console.error);
