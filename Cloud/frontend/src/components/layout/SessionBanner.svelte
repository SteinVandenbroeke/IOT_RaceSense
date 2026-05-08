<script lang="ts">
	import { globalSocket } from '$lib/communcation/globalSocket.svelte';

	// Svelte 5 derived state makes the UI perfectly reactive
	let currentFlag = $derived(globalSocket.trackFlag);
	let isConnected = $derived(globalSocket.isConnected);
</script>

<div class="bg-zinc-900 border-b border-zinc-800 px-4 py-3 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4 sticky top-0 z-30">

	<div class="flex items-center gap-3">
		<div class="flex items-center justify-center w-10 h-10 rounded bg-zinc-950 border border-zinc-800">
			<svg class="w-5 h-5 {isConnected ? 'text-emerald-500' : 'text-red-500'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
			</svg>
		</div>
		<div>
			<h2 class="text-sm font-bold text-white flex items-center gap-2">
				Race Control Uplink
				<span class="w-2 h-2 rounded-full {isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}"></span>
			</h2>
			<p class="text-[10px] text-zinc-400 font-mono uppercase tracking-wider">
				{isConnected ? 'System Online • Receiving' : 'Offline • Waiting for Hardware...'}
			</p>
		</div>
	</div>

	<div class="flex items-center gap-1.5 bg-zinc-950 border border-zinc-800 rounded-lg p-1.5 shadow-inner">
		<span class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mr-2 ml-2 hidden lg:inline">Track Status:</span>

		<button
			onclick={() => globalSocket.setTrackFlag('Green')}
			class="px-5 py-2 rounded text-xs font-black uppercase tracking-wider transition-all duration-300 {currentFlag === 'Green' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shadow-[0_0_10px_rgba(16,185,129,0.2)]' : 'text-zinc-600 hover:text-zinc-400 border border-transparent'}"
		>
			Green
		</button>

		<button
			onclick={() => globalSocket.setTrackFlag('Yellow')}
			class="px-5 py-2 rounded text-xs font-black uppercase tracking-wider transition-all duration-300 {currentFlag === 'Yellow' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 shadow-[0_0_10px_rgba(234,179,8,0.2)]' : 'text-zinc-600 hover:text-zinc-400 border border-transparent'}"
		>
			Yellow
		</button>

		<button
			onclick={() => globalSocket.setTrackFlag('Red')}
			class="px-5 py-2 rounded text-xs font-black uppercase tracking-wider transition-all duration-300 {currentFlag === 'Red' ? 'bg-red-500/20 text-red-400 border border-red-500/30 shadow-[0_0_10px_rgba(239,68,68,0.2)]' : 'text-zinc-600 hover:text-zinc-400 border border-transparent'}"
		>
			Red
		</button>
	</div>

</div>