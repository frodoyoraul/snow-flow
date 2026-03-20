const snow = require('./skills/snowflow/snowflow');

async function listAllVariables() {
  const result = await snow.queryRecords('item_option_new', 'cat_item=68a7f85d472f7290a3978f59e16d43af', {
    fields: 'sys_id,name,question_text,type,mandatory,order',
    limit: 100
  });
  
  console.log(`Total variables definidas para el catálogo: ${result.records.length}\n`);
  console.log('Name'.padEnd(25) + 'Question Text'.padEnd(30) + 'Type'.padEnd(8) + 'Mandatory');
  console.log('-'.repeat(70));
  
  result.records.forEach(r => {
    const name = r.name?.value || r.name || '';
    const qtext = r.question_text?.value || r.question_text || '';
    const type = r.type?.value || r.type || '';
    const mandatory = r.mandatory?.value !== undefined ? r.mandatory.value : (r.mandatory || '');
    console.log(name.substring(0,25).padEnd(25) + qtext.substring(0,30).padEnd(30) + String(type).substring(0,8).padEnd(8) + String(mandatory));
  });
}

listAllVariables().catch(console.error);
