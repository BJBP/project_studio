// The blocks of the voice demo, in their default order. Visible ones: Circuito 3D, OLED, Hablar, Cerebro;
// the rest wait in «+ Añadir bloque».
import { createCircuitBlock } from './circuit-block.js';
import { createOledBlock } from './oled-block.js';
import { createTalkBlock } from './talk-block.js';
import { createBrainBlock } from './brain-block.js';
import { createConversationBlock } from './conversation-block.js';
import { createDevicesBlock } from './devices-block.js';
import { createModesBlock } from './modes-block.js';
import { createCameraBlock } from './camera-block.js';

// A catalog may list the blocks shown at first ("blocks": ["devices", "modes"]); the rest stay in «+ Añadir bloque».
export function createDemoBlocks(ctx) {
  const shown = ctx.catalog?.blocks;
  const blocks = [
    createCircuitBlock(ctx),
    createOledBlock(ctx),
    createTalkBlock(ctx),
    createBrainBlock(ctx),
    createModesBlock(ctx),
    createCameraBlock(ctx),
    createConversationBlock(ctx),
    createDevicesBlock(ctx),
  ];
  return shown ? blocks.map((block) => ({ ...block, defaultVisible: shown.includes(block.id) })) : blocks;
}
