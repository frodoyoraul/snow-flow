const snow = require('./skills/snowflow/snowflow');

async function listAllVariables() {
  const result = await snow.queryRecords('item_option_new', 'cat_item=68a7f85d472f7290a3978f59e16d43af', {
    fields: 'sys_id,name,mandatory',
    limit: 100
  });
  
  console.log(`Total variables definidas: ${result.records.length}\n`);
  result.records.forEach(r => {
    const name = r.name?.value || r.name || r.name?.display_value || '???';
    const mandatory = r.mandatory?.value !== undefined ? r.mandatory.value : r.mandatory;
    console.log(`- ${name} (mandatory: ${mandatory})`);
  });
}

listAllVariables().catch(console.error);
