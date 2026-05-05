<script lang="ts">
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
</script>

{#if session.isActive}
    <section role="alert" aria-live="polite" class="bg-zinc-900 border-b border-zinc-800 px-4 py-3 sm:px-6 shadow-md">
        <!-- TOP ROW: Existing Session Info -->
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
                <div class="flex items-center gap-2" title={session.weather}>
                    <span class="text-lg" aria-hidden="true">{weatherIcons[session.weather]}</span>
                    <span class="text-zinc-300 hidden xl:inline">{session.weather}</span>
                </div>

                <div class="flex items-center gap-2">
                    <span class="text-zinc-500 uppercase text-[10px]">Track</span>
                    <span class="text-zinc-200 tabular-nums">{session.trackTemp}°C</span>
                </div>

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

        <!-- BOTTOM ROW: The Dynamic Fleet Carousel -->
        <div class="mt-4 border-t border-zinc-800/80 pt-3 flex gap-3 overflow-x-auto pb-2 scrollbar-thin">
            {#each Object.entries(globalSocket.cars) as [idStr, carData]}
                {@const carId = Number(idStr)}
                <button
                    class="flex flex-col items-start min-w-[130px] p-2.5 rounded-lg border transition-all duration-200 text-left cursor-pointer
                    {globalSocket.selectedCarId === carId
                        ? 'bg-zinc-800 border-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.15)]'
                        : 'bg-zinc-950 border-zinc-800 hover:border-zinc-600 hover:bg-zinc-900'}"
                    onclick={() => globalSocket.selectedCarId = carId}
                >
                    <div class="flex justify-between w-full items-center mb-1.5">
                        <span class="text-xs font-black text-white">CAR {carId.toString().padStart(2, '0')}</span>
                        <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_4px_#10b981]"></span>
                    </div>

                    <div class="grid grid-cols-2 gap-2 w-full text-[10px] font-mono">
                        <div>
                            <span class="text-zinc-500 block text-[8px] uppercase">Speed</span>
                            <span class="text-zinc-300">{carData.Speed || '0'}</span>
                        </div>
                        <div>
                            <span class="text-zinc-500 block text-[8px] uppercase">Temp</span>
                            <span class="text-zinc-300">{Math.round(carData.TempAndHumidity?.temp || 0)}°</span>
                        </div>
                    </div>
                </button>
            {/each}

            {#if Object.keys(globalSocket.cars).length === 0}
                <div class="text-xs text-zinc-600 italic py-2 font-mono flex items-center gap-2">
                    <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v2m0 12v2m8-8h-2M6 12H4m13.414-5.657l-1.414 1.414M7.414 17.657l-1.414 1.414m0-11.314l1.414 1.414m11.314 11.314l-1.414-1.414"></path></svg>
                    Waiting for OBU Telemetry...
                </div>
            {/if}
        </div>
    </section>
{/if}