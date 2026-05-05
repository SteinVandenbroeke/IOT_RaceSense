<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { globalSocket } from '$lib/communcation/globalSocket.svelte';

	type SessionMode =
		| { type: 'Practice'; timeRemaining: string }
		| { type: 'Qualifying'; timeRemaining: string }
		| { type: 'Race'; format: 'time'; timeRemaining: string }
		| { type: 'Race'; format: 'laps'; currentLap: number; totalLaps: number };

	type FlagType = 'Green' | 'Yellow' | 'Double Yellow' | 'Red' | 'SC' | 'VSC';
	type WeatherType = 'Sunny' | 'Cloudy' | 'Light Rain' | 'Heavy Rain' | 'Dry';

	interface session {
		isActive: boolean;
		location: string;
		mode: SessionMode;
		trackTemp: number;
		flag: FlagType;
		weather: WeatherType;
	}

	let session: session = $state({
		isActive: true,
		location: 'Spa-Francorchamps',
		mode: { type: 'Race', format: 'laps', currentLap: 12, totalLaps: 44 },
		trackTemp: 22.5,
		flag: 'Green',
		weather: 'Light Rain'
	});

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

	// --- Carousel Logic ---
	let showLeaderGap = $state(false);
	let carouselRef: HTMLDivElement;
	let gapTimer: ReturnType<typeof setInterval>;
	let scrollTimer: ReturnType<typeof setInterval>;

	onMount(() => {
		// 1. Toggle between Gap to Ahead and Gap to Leader every 4 seconds
		gapTimer = setInterval(() => {
			showLeaderGap = !showLeaderGap;
		}, 4000);

		// 2. Auto-rotate the carousel every 3 seconds (pauses if user hovers)
		scrollTimer = setInterval(() => {
			if (carouselRef && !carouselRef.matches(':hover')) {
				// Scroll to the right by ~150px
				carouselRef.scrollBy({ left: 160, behavior: 'smooth' });

				// If we hit the end, snap smoothly back to the beginning
				if (carouselRef.scrollLeft + carouselRef.clientWidth >= carouselRef.scrollWidth - 10) {
					carouselRef.scrollTo({ left: 0, behavior: 'smooth' });
				}
			}
		}, 3000);
	});

	onDestroy(() => {
		clearInterval(gapTimer);
		clearInterval(scrollTimer);
	});

	// Derive a sorted array based on the mock position (fallback to 99 if missing)
	let sortedCars = $derived(
		Object.entries(globalSocket.cars).sort((a, b) => (a[1].position || 99) - (b[1].position || 99))
	);
</script>

{#if session.isActive}
	<section role="alert" aria-live="polite" class="bg-zinc-900 border-b border-zinc-800 px-4 py-2 sm:px-6 shadow-md">
		<!-- TOP ROW: Session Info -->
		<div class="grid grid-cols-1 lg:grid-cols-3 items-center gap-4">
			<div class="flex items-center justify-start gap-4">
				<div class="w-8 h-6 rounded-sm shadow-sm border border-black/20 {flagColors[session.flag]}" title="Current Track Status: {session.flag}">
					{#if session.flag === 'SC' || session.flag === 'VSC'}
						<span class="text-[10px] tracking-tighter text-black font-black flex items-center justify-center h-full">{session.flag}</span>
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
				<div class="status-badge flex items-center gap-1.5 ml-2">
					{#if globalSocket.isConnected}
						<span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
						<span class="text-emerald-500">Live</span>
					{:else}
						<span class="w-2 h-2 rounded-full bg-red-500"></span>
						<span class="text-red-500">Offline</span>
					{/if}
				</div>
			</div>
		</div>

		<!-- BOTTOM ROW: Sleek Timing Carousel -->
		<div class="mt-3 pt-2 border-t border-zinc-800 flex items-center relative">

			<!-- Indicator showing what the time column represents -->
			<div class="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-zinc-900 pr-2">
				<span class="text-[9px] font-black uppercase tracking-widest text-zinc-500 transition-opacity duration-300">
					{showLeaderGap ? 'TO LEADER' : 'INTERVAL'}
				</span>
			</div>

			<!-- The scrolling carousel container -->
			<div
				bind:this={carouselRef}
				class="flex gap-2 overflow-x-auto pl-20 scrollbar-none snap-x snap-mandatory scroll-smooth w-full"
				style="scrollbar-width: none;"
			>
				{#each sortedCars as [idStr, carData]}
					{@const carId = Number(idStr)}
					<button
						class="flex-shrink-0 flex items-center gap-3 px-3 py-1.5 rounded bg-zinc-950 border transition-all duration-200 snap-start
						{globalSocket.selectedCarId === carId
							? 'border-emerald-500 text-white shadow-[0_0_8px_rgba(16,185,129,0.15)]'
							: 'border-zinc-800 text-zinc-400 hover:border-zinc-600 hover:text-zinc-200 hover:bg-zinc-900'}"
						onclick={() => globalSocket.selectedCarId = carId}
					>
						<span class="text-xs font-black {globalSocket.selectedCarId === carId ? 'text-emerald-400' : 'text-zinc-500'} w-6 text-left">
							P{carData.position || '-'}
						</span>
						<span class="w-px h-3 bg-zinc-700"></span>
						<span class="text-xs font-bold w-12 text-center text-zinc-300">
							CAR {carId.toString().padStart(2, '0')}
						</span>
						<span class="w-px h-3 bg-zinc-700"></span>
						<span class="text-xs font-mono font-bold w-14 text-right transition-all duration-300 {showLeaderGap ? 'text-zinc-300' : 'text-zinc-400'}">
							{showLeaderGap ? (carData.gapToLeader || 'N/A') : (carData.gapToAhead || 'N/A')}
						</span>
					</button>
				{/each}

				{#if sortedCars.length === 0}
					<div class="text-xs text-zinc-600 italic py-1 font-mono flex items-center gap-2">
						Waiting for grid data...
					</div>
				{/if}
			</div>

			<!-- Right fade out to indicate more cars -->
			<div class="absolute right-0 top-0 bottom-0 w-12 bg-gradient-to-l from-zinc-900 to-transparent pointer-events-none"></div>
		</div>
	</section>
{/if}