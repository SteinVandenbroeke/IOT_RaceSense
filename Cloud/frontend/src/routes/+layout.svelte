<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { globalSocket } from '$lib/communcation/globalSocket.svelte';
	import Sidebar from '../components/layout/Sidebar.svelte';
	import SessionBanner from '../components/layout/SessionBanner.svelte';
	import './layout.css';

	let { children } = $props();

	let isMenuOpen = $state(false);
	const closeMenu = () => (isMenuOpen = false);

	onMount(() => {
		globalSocket.loadDemoFleet(); // REMOVE this when you have the real board!
		globalSocket.connect();
	});

	onDestroy(() => {
		globalSocket.disconnect();
	});
</script>

<div class="flex h-screen bg-zinc-950 text-zinc-100 overflow-hidden">
	{#if isMenuOpen}
		<button
			class="fixed inset-0 bg-black/60 z-40 lg:hidden backdrop-blur-sm"
			onclick={closeMenu}
			aria-label="Close menu"
		></button>
	{/if}

	<Sidebar {isMenuOpen} {closeMenu} />

	<div class="flex-1 flex flex-col min-w-0">
		<main class="flex-1 overflow-y-auto">

			<SessionBanner />

			<div class="p-4 sm:p-6">
				{@render children()}
			</div>
		</main>
	</div>
</div>