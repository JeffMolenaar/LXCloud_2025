const path = require('path');
const fs = require('fs');

console.log('🧪 LXCloud Complete Platform - Test Suite');
console.log('==========================================');

const tests = [
    {
        name: 'Project Structure',
        test: testProjectStructure
    },
    {
        name: 'Required Files',
        test: testRequiredFiles
    },
    {
        name: 'Dependencies',
        test: testDependencies
    },
    {
        name: 'Database Module',
        test: testDatabaseModule
    },
    {
        name: 'MQTT Module',
        test: testMQTTModule
    },
    {
        name: 'Authentication Module',
        test: testAuthModule
    },
    {
        name: 'Setup Script',
        test: testSetupScript
    },
    {
        name: 'Update Script',
        test: testUpdateScript
    }
];

async function runTests() {
    let passed = 0;
    let failed = 0;
    
    console.log(`\nRunning ${tests.length} tests...\n`);
    
    for (let i = 0; i < tests.length; i++) {
        const test = tests[i];
        process.stdout.write(`${i + 1}. Testing ${test.name}...`);
        
        try {
            await test.test();
            console.log(' ✅ PASSED');
            passed++;
        } catch (error) {
            console.log(` ❌ FAILED: ${error.message}`);
            failed++;
        }
    }
    
    console.log('\n==========================================');
    console.log(`📊 Test Results: ${passed}/${tests.length} tests passed`);
    
    if (failed === 0) {
        console.log('🎉 All tests passed! LXCloud is ready to use.');
    } else {
        console.log('⚠️  Some tests failed. Check the output above for details.');
    }
    
    console.log('==========================================');
}

async function testProjectStructure() {
    const requiredDirs = ['config', 'routes', 'models', 'controllers', 'middleware', 'services', 'views', 'public'];
    
    for (const dir of requiredDirs) {
        if (!fs.existsSync(dir)) {
            throw new Error(`Missing required directory: ${dir}`);
        }
    }
}

async function testRequiredFiles() {
    const requiredFiles = [
        'server.js',
        'package.json',
        'setup.sh',
        'update.sh',
        'README.md',
        'test.js'
    ];
    
    for (const file of requiredFiles) {
        if (!fs.existsSync(file)) {
            throw new Error(`Missing required file: ${file}`);
        }
    }
}

async function testDependencies() {
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    const requiredDeps = ['express', 'mysql2', 'mqtt', 'socket.io', 'bcryptjs'];
    
    for (const dep of requiredDeps) {
        if (!packageJson.dependencies[dep]) {
            throw new Error(`Missing required dependency: ${dep}`);
        }
    }
}

async function testDatabaseModule() {
    try {
        const database = require('./config/database');
        if (!database) {
            throw new Error('Database module did not export anything');
        }
    } catch (error) {
        throw new Error(`Database module failed to load: ${error.message}`);
    }
}

async function testMQTTModule() {
    try {
        const mqttController = require('./controllers/mqttController');
        if (!mqttController) {
            throw new Error('MQTT module did not export anything');
        }
    } catch (error) {
        throw new Error(`MQTT module failed to load: ${error.message}`);
    }
}

async function testAuthModule() {
    try {
        const authRoutes = require('./routes/auth');
        if (!authRoutes) {
            throw new Error('Auth module did not export anything');
        }
    } catch (error) {
        throw new Error(`Auth module failed to load: ${error.message}`);
    }
}

async function testSetupScript() {
    if (!fs.existsSync('setup.sh')) {
        throw new Error('Setup script not found');
    }
    
    const stats = fs.statSync('setup.sh');
    if (!(stats.mode & parseInt('100', 8))) {
        throw new Error('Setup script is not executable');
    }
}

async function testUpdateScript() {
    if (!fs.existsSync('update.sh')) {
        throw new Error('Update script not found');
    }
    
    const stats = fs.statSync('update.sh');
    if (!(stats.mode & parseInt('100', 8))) {
        throw new Error('Update script is not executable');
    }
}

// Run the tests
runTests().catch(console.error);