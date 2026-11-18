import test from "node:test";
import assert from "node:assert/strict";
import { stateTopic, commandTopic, availabilityTopic } from "../../web/demos/voice/js/domain/topics.js";

test("builds state, command and availability topics", () => {
  assert.equal(stateTopic("studio", "circuito_maestro", "foco"), "studio/circuito_maestro/foco/state");
  assert.equal(commandTopic("studio", "circuito_maestro", "foco"), "studio/circuito_maestro/foco/set");
  assert.equal(availabilityTopic("studio", "circuito_maestro"), "studio/circuito_maestro/status");
});

test("uses the given base topic verbatim", () => {
  assert.equal(stateTopic("home/lab", "dev1", "k"), "home/lab/dev1/k/state");
});

test("topics differ only in their suffix", () => {
  const state = stateTopic("b", "d", "k");
  const command = commandTopic("b", "d", "k");
  assert.ok(state.endsWith("/state"));
  assert.ok(command.endsWith("/set"));
  assert.notEqual(state, command);
});
