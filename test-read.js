const snow = require('./skills/snowflow/snowflow');

async function testRead() {
  const ritmSysId = '9ec40c7c47773654a3978f59e16d43b8';
  try {
    const values = await snow.getRITMVariableValues(ritmSysId);
    console.log('Variables encontradas:', values.length);
    values.forEach(v => console.log(`  ${v.variable_name}: ${v.value}`));
  } catch (err) {
    console.error('ERROR:', err.message);
  }
}

testRead();
