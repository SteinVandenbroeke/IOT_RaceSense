<script lang="ts">
	import './layout.css';
	let { children } = $props();

	// Svelte 5 state for the mobile menu
	let isMenuOpen = $state(false);

	const navLinks = [
		{ name: 'Live Tracking', href: '/', icon: '🏎️' },
		{ name: 'History & Analytics', href: '/history', icon: '📊' },
		{ name: 'Vehicle Settings', href: '/settings', icon: '🔧' }
	];

	const closeMenu = () => (isMenuOpen = false);
</script>

<div class="flex h-screen bg-zinc-950 text-zinc-100 overflow-hidden">
	{#if isMenuOpen}
		<button 
			class="fixed inset-0 bg-black/60 z-40 lg:hidden backdrop-blur-sm" 
			onclick={closeMenu}
			aria-label="Close menu"
		></button>
	{/if}

	<aside 
		class="fixed inset-y-0 left-0 z-50 w-64 border-r border-zinc-800 bg-zinc-900 flex flex-col transition-transform duration-300 lg:translate-x-0 lg:static lg:inset-auto 
		{isMenuOpen ? 'translate-x-0' : '-translate-x-full'}"
	>
		<header class="p-6 border-b border-zinc-800 flex justify-between items-center">
			<div>
				<h1 class="text-xl font-black tracking-tighter text-emerald-500">RACESENSE</h1>
				<p class="text-xs text-zinc-500 font-mono uppercase">Telemetry v1.0</p>
			</div>
			<button class="lg:hidden p-2 text-zinc-400" onclick={closeMenu} aria-label="Close menu">
				✕
			</button>
		</header>

		<nav aria-label="Main Navigation" class="flex-1 p-4">
			<ul class="space-y-2">
				{#each navLinks as link}
					<li>
						<a
							href={link.href}
							onclick={closeMenu}
							class="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-zinc-800 transition-colors group"
						>
							<span class="text-lg" aria-hidden="true">{link.icon}</span>
							<span class="font-medium text-zinc-400 group-hover:text-white">{link.name}</span>
						</a>
					</li>
				{/each}
			</ul>
		</nav>

		<footer class="p-4 border-t border-zinc-800 bg-zinc-900/80">
			<div class="flex items-center gap-2 px-2" role="status">
				<div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
				<span class="text-xs font-mono text-zinc-400 uppercase">OBU Linked</span>
			</div>
		</footer>
	</aside>

	<div class="flex-1 flex flex-col min-w-0">
		<header class="sticky top-0 z-30 bg-zinc-950/80 backdrop-blur-md border-b border-zinc-800 p-4">
			<div class="flex justify-between items-center">
				<div class="flex items-center gap-4">
					<button 
						class="lg:hidden p-2 -ml-2 text-zinc-400 hover:text-white" 
						onclick={() => isMenuOpen = true}
						aria-label="Open menu"
					>
						<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
						</svg>
					</button>
					<h2 class="text-xs sm:text-sm font-mono uppercase tracking-widest text-zinc-500 truncate">
						Spa-Francorchamps
					</h2>
				</div>
				
				<div class="hidden sm:flex gap-4 text-xs font-mono">
					<span class="text-zinc-500">LAT: <span class="text-zinc-200">50.437</span></span>
					<span class="text-zinc-500">LON: <span class="text-zinc-200">5.971</span></span>
				</div>
			</div>
		</header>

		<main class="flex-1 overflow-y-auto p-4 sm:p-6">
			{@render children()}
		</main>
	</div>
</div>