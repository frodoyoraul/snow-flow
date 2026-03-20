const snow = require('./skills/snowflow/snowflow');

async function testOneVar() {
  try {
    const result = await snow.orderCatalogItem(
      '68a7f85d472f7290a3978f59e16d43af',
      'test.user',
      { first_name: 'Test' }
    );
    console.log('\n✅ FIN:', result);
  } catch (err) {
    console.error('\n❌ ERROR:', err.message);
  }
}

testOneVar();
