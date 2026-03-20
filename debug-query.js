const snow = require('./skills/snowflow/snowflow');

async function debugQuery() {
  const ritmSysId = '77054cbc47773654a3978f59e16d431a';
  const mtom = await snow.queryRecords('sc_item_option_mtom', `request_item=${ritmSysId}`, {
    fields: 'sc_item_option',
    limit: 100
  });
  console.log('MTOM records raw:', JSON.stringify(mtom, null, 2));
  
  const optionSysIds = mtom.records
    .map(r => r.sc_item_option?.value || r.sc_item_option)
    .filter(Boolean);
  console.log('Option sys_ids:', optionSysIds);
  
  if (optionSysIds.length > 0) {
    const result = await snow.queryTable('sc_item_option', `sys_id=${optionSysIds[0]}`, 'item_option_new,value', 1, undefined, undefined, true);
    console.log('QueryTable result raw:', JSON.stringify(result, null, 2));
  }
}

debugQuery();
