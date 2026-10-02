import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import ts from 'typescript';

function client(fetch) {
  const source = fs.readFileSync(path.join(import.meta.dirname, '../src/lib/api.ts'), 'utf8');
  const compiled = ts.transpileModule(source, {compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022}}).outputText;
  const loaded = {exports: {}};
  const requireStub = name => {
    if (name === 'server-only') return {};
    if (name === 'react') return {cache: fn => fn};
    if (name === './env') return {API_URL: 'https://api.example.test/api/v1/'};
    throw new Error(`Unexpected runtime import: ${name}`);
  };
  new Function('require', 'module', 'exports', 'fetch', compiled)(requireStub, loaded, loaded.exports, fetch);
  return loaded.exports;
}

test('localized reads preserve the API base, pagination, cache tags and timeout', async () => {
  const api = client(async (url, options) => {
    const parsed = new URL(url);
    assert.equal(parsed.origin, 'https://api.example.test');
    assert.equal(parsed.pathname, '/api/v1/products/');
    assert.equal(parsed.searchParams.get('lang'), 'ar');
    assert.equal(parsed.searchParams.get('page'), '2');
    assert.equal(parsed.searchParams.get('service'), 'web-development');
    assert.equal(parsed.searchParams.has('category'), false);
    assert.equal(options.next.revalidate, 300);
    assert.deepEqual(options.next.tags, ['products']);
    assert.ok(options.signal instanceof AbortSignal);
    return Response.json({count: 13, next: null, previous: null, results: []});
  });
  assert.equal((await api.getProducts('ar', {page: 2, service: 'web-development', category: ''})).count, 13);
});

test('missing or gated site settings return null, while outages fail visibly', async () => {
  const missing = client(async () => new Response('', {status: 404}));
  assert.equal(await missing.getSiteSettings('en'), null);
  const unavailable = client(async () => new Response('private upstream body', {status: 503}));
  await assert.rejects(unavailable.getSiteSettings('en'), error => {
    assert.equal(error.status, 503);
    assert.equal(error.message.includes('private upstream body'), false);
    return true;
  });
});

test('network failures and malformed JSON are not mistaken for empty content', async () => {
  const offline = client(async () => {throw new TypeError('network unavailable');});
  await assert.rejects(offline.getServices('en'), /network unavailable/);
  const malformed = client(async () => new Response('not JSON'));
  await assert.rejects(malformed.getServices('en'), SyntaxError);
});

test('transport rejects external, traversing or query-bearing endpoint paths before fetch', async () => {
  const api = client(async () => {throw new Error('must not fetch');});
  for (const path of ['https://other.test/', '//other.test/', '/../admin/', '/services/?lang=ar', '/services/../admin/']) {
    await assert.rejects(api.apiGet(path), /relative endpoint paths/);
  }
});
