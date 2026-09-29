const test = require('node:test');
const assert = require('node:assert/strict');
const units = require('../frontend/scripts/measurements.js');
test('feet and inches use exact centimetre conversion',()=>assert.equal(units.height(5,'ft',6),167.64000000000001));
test('metres and pounds convert correctly',()=>{assert.equal(units.height(1.7,'m'),170);assert.ok(Math.abs(units.weight(150,'lb')-68.0388555)<1e-8);});
test('invalid measurements are rejected',()=>{for(const args of [[5,'ft',12],[-1,'cm'],[5.5,'ft',0],[Infinity,'cm']])assert.ok(Number.isNaN(units.height(...args)));assert.ok(Number.isNaN(units.weight(0,'kg')));});
