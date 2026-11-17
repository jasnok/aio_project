// No dependencies. Reads actual Set assignments, IF expressions and connections.
// This harness models n8n item routing; it is not a live HTTP/Webhook test.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const filename = process.argv[2] || path.join(__dirname, 'rock-paper-scissors.workflow.json');
const workflow = JSON.parse(fs.readFileSync(filename, 'utf8'));
const nodes = new Map(workflow.nodes.map(n => [n.name, n]));
let cases = 0;
function test(name, fn) { fn(); cases++; console.log(`PASS ${name}`); }
function expression(value, json, math = Math) {
  if (typeof value !== 'string' || !value.startsWith('=')) return value;
  assert.match(value, /^=\{\{[\s\S]*\}\}$/);
  return vm.runInNewContext(`(${value.slice(3, -2)})`, { $json: json, Math: math }, { timeout: 1000 });
}
function executeSet(node, json, random) {
  assert.equal(node.parameters.mode, 'manual');
  const math = Object.create(Math); math.random = random;
  const output = node.parameters.includeOtherFields ? { ...json } : {};
  for (const field of node.parameters.assignments.assignments) {
    const value = expression(field.value, json, math);
    assert.equal(typeof value, field.type);
    output[field.name] = value;
  }
  return JSON.parse(JSON.stringify(output));
}
function branch(node, json) {
  const filter = node.parameters.conditions;
  assert.equal(filter.combinator, 'and');
  assert.equal(filter.options.typeValidation, 'strict');
  assert.equal(filter.conditions.length, 1);
  const condition = filter.conditions[0];
  assert.deepEqual(condition.operator, { type: 'boolean', operation: 'true', singleValue: true });
  const value = expression(condition.leftValue, json);
  assert.equal(typeof value, 'boolean');
  return value === true ? 0 : 1;
}
function run(body, randomValue = 0) {
  let name = 'RPS webhook';
  let json = { body };
  let randomCalls = 0;
  const visited = [], responses = [];
  while (name) {
    assert.ok(!visited.includes(name), 'cycle');
    visited.push(name);
    const node = nodes.get(name);
    let port = 0;
    switch (node.type) {
      case 'n8n-nodes-base.webhook': break;
      case 'n8n-nodes-base.set':
        json = executeSet(node, json, () => { randomCalls++; return randomValue; });
        break;
      case 'n8n-nodes-base.if': port = branch(node, json); break;
      case 'n8n-nodes-base.respondToWebhook':
        assert.equal(node.parameters.respondWith, 'json');
        responses.push({ status: node.parameters.options.responseCode,
          body: JSON.parse(JSON.stringify(expression(node.parameters.responseBody, json))) });
        break;
      default: throw Error(`Unexpected node ${node.type}`);
    }
    const edges = workflow.connections[name]?.main[port] || [];
    assert.ok(edges.length <= 1, 'unexpected response fan-out');
    name = edges[0]?.node;
  }
  assert.equal(responses.length, 1, 'each request must reach exactly one response');
  return { ...responses[0], visited, randomCalls };
}
test('JSON, unique IDs/names, supported node versions and complete acyclic graph', () => {
  assert.equal(workflow.active, false);
  assert.equal(workflow.settings.executionOrder, 'v1');
  assert.equal(nodes.size, workflow.nodes.length);
  assert.equal(new Set(workflow.nodes.map(n => n.id)).size, nodes.size);
  const versions = { webhook: 2, set: 3.4, if: 2.2, respondToWebhook: 1.1 };
  for (const node of workflow.nodes) {
    assert.ok(node.id && node.name && node.parameters);
    assert.equal(node.typeVersion, versions[node.type.split('.')[1]]);
    assert.equal(node.position.length, 2);
    assert.ok(node.position.every(Number.isFinite));
    assert.ok(!node.credentials && !node.disabled && !node.continueOnFail);
    assert.ok(!/\.(code|function|functionItem)$/.test(node.type));
    assert.ok(!('jsCode' in node.parameters));
  }
  const seen = new Set(), stack = new Set();
  function visit(name) {
    assert.ok(nodes.has(name));
    assert.ok(!stack.has(name), 'cycle');
    if (seen.has(name)) return;
    stack.add(name);
    for (const edges of workflow.connections[name]?.main || []) for (const e of edges) {
      assert.equal(e.type, 'main'); assert.equal(e.index, 0); visit(e.node);
    }
    stack.delete(name); seen.add(name);
  }
  for (const source of Object.keys(workflow.connections)) assert.ok(nodes.has(source));
  visit('RPS webhook'); assert.equal(seen.size, nodes.size);
  const webhook = nodes.get('RPS webhook').parameters;
  assert.equal(webhook.httpMethod, 'POST');
  assert.equal(webhook.responseMode, 'responseNode');
  assert.equal(webhook.path, 'rock-paper-scissors');
});
const matrix = [
  ['바위', '바위', '무승부'], ['바위', '보', '컴퓨터 승리'], ['바위', '가위', '사용자 승리'],
  ['보', '바위', '사용자 승리'], ['보', '보', '무승부'], ['보', '가위', '컴퓨터 승리'],
  ['가위', '바위', '컴퓨터 승리'], ['가위', '보', '사용자 승리'], ['가위', '가위', '무승부'],
];
const choices = ['바위', '보', '가위'];
for (const [user, computer, expected] of matrix) test(`9-way: ${user}/${computer} -> ${expected}`, () => {
  const response = run({ choice: user }, (choices.indexOf(computer) + 0.5) / 3);
  assert.deepEqual(response.body, { ok: true, userChoice: user, computerChoice: computer,
    result: expected, message: `사용자: ${user}, 컴퓨터: ${computer} — ${expected}!` });
  assert.equal(response.status, 200); assert.equal(response.randomCalls, 1);
  assert.ok(!response.visited.includes('Respond 400'));
});
for (const [value, expected] of [
  ['바위', '바위'], ['보', '보'], ['가위', '가위'], ['R', '바위'], ['P', '보'], ['S', '가위'],
  ['r', '바위'], ['p', '보'], ['s', '가위'], [' R ', '바위'], [' p ', '보'], ['\tS\n', '가위'],
  [' 바위 ', '바위'], ['\t보\n', '보'], [' 가위 ', '가위'],
]) test(`normalize ${JSON.stringify(value)}`, () => {
  const response = run({ choice: value });
  assert.equal(response.status, 200); assert.equal(response.body.userChoice, expected);
});
const invalidBodies = [undefined, null, {}, [], '바위', 7, true, { Choice: 'R' },
  ...[undefined, '', ' ', '\t\n', 'rock', 'paper', 'scissors', 'RR', '바 위', '주먹',
    'constructor', '__proto__', 'toString', 0, 1, -1, 3.14, null, false, true, [], ['R'], {},
    { toString: 'R' }].map(choice => ({ choice })),
  { body: { choice: 'R' } }, { choice: '', computerChoice: '가위' },
];
invalidBodies.forEach((body, index) => test(`invalid input #${index + 1}`, () => {
  const response = run(body);
  assert.equal(response.status, 400);
  assert.deepEqual(response.body, { ok: false, error: 'INVALID_CHOICE',
    message: '바위, 보, 가위 또는 R, P, S 중 하나를 입력하세요.' });
  assert.equal(response.randomCalls, 0);
  assert.ok(!response.visited.includes('Computer choice'));
  assert.ok(!response.visited.includes('Draw?'));
  assert.equal(response.visited.at(-1), 'Respond 400');
}));
for (const [value, expected] of [
  [0, '바위'], [1 / 3 - Number.EPSILON, '바위'], [1 / 3, '보'],
  [0.5, '보'], [2 / 3 - Number.EPSILON, '보'], [2 / 3, '가위'],
  [1 - Number.EPSILON, '가위'],
]) test(`random boundary ${value}`, () => {
  const response = run({ choice: 'R' }, value);
  assert.equal(response.body.computerChoice, expected); assert.equal(response.randomCalls, 1);
});
test('Webhook input cannot override random computer choice or result', () => {
  const response = run({ choice: 'R', computerChoice: '가위', random: 0.99,
    forceComputerChoice: '가위', result: '사용자 승리', valid: false }, 0);
  assert.equal(response.body.computerChoice, '바위'); assert.equal(response.body.result, '무승부');
  assert.equal(response.randomCalls, 1);
});
console.log(`SUCCESS: ${cases} tests; workflow configuration evaluated directly; no statistical uniformity claim.`);
