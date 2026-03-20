const snow = require('./skills/snowflow/snowflow');

async function testBatch() {
  const ritmSysId = '77054cbc47773654a3978f59e16d431a';
  const mtom = await snow.queryRecords('sc_item_option_mtom', `request_item=${ritmSysId}`, {
    fields: 'sc_item_option',
    limit: 100
  });
  const optionSysIds = mtom.records
    .map(r => r.sc_item_option?.value || r.sc_item_option)
    .filter(Boolean);
  
  console.log('Option sys_ids:', optionSysIds);
  
  // Probar batch de 2
  if (optionSysIds.length >= 2) {
    const batch = optionSysIds.slice(0, 2);
    const query = batch.map(id => `sys_id=${id}`).join('^');
    console.log('Query batch 2:', query);
    const result = await snow.queryRecords('sc_item_option', query, {
      fields: 'item_option_new,value',
      limit: 2,
      display_value: true
    });
    console.log('Result records:', result.records.length);
    result.records.forEach(r => {
      const varName = r.item_option_new?.display_value || 'Unknown';
      const val = r.value?.display_value || '';
      console.log(`  ${varName}: ${val}`);
    });
  }
}

testBatch();
