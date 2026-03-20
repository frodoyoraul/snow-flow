const snow = require('./skills/snowflow/snowflow');

async function test() {
  try {
    console.log('Creando sc_request...');
    const req = await snow.createRecord('sc_request', { requested_for: 'test.user', opened_by: 'test.user' });
    console.log('sc_request creado:', req.sys_id);

    console.log('Creando sc_req_item...');
    const ritm = await snow.createRecord('sc_req_item', {
      request: req.sys_id,
      cat_item: '68a7f85d472f7290a3978f59e16d43af',
      requested_for: 'test.user',
      quantity: 1
    });
    console.log('sc_req_item creado:', ritm.sys_id, ritm.number);

    console.log('Consultando variables del catálogo...');
    const varDefs = await snow.queryRecords('item_option_new', `cat_item=68a7f85d472f7290a3978f59e16d43af`, { fields: 'sys_id,name', limit: 10 });
    console.log('Variables encontradas:', varDefs.records.length);
    varDefs.records.forEach(r => {
      const name = r.name?.value || r.name;
      const sysId = r.sys_id?.value || r.sys_id;
      console.log(`  ${name}: ${sysId}`);
    });

  } catch (err) {
    console.error('ERROR:', err.message);
  }
}

test();
