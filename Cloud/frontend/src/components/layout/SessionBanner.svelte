<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { globalSocket } from '$lib/communcation/globalSocket.svelte';

    type SessionMode =
       | { type: 'Practice'; timeRemaining: string }
       | { type: 'Qualifying'; timeRemaining: string }
       | { type: 'Race'; format: 'time'; timeRemaining: string }
       | { type: 'Race'; format: 'laps'; currentLap: number; totalLaps: number };

    type WeatherType = 'Sunny' | 'Cloudy' | 'Light Rain' | 'Heavy Rain' | 'Dry';

    interface session {
       isActive: boolean;
       location: string;
       mode: SessionMode;
       trackTemp: number;
       weather: WeatherType;
    }

    let session: session = $state({
       isActive: true,
       location: 'Spa-Francorchamps',
       mode: { type: 'Race', format: 'laps', currentLap: 12, totalLaps: 44 },
       trackTemp: 22.5,
       weather: 'Light Rain'
    });

    const weatherIcons: Record<WeatherType, string> = {
       'Sunny': '☀️', 'Cloudy': '☁️', 'Light Rain': '🌦️', 'Heavy Rain': '🌧️', 'Dry': '🌤️'
    };

    // --- Global Socket Reactive State ---
    let currentFlag = $derived(globalSocket.trackFlag);
    let isConnected = $derived(globalSocket.isConnected);

    // --- Carousel Logic ---
    let showLeaderGap = $state(false);
    let carouselRef: HTMLDivElement;
    let scrollTimer: ReturnType<typeof setInterval>;

    onMount(() => {
       scrollTimer = setInterval(() => {
          if (carouselRef && !carouselRef.matches(':hover')) {
             carouselRef.scrollBy({ left: 160, behavior: 'smooth' });
             if (carouselRef.scrollLeft + carouselRef.clientWidth >= carouselRef.scrollWidth - 10) {
                carouselRef.scrollTo({ left: 0, behavior: 'smooth' });
                showLeaderGap = !showLeaderGap;
             }
          }
       }, 3000);
    });

    onDestroy(() => {
       clearInterval(scrollTimer);
    });

    let sortedCars = $derived(
       Object.entries(globalSocket.cars).sort((a, b) => (a[1].position || 99) - (b[1].position || 99))
    );
</script>

{#if session.isActive}
    <section role="alert" aria-live="polite" class="bg-zinc-900 border-b border-zinc-800 px-4 py-2 sm:px-6 shadow-md sticky top-0 z-30">

       <div class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">

          <div class="flex items-center gap-4">
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

             <span class="hidden lg:flex text-sm font-black text-emerald-400 tracking-widest uppercase items-center gap-2 ml-4">
                <svg class="w-4 h-4 text-emerald-500/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.243-4.243a8 8 0 1111.314 0z" />
                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                {session.location}
             </span>
          </div>

          <div class="flex items-center gap-4 w-full lg:w-auto overflow-x-auto pb-1 lg:pb-0 scrollbar-none">

             <div class="flex items-center shrink-0 gap-1.5 bg-zinc-950 border border-zinc-800 rounded-lg p-1 shadow-inner">
                <span class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mr-2 ml-2 hidden sm:inline">Track Status:</span>

                <button
                   onclick={() => globalSocket.setTrackFlag('Green')}
                   class="group flex items-center gap-1.5 px-3 py-1.5 rounded transition-all duration-300 border {currentFlag === 'Green' ? 'bg-emerald-500/20 border-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.2)]' : 'bg-transparent border-transparent hover:bg-zinc-900'}"
                >
                   <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
                      stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                      class="transition-colors duration-300 {currentFlag === 'Green' ? 'text-emerald-500 fill-emerald-500' : 'text-zinc-600 fill-transparent group-hover:text-zinc-400'}">
                      <path d="M4 22V4a1 1 0 0 1 .4-.8A6 6 0 0 1 8 2c3 0 5 2 7.333 2q2 0 3.067-.8A1 1 0 0 1 20 4v10a1 1 0 0 1-.4.8A6 6 0 0 1 16 16c-3 0-5-2-8-2a6 6 0 0 0-4 1.528"/>
                   </svg>
                   <span class="text-[10px] font-black uppercase tracking-wider {currentFlag === 'Green' ? 'text-emerald-400' : 'text-zinc-600 group-hover:text-zinc-400'}">Green</span>
                </button>

                <button
                   onclick={() => globalSocket.setTrackFlag('Yellow')}
                   class="group flex items-center gap-1.5 px-3 py-1.5 rounded transition-all duration-300 border {currentFlag === 'Yellow' ? 'bg-yellow-500/20 border-yellow-500/50 shadow-[0_0_15px_rgba(234,179,8,0.2)]' : 'bg-transparent border-transparent hover:bg-zinc-900'}"
                >
                   <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
                      stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                      class="transition-colors duration-300 {currentFlag === 'Yellow' ? 'text-yellow-500 fill-yellow-500' : 'text-zinc-600 fill-transparent group-hover:text-zinc-400'}">
                      <path d="M4 22V4a1 1 0 0 1 .4-.8A6 6 0 0 1 8 2c3 0 5 2 7.333 2q2 0 3.067-.8A1 1 0 0 1 20 4v10a1 1 0 0 1-.4.8A6 6 0 0 1 16 16c-3 0-5-2-8-2a6 6 0 0 0-4 1.528"/>
                   </svg>
                   <span class="text-[10px] font-black uppercase tracking-wider {currentFlag === 'Yellow' ? 'text-yellow-400' : 'text-zinc-600 group-hover:text-zinc-400'}">Yellow</span>
                </button>

                <button
                   onclick={() => globalSocket.setTrackFlag('Red')}
                   class="group flex items-center gap-1.5 px-3 py-1.5 rounded transition-all duration-300 border {currentFlag === 'Red' ? 'bg-red-500/20 border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.2)]' : 'bg-transparent border-transparent hover:bg-zinc-900'}"
                >
                   <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
                      stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                      class="transition-colors duration-300 {currentFlag === 'Red' ? 'text-red-500 fill-red-500' : 'text-zinc-600 fill-transparent group-hover:text-zinc-400'}">
                      <path d="M4 22V4a1 1 0 0 1 .4-.8A6 6 0 0 1 8 2c3 0 5 2 7.333 2q2 0 3.067-.8A1 1 0 0 1 20 4v10a1 1 0 0 1-.4.8A6 6 0 0 1 16 16c-3 0-5-2-8-2a6 6 0 0 0-4 1.528"/>
                   </svg>
                   <span class="text-[10px] font-black uppercase tracking-wider {currentFlag === 'Red' ? 'text-red-400' : 'text-zinc-600 group-hover:text-zinc-400'}">Red</span>
                </button>
             </div>

             <div class="hidden sm:flex items-center gap-2 pl-4 border-l border-zinc-800 text-xs font-mono shrink-0">
                {#if isConnected}
                   <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                   <span class="text-emerald-500">Uplink Live</span>
                {:else}
                   <span class="w-2 h-2 rounded-full bg-red-500"></span>
                   <span class="text-red-500">Offline</span>
                {/if}
             </div>
          </div>
       </div>

       <div class="mt-3 pt-2 border-t border-zinc-800 flex items-center gap-3">

          <div class="w-20 shrink-0 border-r border-zinc-800/50 pr-3 flex items-center">
             <span class="text-[9px] font-black uppercase tracking-widest text-zinc-500 transition-opacity duration-300">
                {showLeaderGap ? 'TO LEADER' : 'INTERVAL'}
             </span>
          </div>

          <div class="relative flex-1 min-w-0 overflow-hidden">
             <div class="absolute left-0 top-0 bottom-0 w-6 bg-gradient-to-r from-zinc-900 to-transparent z-10 pointer-events-none"></div>

             <div
                bind:this={carouselRef}
                class="flex gap-2 overflow-x-auto scrollbar-none snap-x snap-mandatory scroll-smooth w-full px-2"
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

             <div class="absolute right-0 top-0 bottom-0 w-12 bg-gradient-to-l from-zinc-900 to-transparent z-10 pointer-events-none"></div>
          </div>
       </div>
    </section>
{/if}