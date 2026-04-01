// src/lib/state/socket.svelte.ts
import { WebSocketModel } from '$lib/communcation/WebSocket.svelte';

// We create ONE instance here and export it.
// Every component that imports 'globalSocket' will share this exact same connection.
export const globalSocket = new WebSocketModel('ws://localhost:8000/ws');