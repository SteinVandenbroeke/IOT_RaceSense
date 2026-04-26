<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { globalSocket } from '$lib/communcation/globalSocket.svelte';
	import './layout.css';
	let { children } = $props();

	let isMenuOpen = $state(false);
	const closeMenu = () => (isMenuOpen = false);

	const navLinks = [
		{ name: 'Dashboard Overview', href: '/', icon: '🏁' },
		{ name: 'Live Telemetry', href: '/live', icon: '📡' },
		{ name: 'Lap Analytics', href: '/analytics', icon: '📈' },
		{ name: 'Vehicle Settings', href: '/settings', icon: '🔧' }
	];

	// 1. Define the strict racing presets
	type SessionMode =
		| { type: 'Practice'; timeRemaining: string }
		| { type: 'Qualifying'; timeRemaining: string }
		| { type: 'Race'; format: 'time'; timeRemaining: string }
		| { type: 'Race'; format: 'laps'; currentLap: number; totalLaps: number };

	type FlagType = 'Green' | 'Yellow' | 'Double Yellow' | 'Red' | 'SC' | 'VSC';
	type WeatherType = 'Sunny' | 'Cloudy' | 'Light Rain' | 'Heavy Rain' | 'Dry';

	// 2. The master state interface
	interface session {
		isActive: boolean;
		location: string;
		mode: SessionMode;
		trackTemp: number;
		flag: FlagType;
		weather: WeatherType;
	}

	// 3. Mock Data (Change this to test the presets!)
	let session: session = $state({
		isActive: true,
		location: 'Spa-Francorchamps',
		mode: { type: 'Race', format: 'laps', currentLap: 12, totalLaps: 44 },
		trackTemp: 22.5,
		flag: 'Green',
		weather: 'Light Rain'
	});

	// Helpers for visual UI
	const weatherIcons: Record<WeatherType, string> = {
		'Sunny': '☀️', 'Cloudy': '☁️', 'Light Rain': '🌦️', 'Heavy Rain': '🌧️', 'Dry': '🌤️'
	};

	const flagColors: Record<FlagType, string> = {
		'Green': 'bg-emerald-500 animate-pulse',
		'Yellow': 'bg-yellow-400 animate-pulse',
		'Double Yellow': 'bg-yellow-400 animate-pulse',
		'Red': 'bg-red-500 animate-ping',
		'SC': 'bg-yellow-400 text-black font-black flex items-center justify-center',
		'VSC': 'bg-yellow-400 text-black font-black flex items-center justify-center'
	};
	onMount(() => {
		globalSocket.connect();
	});

	onDestroy(() => {
		// Cleans up the connection if the user navigates away from the app
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
		<main class="flex-1 overflow-y-auto">

			{#if session.isActive}
				<section
					role="alert"
					aria-live="polite"
					class="bg-zinc-900 border-b border-zinc-800 px-4 py-3 sm:px-6 grid grid-cols-1 lg:grid-cols-3 items-center gap-4 shadow-md"
				>
					<div class="flex items-center justify-start gap-4">
						<div
							class="w-8 h-6 rounded-sm shadow-sm border border-black/20 {flagColors[session.flag]}"
							title="Current Track Status: {session.flag}"
						>
							{#if session.flag === 'SC' || session.flag === 'VSC'}
								<span class="text-[10px] tracking-tighter text-black font-black flex items-center justify-center h-full">
									{session.flag}
								</span>
							{/if}
						</div>

						<h2 class="text-sm font-bold text-white uppercase tracking-wide flex items-center gap-2">
							{session.mode.type}
							<span class="text-zinc-600 font-normal">|</span>
							<span class="text-zinc-300 font-mono">
								{#if session.mode.type === 'Race' && session.mode.format === 'laps'}
									LAP {session.mode.currentLap} / {session.mode.totalLaps}
								{:else}
									{session.mode.timeRemaining} REMAINING
								{/if}
							</span>
						</h2>
					</div>

					<div class="hidden lg:flex justify-center items-center">
						<span class="text-sm font-black text-emerald-400 tracking-widest uppercase flex items-center gap-2">
							<svg class="w-4 h-4 text-emerald-500/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.243-4.243a8 8 0 1111.314 0z" />
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
							</svg>
							{session.location}
						</span>
					</div>

					<div class="flex items-center justify-end gap-6 text-xs font-mono">
						<div class="flex items-center gap-2" title={session.weather}>
							<span class="text-lg" aria-hidden="true">{weatherIcons[session.weather]}</span>
							<span class="text-zinc-300 hidden xl:inline">{session.weather}</span>
						</div>

						<div class="flex items-center gap-2">
							<span class="text-zinc-500 uppercase text-[10px]">Track</span>
							<span class="text-zinc-200 tabular-nums">{session.trackTemp}°C</span>
						</div>

						<a
							href="/live"
							class="hidden md:flex ml-2 bg-zinc-100 hover:bg-white text-zinc-950 px-4 py-1.5 rounded text-xs font-bold uppercase transition-colors"
						>
							View
						</a>
					</div>
					<div class="status-badge">
						{#if globalSocket.isConnected}
							🟢 Online
						{:else}
							🔴 Offline
						{/if}
					</div>
				</section>
			{/if}

			<div class="p-4 sm:p-6">
				{@render children()}
			</div>
		</main>
	</div>
</div>
