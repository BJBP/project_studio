// How a simulated sensor moves, declared in the catalog ("sim"). nextReading(sim, current, random) -> new value.
// drift: wanders by up to ±step inside [min, max]; other types only change when someone tests them.
export function nextReading(sim, current, random = Math.random) {
  if (!sim || sim.type !== "drift") return current;
  const start = Number.isFinite(current) ? current : sim.rest ?? sim.min;
  const moved = start + (random() * 2 - 1) * sim.step;
  return Math.round(Math.min(sim.max, Math.max(sim.min, moved)) * 10) / 10;
}

// The value a test puts on an entity and the value it goes back to.
export function testValues(entity) {
  if (entity.component === "binary_sensor") return { on: "ON", off: "OFF" };
  return { on: entity.sim?.test ?? entity.sim?.max ?? 1, off: entity.sim?.rest ?? 0 };
}
