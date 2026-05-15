<script lang="ts">
	import TireSet from '../../components/tires/TireSet.svelte';
	import Gauge from '../../components/gauges/analog-gauge.svelte';
	import Speedometer from '../../components/gauges/speedometer.svelte';
	import Tachometer from '../../components/gauges/tachometer.svelte';
	import GMeter from '../../components/g-meter.svelte';
	import TrackWidget from '../../components/trackmap/trackWidget.svelte';
	import { globalSocket } from '$lib/communcation/globalSocket.svelte';
	import RollPitchCard from '../../components/rollPitch/RollPitchCard.svelte';

	let displayMode: 'analog' | 'digital' = $state('digital');

	// 1. Reactively grab the telemetry for whichever car is currently selected
	let activeCar = $derived(globalSocket.cars[globalSocket.selectedCarId] || {});
</script>

<section aria-labelledby="live-telemetry-heading" class="space-y-8 max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">

    <header class="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 border-b border-zinc-800 pb-6">
        <div>
            <h1 id="live-telemetry-heading" class="text-3xl font-black text-white tracking-tight">Live Telemetry</h1>
            <p class="text-emerald-400 text-sm mt-1 font-mono flex items-center gap-2">
				<span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
				VEHICLE {globalSocket.selectedCarId.toString().padStart(2, '0')}
				<span class="text-zinc-500">- LIVE DATA FEED</span>
			</p>
        </div>

        <div class="flex bg-zinc-900 rounded-lg p-1 border border-zinc-800 shadow-inner">
            <button
                class="px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-md transition-all duration-200 {displayMode === 'digital' ? 'bg-zinc-700 text-white shadow' : 'text-zinc-500 hover:text-zinc-300'}"
                onclick={() => displayMode = 'digital'}
            >
                Digital
            </button>
            <button
                class="px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-md transition-all duration-200 {displayMode === 'analog' ? 'bg-zinc-700 text-white shadow' : 'text-zinc-500 hover:text-zinc-300'}"
                onclick={() => displayMode = 'analog'}
            >
                Analog
            </button>
        </div>
    </header>

    <div class="animate-in fade-in duration-500">
        {#if displayMode === 'digital'}
            <h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-3">Digital Cluster</h2>
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <div class="col-span-1">
					<Speedometer value={Math.round(activeCar.Speed || 0)} unit="km/h"/>
                </div>

                <div class="col-span-1 lg:col-span-2">
					<Tachometer
                        value={activeCar.RPM || 0}
                        max={7500}
                        segments={25}
						stepSize={500}
                        demo={false}
                        ranges={[
                            { min: 0, max: 5999, colorClass: 'bg-white' },
                            { min: 6000, max: 6999, colorClass: 'bg-orange-500' },
                            { min: 7000, max: 7500, colorClass: 'bg-red-500' }
                        ]}
                    />
                </div>
            </div>
        {:else}
            <h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-3">Analog Instruments</h2>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
				<Gauge value={Math.round(activeCar.Speed || 0)} max={300} stepSize={20} intermediateTicks={1} unit="km/h" demo={false} />

				<Gauge
                    value={(activeCar.RPM || 0) / 1000} max={7.5} precision={1} stepSize={1} intermediateTicks={4} unit="rpm{'\n'}x1000" demo={false}
                    ranges={[
                        { min: 0, max: 5.99, colorClass: 'text-white' },
                        { min: 6, max: 6.99, colorClass: 'text-orange-500' },
                        { min: 7, max: 7.5, colorClass: 'text-red-500' }
                    ]}
                />

                <Gauge
                    value={activeCar.PressureAndAltitude?.pressure || 0} max={8} stepSize={2} intermediateTicks={3} precision={1} unit="bar" demo={false}
                    ranges={[
                        { min: 0, max: 2.9, colorClass: 'text-red-500' },
                        { min: 3, max: 8, colorClass: 'text-emerald-400' }
                    ]}
                />

                <Gauge
                    value={activeCar.TempAndHumidity?.temp || 0} max={120} stepSize={20} intermediateTicks={1} unit="°C" demo={false}
                    ranges={[
                        { min: 0, max: 100, colorClass: 'text-emerald-400' },
                        { min: 101, max: 120, colorClass: 'text-red-500' }
                    ]}
                />
            </div>
        {/if}
    </div>

    <div>
        <h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-3">Dynamics & Position</h2>
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">

            <div class="col-span-1">
                <GMeter
                    maxG={3}
                    x={activeCar.Accelerometer?.acceleration?.[0] || 0}
                    y={activeCar.Accelerometer?.acceleration?.[1] || 0}
                />
            </div>

            <div class="col-span-1 lg:col-span-2">
                <TrackWidget demo={true} />
            </div>
            <div class="col-span-1">
                <RollPitchCard roll={activeCar.Accelerometer?.roll || 0} pitch={activeCar.Accelerometer?.pitch || 0}></RollPitchCard>
            </div>
        </div>
    </div>

    <div>
        <h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-3">Tyre Status</h2>
        <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-4 shadow-lg">
            <TireSet
                layerCount={2}
                surfaceTemp={activeCar.TempAndHumidity?.temp || { FL: 0, FR: 0, RL: 0, RR: 0 }}
                pressure={activeCar.PressureAndAltitude?.pressure || { FL: 0, FR: 0, RL: 0, RR: 0 }}
                speed={activeCar.Speed || { FL: 0, FR: 0, RL: 0, RR: 0 }}
            />
        </div>
    </div>

    <div>
        <h2 class="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-3">Live Track Vision</h2>

        <div class="bg-zinc-950 border border-zinc-800 rounded-xl shadow-lg flex justify-center items-center aspect-video relative overflow-hidden group">

            {#if globalSocket.latestVideoFrame}
                <img
                    src="data:image/jpeg;base64,{globalSocket.latestVideoFrame}"
                    alt="Live AI Vision"
                    class="w-full h-full object-cover opacity-90 transition-opacity"
                />
            {:else}
                <div class="flex flex-col items-center justify-center text-zinc-600 animate-pulse">
                    <svg class="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
                    <span class="text-sm font-mono uppercase tracking-widest">Awaiting Video Stream...</span>
                </div>
            {/if}

            {#if globalSocket.latestVideoFrame}
                <div class="absolute inset-0 pointer-events-none p-4 sm:p-6 flex flex-col justify-between">

                    <div class="flex justify-between items-start">
                        {#if globalSocket.aiVisionState === 'SCANNING'}
                            <div class="flex items-center gap-2 bg-zinc-900/80 border border-zinc-700 px-3 py-1.5 rounded backdrop-blur-md transition-all duration-300">
                                <span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                                <span class="text-[10px] sm:text-xs font-mono font-bold text-cyan-400 tracking-widest">AI: SEEKING TARGET</span>
                            </div>
                        {:else if globalSocket.aiVisionState === 'CLEAR'}
                            <div class="flex items-center gap-2 bg-emerald-950/80 border border-emerald-500/50 px-3 py-1.5 rounded backdrop-blur-md transition-all duration-300">
                                <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                                <span class="text-[10px] sm:text-xs font-mono font-bold text-emerald-400 tracking-widest">TARGET ACQUIRED: TRACK LIMITS OK</span>
                            </div>
                        {:else if globalSocket.aiVisionState === 'VIOLATION'}
                            <div class="flex items-center gap-2 bg-red-950/90 border border-red-500 px-3 py-1.5 rounded backdrop-blur-md animate-pulse transition-all duration-300">
                                <svg class="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                                <span class="text-[10px] sm:text-xs font-mono font-bold text-red-500 tracking-widest">VIOLATION DETECTED</span>
                            </div>
                        {/if}

                        <div class="flex items-center gap-2 bg-black/50 px-2 py-1 rounded backdrop-blur-sm">
                            <span class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                            <span class="text-[10px] font-bold text-white tracking-widest">REC</span>
                        </div>
                    </div>

                    <div class="flex justify-between items-end opacity-70">
                        <div class="font-mono text-[10px] text-zinc-400">
                            COORD: {activeCar.Accelerometer?.acceleration?.[0]?.toFixed(2) || '0.00'}, {activeCar.Accelerometer?.acceleration?.[1]?.toFixed(2) || '0.00'}<br>
                            SYS: OBU_ACTIVE
                        </div>
                        <div class="font-mono text-[10px] text-zinc-400 text-right">
                            v1.0.4 EDGE_TPU<br>
                            640x480@10FPS
                        </div>
                    </div>

                    {@const reticleColor = globalSocket.aiVisionState === 'VIOLATION' ? 'border-red-500' : globalSocket.aiVisionState === 'CLEAR' ? 'border-emerald-500' : 'border-cyan-500/50'}

                    <div class="absolute top-4 left-4 w-6 sm:w-10 h-6 sm:h-10 border-t-2 border-l-2 transition-colors duration-300 {reticleColor}"></div>
                    <div class="absolute top-4 right-4 w-6 sm:w-10 h-6 sm:h-10 border-t-2 border-r-2 transition-colors duration-300 {reticleColor}"></div>
                    <div class="absolute bottom-4 left-4 w-6 sm:w-10 h-6 sm:h-10 border-b-2 border-l-2 transition-colors duration-300 {reticleColor}"></div>
                    <div class="absolute bottom-4 right-4 w-6 sm:w-10 h-6 sm:h-10 border-b-2 border-r-2 transition-colors duration-300 {reticleColor}"></div>

                </div>

                {#if globalSocket.aiVisionState === 'VIOLATION'}
                    <div class="absolute inset-0 bg-red-500/10 pointer-events-none animate-pulse"></div>
                {/if}
            {/if}
        </div>
    </div>

</section>