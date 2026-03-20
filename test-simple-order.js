const snow = require('./skills/snowflow/snowflow');

async function testSimple() {
  try {
    const result = await snow.orderCatalogItem(
      '68a7f85d472f7290a3978f59e16d43af',
      'test.user',
      {
        first_name: 'Test',
        last_name: 'User',
        personal_email: 'test.user@example.com'
      }
    );
    console.log('RESULT:', JSON.stringify(result, null, 2));
  } catch (err) {
    console.error('ERROR:', err.message);
  }
}

testSimple();
