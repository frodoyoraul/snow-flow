const snow = require('./skills/snowflow/snowflow');

async function testOrder() {
  try {
    console.log('1. Creando sc_request...');
    const request = await snow.createRecord('sc_request', {
      requested_for: 'test.user',
      opened_by: 'test.user'
    });
    console.log('   sc_request:', request.sys_id);

    console.log('2. Creando sc_req_item (RITM)...');
    const ritm = await snow.createRecord('sc_req_item', {
      request: request.sys_id,
      cat_item: '68a7f85d472f7290a3978f59e16d43af',
      requested_for: 'test.user',
      quantity: 1
    });
    console.log('   sc_req_item:', ritm.sys_id, ritm.number);

    console.log('3. Consultando variables del catálogo...');
    const varDefsResult = await snow.queryRecords(
      'item_option_new',
      `cat_item=68a7f85d472f7290a3978f59e16d43af`,
      { fields: 'sys_id,name', limit: 100 }
    );
    const varDefs = varDefsResult.records || [];
    console.log(`   Encontradas: ${varDefs.length} variables`);
    const nameToSysId = {};
    varDefs.forEach(def => {
      const name = def.name?.value || def.name?.display_value || def.name;
      const sysId = def.sys_id?.value || def.sys_id?.display_value || def.sys_id;
      if (name && sysId) nameToSysId[name] = sysId;
    });
    console.log('   Mapa construido. Variables disponibles:', Object.keys(nameToSysId).slice(0,5));

    console.log('4. Creando sc_item_option y sc_item_option_mtom...');
    const variables = {
      first_name: 'Test',
      last_name: 'User',
      personal_email: 'test.user@example.com'
    };
    let count = 0;
    for (const [varName, varValue] of Object.entries(variables)) {
      const itemOptionId = nameToSysId[varName];
      if (!itemOptionId) {
        console.warn(`   Saltando ${varName} (no encontrada)`);
        continue;
      }
      console.log(`   Creando sc_item_option para ${varName}...`);
      const option = await snow.createRecord('sc_item_option', {
        item_option_new: itemOptionId,
        value: varValue
      });
      console.log(`     sc_item_option: ${option.sys_id}`);
      console.log(`     Creando sc_item_option_mtom...`);
      await snow.createRecord('sc_item_option_mtom', {
        request_item: ritm.sys_id,
        item_option: option.sys_id
      });
      count++;
    }
    console.log(`   Total creadas: ${count}`);

    console.log('\n✅ ÉXITO');
  } catch (err) {
    console.error('\n❌ ERROR:', err.message);
    console.error(err.stack);
  }
}

testOrder();
