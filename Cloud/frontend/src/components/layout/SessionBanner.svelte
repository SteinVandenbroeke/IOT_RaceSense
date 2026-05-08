<script lang="ts">
	import { globalSocket } from '$lib/communcation/globalSocket.svelte';

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

	<div class="flex items-center gap-2 bg-zinc-950 border border-zinc-800 rounded-lg p-1.5 shadow-inner">
		<span class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mr-2 ml-2 hidden lg:inline">Track Status:</span>

		<button
			onclick={() => globalSocket.setTrackFlag('Green')}
			class="group flex items-center gap-2 px-4 py-1.5 rounded transition-all duration-300 border {currentFlag === 'Green' ? 'bg-emerald-500/20 border-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.2)]' : 'bg-transparent border-transparent hover:bg-zinc-900'}"
		>
			<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
				stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
				class="transition-colors duration-300 {currentFlag === 'Green' ? 'text-emerald-500 fill-emerald-500' : 'text-zinc-600 fill-transparent group-hover:text-zinc-400'}">
				<path d="M4 22V4a1 1 0 0 1 .4-.8A6 6 0 0 1 8 2c3 0 5 2 7.333 2q2 0 3.067-.8A1 1 0 0 1 20 4v10a1 1 0 0 1-.4.8A6 6 0 0 1 16 16c-3 0-5-2-8-2a6 6 0 0 0-4 1.528"/>
			</svg>
			<span class="text-xs font-black uppercase tracking-wider {currentFlag === 'Green' ? 'text-emerald-400' : 'text-zinc-600 group-hover:text-zinc-400'}">Green</span>
		</button>

		<button
			onclick={() => globalSocket.setTrackFlag('Yellow')}
			class="group flex items-center gap-2 px-4 py-1.5 rounded transition-all duration-300 border {currentFlag === 'Yellow' ? 'bg-yellow-500/20 border-yellow-500/50 shadow-[0_0_15px_rgba(234,179,8,0.2)]' : 'bg-transparent border-transparent hover:bg-zinc-900'}"
		>
			<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
				stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
				class="transition-colors duration-300 {currentFlag === 'Yellow' ? 'text-yellow-500 fill-yellow-500' : 'text-zinc-600 fill-transparent group-hover:text-zinc-400'}">
				<path d="M4 22V4a1 1 0 0 1 .4-.8A6 6 0 0 1 8 2c3 0 5 2 7.333 2q2 0 3.067-.8A1 1 0 0 1 20 4v10a1 1 0 0 1-.4.8A6 6 0 0 1 16 16c-3 0-5-2-8-2a6 6 0 0 0-4 1.528"/>
			</svg>
			<span class="text-xs font-black uppercase tracking-wider {currentFlag === 'Yellow' ? 'text-yellow-400' : 'text-zinc-600 group-hover:text-zinc-400'}">Yellow</span>
		</button>

		<button
			onclick={() => globalSocket.setTrackFlag('Red')}
			class="group flex items-center gap-2 px-4 py-1.5 rounded transition-all duration-300 border {currentFlag === 'Red' ? 'bg-red-500/20 border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.2)]' : 'bg-transparent border-transparent hover:bg-zinc-900'}"
		>
			<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
				stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
				class="transition-colors duration-300 {currentFlag === 'Red' ? 'text-red-500 fill-red-500' : 'text-zinc-600 fill-transparent group-hover:text-zinc-400'}">
				<path d="M4 22V4a1 1 0 0 1 .4-.8A6 6 0 0 1 8 2c3 0 5 2 7.333 2q2 0 3.067-.8A1 1 0 0 1 20 4v10a1 1 0 0 1-.4.8A6 6 0 0 1 16 16c-3 0-5-2-8-2a6 6 0 0 0-4 1.528"/>
			</svg>
			<span class="text-xs font-black uppercase tracking-wider {currentFlag === 'Red' ? 'text-red-400' : 'text-zinc-600 group-hover:text-zinc-400'}">Red</span>
		</button>
	</div>

</div>