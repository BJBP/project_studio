import test from "node:test";
import assert from "node:assert/strict";
import { oledLayout } from "../../web/demos/voice/js/domain/oled.js";

test("truncates the header to 21 characters", () => {
  const { header } = oledLayout({ header: "x".repeat(30), body: "" });
  assert.equal(header.length, 21);
});

test("wraps body text into 21-char lines", () => {
  const { lines } = oledLayout({ header: "h", body: "uno dos tres cuatro cinco seis siete ocho nueve diez once doce" });
  assert.ok(lines.length <= 6);
  assert.ok(lines.every((l) => l.length <= 21));
  assert.equal(lines[0], "uno dos tres cuatro");
});

test("cuts a word longer than 21 characters", () => {
  const { lines } = oledLayout({ header: "h", body: "a".repeat(45) });
  assert.equal(lines[0], "a".repeat(21));
  assert.equal(lines[1], "a".repeat(21));
  assert.equal(lines[2], "a".repeat(3));
});

test("caps at 6 lines and ends the last one with an ellipsis", () => {
  const body = Array.from({ length: 40 }, (_, i) => `palabra${i}`).join(" ");
  const { lines } = oledLayout({ header: "h", body });
  assert.equal(lines.length, 6);
  assert.ok(lines[5].endsWith("…"));
  assert.ok(lines[5].length <= 21);
});
