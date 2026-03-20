// Forzar recarga de la skill
delete require.cache[require.resolve('./skills/snowflow/snowflow')];
const snow = require('./skills/snowflow/snowflow');

async function testRead() {
  const ritmSysId = '77054cbc47773654a3978f59e16d431a'; // RITM0010074
  console.log('Leyendo valores para RITM sys_id:', ritmSysId);
  
  try {
    const vals = await snow.getRITMVariableValues(ritmSysId);
    console.log('Variables encontradas:', vals.length);
    vals.forEach(v => console.log(`  ${v.variable_name}: ${v.value}`));
  } catch (err) {
    console.error('ERROR:', err.message);
    console.error(err.stack);
  }
}

testRead();
