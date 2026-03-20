const snow = require('./skills/snowflow/snowflow');

async function testCreate() {
  try {
    console.log('Intentando crear sc_request con createRecord...');
    const req = await snow.createRecord('sc_request', { requested_for: 'test.user', opened_by: 'test.user' });
    console.log('ÉXITO:', req.sys_id);
  } catch (err) {
    console.error('ERROR:', err.message);
  }
}

testCreate();
